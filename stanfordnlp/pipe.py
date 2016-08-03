#!/usr/bin/env python
# coding=utf-8

import sys, os, subprocess, json, time
from threading import Thread

def based(*parts):
    return os.path.join(os.path.dirname(__file__), *parts)

class CoreNLP:

    def __init__(self, args=['-props', based('default.properties'), '-threads', '8'], cmd=based('run.sh'), verbose=False, name='CoreNLP:'):
        if type(args) is str or type(args) is unicode:
            args = [x for x in args.split(' ') if x]
        self.cmd = [cmd] + list(args)
        self.verbose = verbose
        self.proc = None
        self.ready = False
        self.name = name
        self.start()

    def start(self):
        try:
            self.ready = False
            self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print >> sys.stderr, 'Unable to start:', ' '.join(self.cmd)
            raise

        self.thread = Thread(target=self.__stderr_watch)
        self.thread.daemon = True
        self.thread.start()

        return self.wait_ready()

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self("")
            self.ready = False

    def __stderr_watch(self):
        for line in iter(self.proc.stderr.readline, ''):
            line = line.strip()
            if self.verbose:
                print >> sys.stderr, self.name, line
            if self.proc.poll() is not None:
                self.ready = False
                # terminated
                break
            if line == "Ready":
                self.ready = True

    def wait_ready(self):
        while self.proc is not None and self.proc.poll() is None and not self.ready:
            time.sleep(0.5)
        return self.proc is not None and self.proc.poll() is None and self.ready
    
    def __call__(self, text, debug=False):

        # start or restart
        if self.proc is None or self.proc.poll() is not None:
            if not self.start():
                return

        # split lines
        if type(text) is str or type(text) is unicode:
            text = text.strip().split('\n')
        # join lines
        if type(text) is list or type(text) is tuple:
            text = '\n'.join(l for l in (x.strip() for x in text) if l)

        if debug:
            print >> sys.stderr, self.name, '<<', text+'\n'
        self.proc.stdin.write(text+'\n\n')
        self.proc.stdin.flush()

        # wait for output
        if self.proc.poll() is not None:
            return

        line = self.proc.stdout.readline().strip()
        if line and line.startswith('Threads'):
            # not expected JSON output, read another line
            line = self.proc.stdout.readline().strip()

        if debug:
            print >> sys.stderr, self.name, '>>', line

        if line:
            return json.loads(line)


def make_nlp(threads=4, props='default.properties', verbose=False, name='CoreNLP:'):
    if not os.path.isabs(props):
        props = based(props)
    return CoreNLP(['-props', props, '-threads', str(threads)], verbose=verbose, name=name)


if __name__ == "__main__":

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print 'usage:', sys.argv[0], '[options] [file1] [file2] ... [-]'
        print
        print 'options:'
        print '-v, --verbose            log CoreNLP stderr output'
        print '-d, --debug              show raw input/output payload'
        print '-l, --line               use sentence-per-line split'
        print
        print 'Use "-" for stdin, can be combined with other files.'
        print 'If no files and/or stdin specified, will run default test case.'
        print
        sys.exit(0)

    debug = '--debug' in args or '-d' in args
    verbose = '--verbose' in args or '-v' in args
    line_split = '--line' in args or '-l' in args

    files = [arg for arg in args if not arg.startswith('-')]

    if files or '-' in args:

        if line_split:
            print >> sys.stderr, 'Starting sentence-per-line CoreNLP ...'
            nlp = make_nlp(verbose=verbose)
        else:
            print >> sys.stderr, 'Starting sentence-split CoreNLP ...'
            nlp = make_nlp(props='default_ssplit.properties', name='CoreNLP(ssplit):', verbose=verbose)

        for filename in files:
            with open(filename, 'r') as f:
                if debug:
                    print >> sys.stderr, '<<<<', filename
                text = f.read()
                result = nlp(text, debug=debug)
                print result

        if '-' in args:
            if debug:
                print >> sys.stderr, '<<<< stdin'
            text = sys.stdin.read()
            result = nlp(text, debug=debug)
            print result

        sys.exit(0)

    # some test cases below

    print >> sys.stderr, 'Starting sentence-split CoreNLP ...'
    text = """We’ve all seen the films. A man is caught in quicksand, begging onlookers for help, but the more he struggles, the further down into the sand he is sucked until eventually he disappears. All that’s left is sinister sand, and maybe his hat. There are so many films featuring death by quicksand that Slate journalist Daniel Engbar has even tracked the peak quicksand years in film. In the 1960s, one in 35 films featured quicksands. They were in everything from Lawrence of Arabia to The Monkees."""
    ssplit = make_nlp(props='default_ssplit.properties', name='CoreNLP(ssplit):', verbose=verbose)
    print ssplit(text, debug=debug)
    
    print >> sys.stderr, 'Starting sentence-per-line CoreNLP ...'
    lsplit = make_nlp(verbose=verbose)

    r = lsplit("This is a sentence-per-line text input.\nSecond sentence in next line.", debug=debug)
    print r
    print >> sys.stderr, '---'
    r = lsplit("Testing multi-document input.", debug=debug)
    print r
    print >> sys.stderr, '---'
    r = lsplit("", debug=debug)    # this will exit
    print r
    print >> sys.stderr, '---'
    # must restart
    print >> sys.stderr, 'Re-starting sentence-per-line CoreNLP ...'
    r = lsplit("A sentence after restart.", debug=debug)
    print r
