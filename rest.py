#!/usr/bin/env python
# coding=utf-8

import os, sys, re, json, traceback
from Queue import Queue, Empty
from threading import Lock, Thread, Condition
from multiprocess import Processor
from preprocess import preprocess
from postprocess import postprocess

def AMR2dict_factory():

    from common.util import StrLiteral, SpecialValue, Quantity, Polarity, Interrogative, Literal

    typestr = {}
    typestr[unicode] = 'relation'
    typestr[str] = 'relation'
    typestr[StrLiteral] = 'str'
    typestr[SpecialValue] = 'special'
    typestr[Quantity] = 'quantity'
    typestr[Polarity] = 'polarity'
    typestr[Interrogative] = 'interrogative'
    typestr[Literal] = 'literal'
    tokenvar = re.compile(r'x\d+')

    def AMR2dict(amr, mergeFrom):
        try:
            instances = []
            var2index = {}
            for var, concept in amr.node_to_concepts.items():
                index = len(instances)
                var2index[var] = index
                instances.append(dict(index=index, concept=concept, tokenIndex=int(var.lstrip('x')) if tokenvar.match(var) else None))

            root = var2index[amr.roots[0]]

            relations = []
            for source,edges in amr.items():
                if type(source) is not unicode and type(source) is not str:
                    # print 'Skip source:', source, type(source)
                    continue
                # print source, ':'
                source = var2index.get(source)
                if source is None:
                    continue
                for edge,targets in edges.items():
                    # print '   ', edge, '==', targets
                    for target in targets:
                        # print '       ', type(target), target
                        tstr = typestr.get(type(target), 'unknown')
                        if type(target) is unicode or type(target) is str:
                            target = var2index.get(target, 'unknown')
                            if edge.endswith('-of'):
                                edge = edge.rsplit('-',1)[0]
                                source,target = target,source   # swap
                        elif type(target) is StrLiteral:
                            target = target[:]
                        elif type(target) is Quantity:
                            target = str(target)
                        elif type(target) is Polarity:
                            target = str(target)
                        else:
                            # print 'Unknown target type:', type(target)
                            # sys.exit(1)
                            continue
                        relations.append(dict(source=source, target=target, edge=edge, type=tstr))
                    # if len(targets) > 1:
                    #     print 'more than on target !!!'
                    #     quit()
        except Exception as e:
            # print 'Problems with AMR:'
            raise

        result = dict(mergeFrom)
        result['instances'] = instances
        result['root'] = root
        result['relations'] = relations
        result['AMRtext'] = amr.to_amr_string()
        return result
        # return dict(instances=instances, root=root, relations=relations, AMRtext=amr.to_amr_string(), tokens=tokens)

    return AMR2dict


class ProcessorProxy(Thread):

    def __init__(self, processor_factory):
        Thread.__init__(self)

        self.make_processor = processor_factory

        self.stop = False
        self.input = Queue()

        self.next_id = 0
        self.id_lock = Lock()

        self.results = {}
        # self.results_lock = Lock()
        self.result_available = Condition()
        
        self.start()

    def put(self, id, result):
        # with self.results_lock:
        #     self.results[id] = result
        self.result_available.acquire()
        try:
            self.results[id] = result
            self.result_available.notify_all()
        finally:
            self.result_available.release()

    def get(self, id, timeout=None):
        self.result_available.acquire()
        try:
            # with self.results_lock:
            #     if id in self.results:
            #         return self.results.pop(id, None)
            if id in self.results:
                return self.results.pop(id, None)
            while True:
                self.result_available.wait(timeout) # waiting happens here
                # with self.results_lock:
                #     result = self.results.pop(id, None)
                result = self.results.pop(id, None)
                if timeout is not None or result is not None:
                    return result
        finally:
            self.result_available.release()

    def run(self):
        processor = self.make_processor()
        try:
            while not self.stop:
                id = None
                try:
                    id,data = self.input.get(True, 0.5)   # timeout each second to check for possible stop signal
                    if self.stop:
                        break
                    result = processor(data)
                    self.put(id, result)
                except Empty:
                    pass
                except KeyboardInterrupt:
                    self.stop = True
                    break
                except:
                    traceback.print_exc()
                    if id is not None:
                        self.put(id, None)  # something must be replied to each input
        finally:
            processor.stop()    # stop processor
            # notify any listening process
            self.result_available.acquire()
            try:
                self.result_available.notify_all()
            finally:
                self.result_available.release()

    def newid(self):
        with self.id_lock:
            id = self.next_id
            self.next_id += 1
            return id

    def __call__(self, data):
        id = self.newid()
        self.input.put((id,data))
        return self.get(id)


class NLP(ProcessorProxy):
    def __init__(self, threads=4, props='default.properties', debug=False, name='CoreNLP:'):
        from stanfordnlp.pipe import make_nlp
        ProcessorProxy.__init__(self, lambda: make_nlp(threads, props, verbose=debug, name=name))
        # will buffer at pipe level

class DepParser(ProcessorProxy):
    def __init__(self, processes=4, debug=False):

        def processor_factory():

            from lib.pipe import CoreNLPDepConv
            from bllipparser.ModelFetcher import download_and_install_model
            from bllipparser import RerankingParser
            model_type = 'WSJ+Gigaword'
            path_to_model = download_and_install_model(model_type,'./bllip-parser/models')
            print "Loading BLLIP parser model: %s ..." % (model_type)
            parser = RerankingParser.from_unified_model_dir(path_to_model)
            print "BLLIP parser model %s loaded" % (model_type)

            def factory():
                conv = CoreNLPDepConv(verbose=debug)
                def parse(line):
                    result = "(())"  # dummy output if wasn't able to parse
                    try:
                        line = line.strip()
                        if line:
                            result = parser.simple_parse(line.split())
                            result = conv(result)
                    # except KeyboardInterrupt:
                    #     raise
                    except Exception as e:
                        print >> sys.stderr, "Dependency parser (BLLIP / Charniak-Johnson parser) ERROR:"
                        traceback.print_exc(file=sys.stderr)
                        pass
                        # print >> sys.stderr, 'WARNING: unable to parse sentence:'
                        # print >> sys.stderr, ll.strip()
                    return result
                parse.stop = lambda: conv.stop()
                return parse

            return Processor(factory, processes)

        ProcessorProxy.__init__(self, processor_factory)

class AMRParser(ProcessorProxy):
    def __init__(self, model, processes=4, debug=False):

        from model import Model
        from parser import Parser
        from constants import DET_T2G_ORACLE_ABT
        from graphstate import GraphState

        parser = Parser(model=Model.load_model(model),oracle_type=DET_T2G_ORACLE_ABT,action_type='basic',verbose=False,elog=sys.stdout)

        print 'AMR parser model loaded, parser ready'

        def processor_factory():

            def factory():
                return lambda instance: GraphState.get_parsed_amr(parser.parse(instance,train=False)[1].A)

            return Processor(factory, processes)

        ProcessorProxy.__init__(self, processor_factory)


class Parser:

    from multiprocessing import cpu_count
    def_threads = cpu_count()//2            # give each module half of available threads - let them overlap

    def __init__(self, model, debug=False, ssplit=True, no_ssplit=True, nlp_threads=None, dep_threads=None, amr_threads=None):
        if not ssplit and not no_ssplit:
            # defaults to at least one NLP module - no splitting
            no_ssplit = True
        try:
            self.nlp = NLP(nlp_threads or self.def_threads, debug=debug) if no_ssplit else None
            self.nlp_ssplit = NLP(nlp_threads or self.def_threads,
                    'default_ssplit.properties', debug=debug, name='CoreNLP(ssplit):') if ssplit else None
            self.depparser = DepParser(dep_threads or self.def_threads, debug=debug)
            self.parser = AMRParser(model, amr_threads or self.def_threads, debug=debug)
        except KeyboardInterrupt:
            self.stop()
        self.amr2dict = AMR2dict_factory()
        self.debug = debug

    def stop(self):
        if self.nlp:
            self.nlp.stop = True
        if self.nlp_ssplit:
            self.nlp_ssplit.stop = True
        self.depparser.stop = True
        self.parser.stop = True

    def __call__(self, text, ssplit=False):

        try:

            from stanfordnlp.data import Data
            Data.current_sen = 1

            if debug:
                print >> sys.stderr, 'Input Text:', text
            text = preprocess(text)
            if debug:
                print >> sys.stderr, 'Preprocessed (wrapper) Text:', text
                print >> sys.stderr, 'Sentence split lines:', ssplit

            if ssplit and self.nlp_ssplit or (not self.nlp and self.nlp_ssplit):
                sentences = self.nlp_ssplit(text)
            else:
                sentences = self.nlp(text)

            if debug:
                print >> sys.stderr, 'CoreNLP result sentences:', sentences

            instances = []
            for sentence in sentences:
                data = Data()
                data.addText(sentence['text'])
                # data.addText(' '.join(token['text'] for token in sentence['tokens']))
                data.sentID = len(instances)+1
                index = 1
                for token in sentence['tokens']:
                    token['index'] = index
                    index += 1
                    data.addToken(token['text'], None, None, token['lemma'], token['pos'], token.get('ne', 'O'))
                instances.append(data)

            if debug:
                print >> sys.stderr, 'Dependency parser input sentences:', [u' '.join(instance.get_tokenized_sent()) for instance in instances]

            deptrees = self.depparser([u' '.join(instance.get_tokenized_sent()) for instance in instances])

            if debug:
                print >> sys.stderr, 'Dependency parser output trees:', deptrees

            # add dependency trees to instances
            splitre = re.compile(r'\(|, ')
            for i,deptree in enumerate(deptrees):
                for line in deptree:
                    split_entry = splitre.split(line[:-1])
                    if len(split_entry) == 3:
                        rel, l_lemma, r_lemma = split_entry
                        l_lemma, l_index = l_lemma.rsplit('-', 1)
                        r_lemma, r_index = r_lemma.rsplit('-', 1)
                        parts = r_lemma.rsplit('^', 1)
                        if len(parts) < 2 or not parts[1]:
                            r_trace = None
                        else:
                            r_lemma, r_trace = parts

                        if r_index != 'null':
                            instances[i].addDependency( rel, l_index, r_index )
                        if r_trace is not None:
                            instances[i].addTrace( rel, l_index, r_trace )

            results = self.parser(instances)

            if debug:
                print >> sys.stderr, 'AMR parser results:', results

            amr2dict = self.amr2dict
            results = [amr2dict(postprocess(amr),sentence) for sentence,amr in zip(sentences,results)]

            if debug:
                print >> sys.stderr, 'AMR parser converted results:', results

            return results

        except KeyboardInterrupt:
            self.stop()



def start_REST(model, port=5000, debug=False, ssplit=True, no_ssplit=True,
        amr_threads=Parser.def_threads, nlp_threads=Parser.def_threads, dep_threads=Parser.def_threads):

    import signal, time, thread

    main_thread_id = thread.get_ident()
    parser = None

    def interrupt_handler(signum, frame):
        # only for main thread
        if main_thread_id == thread.get_ident():
            print 'Interrupted, will terminate in few seconds...'
            if parser is not None:
                parser.stop()
            time.sleep(3)   # give everything some seconds to stop
            sys.exit(1)

    signal.signal(signal.SIGINT, interrupt_handler)

    parser = Parser(model, debug=debug, ssplit=ssplit, no_ssplit=no_ssplit, amr_threads=amr_threads, nlp_threads=nlp_threads, dep_threads=dep_threads)

    # from: http://flask.pocoo.org/snippets/56/
    # from datetime import timedelta
    # from flask import make_response, request, current_app
    # from functools import update_wrapper
    #
    # def crossdomain(origin=None, methods=None, headers=None,
    #                 max_age=21600, attach_to_all=True,
    #                 automatic_options=True):
    #     if methods is not None:
    #         methods = ', '.join(sorted(x.upper() for x in methods))
    #     if headers is not None and not isinstance(headers, basestring):
    #         headers = ', '.join(x.upper() for x in headers)
    #     if not isinstance(origin, basestring):
    #         origin = ', '.join(origin)
    #     if isinstance(max_age, timedelta):
    #         max_age = max_age.total_seconds()
    #
    #     def get_methods():
    #         if methods is not None:
    #             return methods
    #
    #         options_resp = current_app.make_default_options_response()
    #         return options_resp.headers['allow']
    #
    #     def decorator(f):
    #         def wrapped_function(*args, **kwargs):
    #             if automatic_options and request.method == 'OPTIONS':
    #                 resp = current_app.make_default_options_response()
    #             else:
    #                 resp = make_response(f(*args, **kwargs))
    #             if not attach_to_all and request.method != 'OPTIONS':
    #                 return resp
    #
    #             h = resp.headers
    #
    #             h['Access-Control-Allow-Origin'] = origin
    #             h['Access-Control-Allow-Methods'] = get_methods()
    #             h['Access-Control-Max-Age'] = str(max_age)
    #             if headers is not None:
    #                 h['Access-Control-Allow-Headers'] = headers
    #             return resp
    #
    #         f.provide_automatic_options = False
    #         return update_wrapper(wrapped_function, f)
    #     return decorator

    import yaml

    class amr_str(str): pass

    yaml.add_representer(amr_str, lambda dumper,data: dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|'))

    from flask import Flask, request, Response, jsonify
    from flask.ext.cors import cross_origin

    app = Flask(__name__)

    @app.route('/api/parse', methods=['POST', 'PUT'])
    # @crossdomain(origin='*')
    @cross_origin()
    def api_parse():
        try:
            ssplit = request.args.get('ssplit', False)
            if type(ssplit) is str:
                try:
                    ssplit = bool(int(ssplit))
                except ValueError:
                    ssplit = ssplit.lower() in ('t', 'true', 'y', 'yes')

            fmt = request.args.get('fmt', 'json')
            if fmt.lower() not in ('json', 'yaml', 'yml'):
                return Response(response='invalid output format: '+fmt, status=400, mimetype='text/plain')

            content_type = request.headers.get('Content-Type')
            if content_type == 'text/plain':
                data = request.data
                if type(data) is str:
                    # data = data.decode('utf-8')
                    data = data.decode('utf-8', errors='ignore')
                    data = data.encode('utf-8')
            elif content_type == 'application/json':
                data = [item if type(item) is unicode else item.get('text', '__no_text_error__') for item in request.get_json()]
            else:
                return Response(response='invalid content-type header value', status=400, mimetype='text/plain')

            accept = tuple(x.strip() for x in request.headers.get('Accept', '*/*').split(','))

            if not ('*/*' in accept or 'application/json' in accept or 'application/json' in accept):
                return Response(response='invalid accept header value', status=400, mimetype='text/plain')

            if fmt.lower() == 'json' and ('*/*' in accept or 'application/json' in accept):
                result = parser(data, ssplit)
                return Response(response=json.dumps(result), status=200, mimetype='application/json')
            elif fmt.lower() == 'yaml' and ('*/*' in accept or 'application/yaml' in accept):
                result = parser(data, ssplit)
                for item in result:
                    item['AMRtext'] = amr_str(item['AMRtext'].replace('\t', '    '))
                return Response(yaml.dump(result), status=200, mimetype='application/yaml')

            return Response(response='required output format inconsistent with accept header', status=400, mimetype='text/plain')
            # return Response(response=json.dumps(result), status=200, mimetype='application/json')
            # return jsonify(result)
        except KeyboardInterrupt:
            shutdown = request.environ.get('werkzeug.server.shutdown')
            if shutdown is None:
                print 'Interrupted, but not running with Werkzeug Server'
                raise   # let flask handle this
            else:
                shutdown()
        except:
            traceback.print_exc()
            return Response(response=traceback.format_exc(), status=500, mimetype='text/html')

    @app.route('/')
    def root():
        # return app.send_static_file('static/index.html')
        return app.send_static_file('index.html')

    app.run(host='0.0.0.0', port=port, static_files={'/': os.path.join(os.path.dirname(__file__), 'static')}, threaded=True)




if __name__ == "__main__":

    # if len(sys.argv) > 1:
    #     try:
    #         port = int(sys.argv[1])
    #     except ValueError:
    #         port = 5000
    # else:
    #     port = 5000

    # debug = '--debug' in sys.argv[1:]

    import argparse

    port = 5000
    model = 'model.m.bz2'

    arg_parser = argparse.ArgumentParser(description="CAMR REST API with Demo UI", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    arg_parser.add_argument('-p', '--port', type=int, default=port, help='change port')
    arg_parser.add_argument('-m', '--model', type=str, default=model, help='specify model filename')
    arg_parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode')
    arg_parser.add_argument('-s', '--ssplit', type=int, default=0, help='sentence split modes enabled: 0 - all enabled, -1 - only no ssplit, 1 - only ssplit')
    arg_parser.add_argument('-t', '--threads', type=int, default=Parser.def_threads, help='default number of threads for each module (NLP, BLLIP, AMR), number of system cores: '+str(Parser.__dict__['cpu_count']()))
    arg_parser.add_argument('--nlp-threads', type=int, default=0, help='number of threads for NLP')
    arg_parser.add_argument('--dep-threads', type=int, default=0, help='number of threads for BLLIP')
    arg_parser.add_argument('--amr-threads', type=int, default=0, help='number of threads for AMR')

    args = arg_parser.parse_args()

    ssplit = args.ssplit >= 0
    no_ssplit = args.ssplit <= 0
    port = args.port
    debug = args.debug
    model = args.model
    Parser.def_threads = args.threads

    if not os.path.isfile(model):
        print >> sys.stderr, 'Error, model file does not exist:', model
        sys.exit(1)

    start_REST(model, port=port, debug=debug, ssplit=ssplit, no_ssplit=no_ssplit,
            amr_threads=args.amr_threads, nlp_threads=args.nlp_threads, dep_threads=args.dep_threads)

    # some tests below

    quit()

    texts = [
        "We’ve all seen the films.",
        "A man is caught in quicksand, begging onlookers for help, but the more he struggles, the further down into the sand he is sucked until eventually he disappears.",
        "All that’s left is sinister sand, and maybe his hat.",
        "There are so many films featuring death by quicksand that Slate journalist Daniel Engbar has even tracked the peak quicksand years in film.",
        "In the 1960s, one in 35 films featured quicksands.",
        "They were in everything from Lawrence of Arabia to The Monkees."
    ]

    if True:
        parser = Parser(model)
        x = parser('\n'.join(texts))
        print(x)
        parser.stop()

    quit()

    if True:
        nlp = NLP()

        result = nlp(texts[0])
        print(result)

        result = nlp(texts[1])
        print(result)

        nlp.stop = True
        nlp.join()

    if True:
        depparser = DepParser()
        print('feed input')
        result = depparser(texts[:3])
        print(result)
        print('feed input 2')
        result = depparser(texts[3:])
        print(result)
        depparser.stop = True
        depparser.join()

