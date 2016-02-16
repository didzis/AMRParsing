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

import pickle
import numpy as np
import struct


class Pickler(pickle.Pickler):

    def __init__(self, file, protocol=None):
        if protocol == 0 or protocol == 1:
            raise ValueError("npickle does not support protocols 0 and 1")
        pickle.Pickler.__init__(self, file, protocol)
        self.file = file
        self.dispatch[np.ndarray] = Pickler.save_numpy_ndarray

    def save_numpy_ndarray(self, obj, pack=struct.pack):
        self.write('n')                             # opcode for numpy arrays
        dtype = str(obj.dtype)                      # prepare type string
        self.write(pack('B', len(dtype)))           # write type string size
        self.write(dtype)                           # write type string
        self.write(pack('I', obj.ndim))             # write number of dimensions
        self.write(pack('I'*obj.ndim, *obj.shape))  # write shape
        obj.tofile(self.file)                       # write numpy array data
        self.memoize(obj)


class Unpickler(pickle.Unpickler):

    def __init__(self, file):
        pickle.Unpickler.__init__(self, file)
        self.file = file
        self.dispatch['n'] = Unpickler.load_numpy_ndarray

    def load_numpy_ndarray(self):
        dtype = np.dtype(self.read(struct.unpack('B', self.read(1))[0]))
        ndim = struct.unpack('I', self.read(4))[0]
        shape = struct.unpack('I'*ndim, self.read(ndim*4))
        # number of elements in array
        count = 1
        for sz in shape:
            count *= sz
        array = np.fromfile(self.file, dtype=dtype, count=count, sep='')
        array = array.reshape(shape)                # restore original shape
        self.append(array)


def dump(obj, filename):
    with open(filename, 'wb') as f:
        Pickler(f, protocol=-1).dump(obj)

def load(filename):
    with open(filename, 'rb') as f:
        return Unpickler(f).load()


# Convenience functions for compressed pickle output (uses external utilities and pipes)
# NOTE: because of using numpy's tofile and fromfile, file-like objects are not supported (like GzipFile)

def dump_bzip2(obj, filename):
    import pipes
    t = pipes.Template()
    t.append('bzip2 --compress', '--')
    with t.open(filename, 'w') as f:
        Pickler(f, protocol=-1).dump(obj)

def load_bzip2(filename):
    import pipes
    t = pipes.Template()
    t.append('bzip2 --decompress --stdout', '--')
    with t.open(filename, 'r') as f:
        return Unpickler(f).load()

def dump_gzip(obj, filename):
    import pipes
    t = pipes.Template()
    t.append('gzip', '--')
    with t.open(filename, 'w') as f:
        Pickler(f, protocol=-1).dump(obj)

def load_gzip(filename):
    import pipes
    t = pipes.Template()
    t.append('gzip --decompress --stdout', '--')
    with t.open(filename, 'r') as f:
        return Unpickler(f).load()

