#!/bin/bash/env python
# coding=utf-8

import sys, os, traceback
from multiprocessing import Queue, Process, Lock, JoinableQueue, cpu_count
from multiprocessing.sharedctypes import Value
from Queue import Empty
from progress import Progress
from threading import Thread


# parse process body
def worker(processor, input_queue, results_queue, count, sync_after=0):

    local_count = 0
    try:
        while True:
            item = input_queue.get(True, 2)
            if item:
                index, data = item
                result = processor(data)
                results_queue.put((index, result))

            local_count += 1
            input_queue.task_done()

            if local_count >= sync_after:
                count.value += local_count
                local_count = 0

    except KeyboardInterrupt:
        # print >> sys.stderr, 'Job interrupted'
        os.abort() # abort instead of exit so that multiprocessing won't wait
        return
    except Empty:
        pass
    except:
        traceback.print_exc()

    if local_count > 0:
        count.value += local_count


def process(input_data, processor, max_refresh_delay=0.3):
    # will use multiprocessing to parallelize parsing

    queue = JoinableQueue()
    results_queue = Queue()

    # populate queue, reserve place for results
    results = []
    for i, data in enumerate(input_data):
        queue.put((i, data))
        results.append(None)

    p = Progress(len(input_data), estimate=True, values=True) # output progress bar

    # define jobs
    count = Value('i', 0)
    num_threads = cpu_count()
    sync_count = len(input_data)/1000/num_threads

    print 'Starting %i jobs ...' % num_threads

    jobs = [Process(target=worker, args=(processor, queue, results_queue, count, sync_count)) for i in range(num_threads)]

    try:
        # start jobs
        for job in jobs:
            job.start()

        # gathering results from jobs
        total_count = 0
        while total_count < len(input_data):
            try:
                item = results_queue.get(True, max_refresh_delay)   # timeout delay small enough to update progress bar, see below
                results[item[0]] = item[1]
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
    except:
        traceback.print_exc()

    return results


class Processor(Thread):

    def __init__(self, processor_factory, processes=4):
        Thread.__init__(self)
        self.processor_factory = processor_factory
        self.input_queue = JoinableQueue()
        self.results_queue = Queue()
        self.processes = processes
        self._stop = False
        self.__stop = None
        self.start()

    def stop(self):
        self._stop = True
        if self.__stop:
            self.__stop.value = 1

    @staticmethod
    def worker(make_processor, input_queue, results_queue, stop):
        processor = None
        try:
            processor = make_processor()
            while stop.value == 0:
                try:
                    while stop.value == 0:
                        item = input_queue.get(True, 0.5)
                        if item:
                            index, data = item
                            result = processor(data)
                            results_queue.put((index, result))

                        input_queue.task_done()
                except Empty:
                    pass
        except KeyboardInterrupt:
            # print >> sys.stderr, 'Job interrupted'
            # os.abort() # abort instead of exit so that multiprocessing won't wait
            pass
        except:
            traceback.print_exc()
        finally:
            if processor and hasattr(processor, 'stop'):
                processor.stop()
        # print >> sys.stderr, 'Job interrupted'

    def run(self):

        try:
            stop = Value('B', 0)
            self.__stop = stop

            jobs = [Process(target=self.worker, args=(self.processor_factory, self.input_queue, self.results_queue, stop)) for i in range(self.processes)]

            import time

            # start jobs
            for job in jobs:
                job.start()

            while not self._stop:
                time.sleep(0.5)

            stop.value = 1

            # wait for jobs to finish
            self.input_queue.join()
            for job in jobs:
                job.join()

        except KeyboardInterrupt:
            # print >> sys.stderr, '\nInterrupted, aborting'
            # os.abort() # abort instead of exit so that multiprocessing won't wait
            pass
        except:
            traceback.print_exc()

    def __call__(self, input_data):

        results = []
        for i, data in enumerate(input_data):
            self.input_queue.put((i, data))
            results.append(None)

        # gathering results from jobs
        total_count = 0
        while total_count < len(input_data):
            try:
                item = self.results_queue.get(True, 0.5)    # waiting happens here
                results[item[0]] = item[1]
                total_count += 1
            except Empty:
                pass

        return results
