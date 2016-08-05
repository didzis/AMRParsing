#!/usr/bin/env python
# codec=utf-8

import sys, os, subprocess
from threading import Thread

class CoreNLPDepConv:

    def __init__(self, cmd=os.path.join(os.path.dirname(__file__), 'run.sh'), verbose=False, name='CoreNLPDepConv:'):
        self.cmd = cmd
        self.proc = None
        self.name = name
        self.verbose = verbose
        # self.start()

    def start(self):
        try:
            self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print >> sys.stderr, 'Unable to start:', self.cmd
            raise

        self.thread = Thread(target=self.__stderr_watch)
        self.thread.daemon = True
        self.thread.start()

        return self.proc.poll() is None

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self("")

    def __stderr_watch(self):
        for line in iter(self.proc.stderr.readline, ''):
            line = line.strip()
            if self.verbose:
                print >> sys.stderr, self.name, line
            if self.proc.poll() is not None:
                # terminated
                break
    
    def __call__(self, text):

        # start or restart
        if self.proc is None or self.proc.poll() is not None:
            self.start()

        self.proc.stdin.write(text.strip()+'\n')
        self.proc.stdin.flush()

        result = []

        # wait for output
        while True:
            line = self.proc.stdout.readline().strip()
            if not line:
                break
            result.append(line)

        return result


if __name__ == "__main__":
    
    conv = CoreNLPDepConv()

    r = conv("(S1 (S (NP (DT The) (NN center)) (VP (MD will) (VP (VB bolster) (NP (NP (NP (NNP NATO) (POS 's)) (NNS defenses)) (PP (IN against) (NP (NNP cyber) (NNS attacks)))))) (. .)))'))))))))")
    print r
    print '---'
    r = conv("(S1 (S (NP (DT The) (NN center)) (VP (MD will) (VP (VB bolster) (NP (NP (NP (NNP NATO) (POS 's)) (NNS defenses)) (PP (IN against) (NP (NNP cyber) (NNS attacks)))))) (. .)))'))))))))")
    print r
    print '---'
    r = conv("")    # this will exit the convertot
    print r
    print '---'
    # must restart convertor
    r = conv("(S1 (S (NP (DT The) (NN center)) (VP (MD will) (VP (VB bolster) (NP (NP (NP (NNP NATO) (POS 's)) (NNS defenses)) (PP (IN against) (NP (NNP cyber) (NNS attacks)))))) (. .)))'))))))))")
    print r
    print '---'
    r = conv("(())")
    print r
