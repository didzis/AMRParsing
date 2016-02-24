#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Didzis Gosko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, datetime

def print_progress(progress, width=70, prefix='', format='%.2f %% ', stream=sys.stderr):
    completed = int(width*progress)
    if completed > width: completed = width
    elif completed < 0: completed = 0
    tip = '>' if progress > 0 or completed < width else ''
    done = '='*completed
    left = tip+' '*(width-completed-len(tip)) if completed < width else ''
    stream.write(('\r%s[%s%s] '+format) % (prefix, done, left, progress*100))
    stream.flush()

class Progress:
    
    def __init__(self, end=100, start=0, precision=0.1, format="%5.1f%% ", prefix="", width=70, estimate=False, values=False, stream=sys.stderr):
        self.redraw_hi, self.redraw_lo = start, start
        self.start = start
        self.end = end
        self.precision = precision/100.0
        self.format = format
        self.prefix = prefix
        self.width = width
        self.stream = stream
        self.value = start
        self.estimate = estimate
        self.start_dt = datetime.datetime.now()
        self.values = values
        self.range = float(end-start)

    def reset(end=None, start=None, precision=None):
        if end is not None:
            self.end = end
        if start is not None:
            self.start = start
        if precision is not None:
            self.precision = precision/100.0
        self.value = self.start
        self.range = float(self.end-self.start)
        self.start_dt = datetime.datetime.now()
        self.redraw_hi, self.redraw_lo = self.start, self.start

    def __iadd__(self, value):
        self.set(self.value + value)
        return self

    def __isub__(self, value):
        self.set(self.value - value)
        return self

    def set(self, value):
        self.value = value
        if value <= self.redraw_lo or value >= self.redraw_hi:
            self.redraw_lo = value - self.range*self.precision
            self.redraw_hi = value + self.range*self.precision
            if self.redraw_lo < self.start: self.redraw_lo = self.start
            if self.redraw_hi > self.end: self.redraw_hi = self.end
            self.draw()
        return value

    def draw(self, complete=False):
        width = self.width
        progress = float(self.value) / self.range
        completed = int(width*progress)
        if completed > width: completed = width
        elif completed < 0: completed = 0
        tip = '>' if progress > 0 or completed < width else ''
        done = '='*completed
        left = tip+' '*(width-completed-len(tip)) if completed < width else ''
        self.stream.write(('\r%s[%s%s] '+self.format) % (self.prefix, done, left, progress*100))
        if self.estimate:
            d = datetime.datetime.now()-self.start_dt
            total_seconds = d.total_seconds()
            elapsed_seconds = total_seconds
            if complete:
                self.stream.write(' total: ')
            else:
                total_seconds = total_seconds/progress - total_seconds if progress > 0 else 0
                self.stream.write(' est/ela: ')

            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                self.stream.write('% 2i:' % hours)
            self.stream.write('%02i:%02i ' % (minutes, seconds))

            if not complete:
                self.stream.write('/ ')

                total_seconds = elapsed_seconds
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    self.stream.write('% 2i:' % hours)
                self.stream.write('%02i:%02i ' % (minutes, seconds))

            if self.values:
                self.stream.write(' %i/%i  ' % (self.value-self.start, self.range))

            if complete:
                self.stream.write(' '*(2+8+(2 if hours > 0 else 0))) # 2 - label diff, 8 - extra time diff, 2 - extra time hours diff

        self.stream.flush()

    def complete(self):
        self.draw(True)
        self.stream.write('\n')
        self.stream.flush()


if __name__ == "__main__":
    sys.stderr.write('Simple demo\n')
    # print_progress(1)
    # sys.stderr.write('\n')
    p = Progress(1000, estimate=True, values=True)
    p.prefix = "Demo transfer: "
    import time
    for i in range(1000):
        # p.set(i)
        p += 1 
        time.sleep(0.01)
    p.complete()

