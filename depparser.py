#!/usr/bin/env python
import os,subprocess

VERBOSE = True

class DepParser(object):
    
    def __init__(self):
        pass

    def parse(self,sent_filename):
        '''the input should be tokenized sentences (tokenized by stanford CoreNLP) '''
        raise NotImplemented("Must implement setup method!")


import sys, traceback
from multiprocessing import Queue, Process, Lock, JoinableQueue, cpu_count
from multiprocessing.sharedctypes import Value
from Queue import Empty, Full
from progress import Progress


# parse process body
def parse_queue(parser, queue, results, count, sync_after=0, p=None, i=-1):

    local_count = 0
    try:
        while True:
            item = queue.get(True, 2)
            r = "(())"  # dummy output if wasn't able to parse
            try:
                ll = item[1].strip()
                if ll:
                    r = parser.simple_parse(ll.split())     # call parser
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print >> sys.stderr, 'WARNING: unable to parse sentence:'
                print >> sys.stderr, ll.strip()

            results.put((item[0], r))

            local_count += 1
            queue.task_done()

            if local_count >= sync_after:
                count.value += local_count
                local_count = 0
                if p is not None:
                    p.set(count.value)

    except KeyboardInterrupt:
        # print >> sys.stderr, 'Job interrupted'
        os.abort() # abort instead of exit so that multiprocessing won't wait
        return
    except Empty:
        pass

    if local_count > 0:
        count.value += local_count

    if p is not None:
        p.set(count.value)


class CharniakParser(DepParser):

    parser = None

    def __init__(self):
        if CharniakParser.parser is None:
            from bllipparser.ModelFetcher import download_and_install_model
            from bllipparser import RerankingParser
            model_type = 'WSJ+Gigaword'
            path_to_model = download_and_install_model(model_type,'./bllip-parser/models')
            print "Loading Charniak parser model: %s ..." % (model_type)
            CharniakParser.parser = RerankingParser.from_unified_model_dir(path_to_model)
    
    def parse(self,sent_filename):
        """
        use Charniak parser to parse sentences then convert results to Stanford Dependency
        """
        rrp = CharniakParser.parser
        print "Begin Charniak parsing ..."
        parsed_filename = sent_filename+'.charniak.parse'
        parsed_trees = ''

        # will use multiprocessing to parallelize parsing

        queue = JoinableQueue()
        results = Queue()

        print 'Reading', sent_filename, '...'
        data = []
        with open(sent_filename,'rb') as f:
            for line in f:
                l = line.decode('utf8', errors='ignore')
                # queue.put((len(data), l))
                data.append(l)

        feed = enumerate(data)
        fed_count = 0
        # feed first 100 items
        for item in feed:
            queue.put(item)
            data[item[0]] = ''
            fed_count += 1
            if item[0] >= 1024:
                break

        p = Progress(len(data), estimate=True, values=True) # output progress bar

        # define jobs
        count = Value('i', 0)
        num_threads = cpu_count()
        sync_count = len(data)/1000/num_threads

        print 'Starting %i jobs ...' % num_threads

        jobs = [Process(target=parse_queue, args=(rrp, queue, results, count, sync_count, p if i == -1 else None, i)) for i in range(num_threads)]

        try:
            # start jobs
            for job in jobs:
                job.start()

            total_count = 0

            # feed rest items
            while fed_count < len(data):
                for item in feed:
                    while True:
                        try:
                            queue.put(item, True, 0.3)
                            data[item[0]] = ''
                            fed_count += 1
                            break
                        except Full:
                            # gather some results
                            try:
                                while True:
                                    i,v = results.get(True, 0.3)
                                    data[i] = v
                                    total_count += 1
                                    p.set(count.value)
                            except Empty:
                                pass
                    p.set(count.value)

            # gathering results from jobs
            while total_count < len(data):
                try:
                    i,v = results.get(True, 0.3)   # timeout delay small enough to update progress bar, see below
                    data[i] = v
                    total_count += 1
                except Empty:
                    pass
                p.set(count.value)  # even if no results are received (cached somewhere), the counter will be updated after get() timeout above
                # NOTE: There might be a slight delay after reaching 100%, because the finished results counter is ahead of received results counter;
                # will stay at 100% until all results are received.

            p.set(total_count)
            p.complete()

            # wait for jobs to finish
            queue.join()
            for job in jobs:
                job.join()

        except KeyboardInterrupt:
            print >> sys.stderr, '\nInterrupted, aborting'
            os.abort() # abort instead of exit so that multiprocessing won't wait

        print 'Writing', parsed_filename, '...'
        with open(parsed_filename, 'w') as f:
            for item in data:
                print >> f, item

        # convert parse tree to dependency tree
        print "Convert Charniak parse tree to Stanford Dependency tree ..."
        subprocess.call('./scripts/stdconvert.sh '+parsed_filename,shell=True)
        

class StanfordDepParser(DepParser):
    
    def parse(self,sent_filename):
        """
        separate dependency parser
        """

        # jars = ["stanford-parser-3.3.1-models.jar",
        #         "stanford-parser.jar"]
        jars = ["stanford-corenlp-3.2.0-models.jar",
                "stanford-corenlp-3.2.0.jar"]
       
        # if CoreNLP libraries are in a different directory,
        # change the corenlp_path variable to point to them
        stanford_path = os.path.join(os.path.dirname(__file__), "stanfordnlp/stanford-corenlp-full-2013-06-20")
        
        java_path = "java"
        classname = "edu.stanford.nlp.parser.lexparser.LexicalizedParser"
        # include the properties file, so you can change defaults
        # but any changes in output format will break parse_parser_results()
        #props = "-props default.properties"
        flags = "-tokenized -sentences newline -outputFormat typedDependencies -outputFormatOptions basicDependencies,markHeadNodes"
        # add and check classpaths
        model = "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz"
        jars = [os.path.join(stanford_path, jar) for jar in jars]
        for jar in jars:
            if not os.path.exists(jar):
                print "Error! Cannot locate %s" % jar
                import sys
                sys.exit(1)

        #Change from ':' to ';'
        # spawn the server
        start_depparser = "%s -Xmx2500m -cp %s %s %s %s %s" % (java_path, ':'.join(jars), classname, flags, model, sent_filename)
        if VERBOSE: print start_depparser
        #incoming = pexpect.run(start_depparser)    
        process = subprocess.Popen(start_depparser.split(),shell=False,stdout=subprocess.PIPE)
        incoming = process.communicate()[0]
        print 'Incoming',incoming
        
        return incoming


class ClearDepParser(DepParser):

    def parse(self,sent_filename):
        subprocess.call(["cp",sent_filename,sent_filename+'.tmp'])
        subprocess.call(["sed","-i",r':a;N;$!ba;s/\n/\n\n/g',sent_filename])
        subprocess.call(["sed","-i",r':a;N;$!ba;s/\s/\n/g',sent_filename])

        clear_path="/home/j/llc/cwang24/Tools/clearnlp"
        extension = "clear.dep"
        
        start_depparser = "%s/clearnlp-parse %s %s" % (clear_path,sent_filename,extension)
        print start_depparser
        extcode = subprocess.call(start_depparser,shell=True)
        dep_result = open(sent_filename+'.'+extension,'r').read()
        subprocess.call(["mv",sent_filename+'.tmp',sent_filename])
        return dep_result

class TurboDepParser(DepParser):
    
    def parse(self,sent_filename):
        turbo_path="/home/j/llc/cwang24/Tools/TurboParser"
        extension = "turbo.dep"

        start_depparser = "%s/scripts/parse-tok.sh %s %s" % (turbo_path,sent_filename,sent_filename+'.'+extension)
        print start_depparser
        subprocess.call(start_depparser,shell=True)
        dep_result = open(sent_filename+'.'+extension,'r').read()
        return dep_result


class MateDepParser(DepParser):
    
    def parse(self,sent_filename):
        mate_path="/home/j/llc/cwang24/Tools/MateParser"
        extension = "mate.dep"

        start_depparser = "%s/parse-eng %s %s" % (mate_path,sent_filename,sent_filename+'.'+extension)
        print start_depparser
        subprocess.call(start_depparser,shell=True)
        dep_result = open(sent_filename+'.'+extension,'r').read()
        return dep_result
