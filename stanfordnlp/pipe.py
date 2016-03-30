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
    
    def __call__(self, text):

        # start or restart
        if self.proc is None or self.proc.poll() is not None:
            if not self.start():
                return

        # split lines
        if type(text) is str or type(text) is unicode:
            text = text.split('\n')
        # join lines
        if type(text) is list or type(text) is tuple:
            text = '\n'.join(l for l in (x.strip() for x in text) if l)

        self.proc.stdin.write(text+'\n\n')
        self.proc.stdin.flush()

        # wait for output
        if self.proc.poll() is not None:
            return

        line = self.proc.stdout.readline().strip()
        if line and line.startswith('Threads'):
            # not expected JSON output, read another line
            line = self.proc.stdout.readline().strip()

        if line:
            return json.loads(line)


def make_nlp(threads=4, props='default.properties', verbose=False, name='CoreNLP:'):
    if not os.path.isabs(props):
        props = based(props)
    return CoreNLP(['-props', props, '-threads', str(threads)], verbose=verbose, name=name)


if __name__ == "__main__":

    if True:
        text = """We’ve all seen the films.  A man is caught in quicksand, begging onlookers for help, but the more he struggles, the further down into the sand he is sucked until eventually he disappears. All that’s left is sinister sand, and maybe his hat. There are so many films featuring death by quicksand that Slate journalist Daniel Engbar has even tracked the peak quicksand years in film. In the 1960s, one in 35 films featured quicksands. They were in everything from Lawrence of Arabia to The Monkees."""
        ssplit = make_nlp(props='default_ssplit.properties')
        print(ssplit(text))
        quit()
    
    corenlp = CoreNLP()

    r = corenlp("Have a nice day.\nToday.")
    print r
    print('---')
    r = corenlp("Try again!")
    print r
    print('---')
    r = corenlp("")    # this will exit
    print r
    print('---')
    # must restart
    r = corenlp("Last try.")
    print r
