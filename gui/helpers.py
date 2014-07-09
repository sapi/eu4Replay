# Copyright Sean Purdon 2014
# All Rights Reserved

from threading import Thread
import time


class PeriodicThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None,
            verbose=None, period=None):
        if kwargs is None:
            kwargs = {}

        Thread.__init__(self, group=group, target=target, name=name, args=args,
                kwargs=kwargs, verbose=verbose)

        self.f = target
        self.args = args
        self.kwargs = kwargs

        assert period is not None
        self.period = period

        self.flStop = False

    def run(self):
        # note that this run loop is *not* synchronised properly wrt flStop
        while not self.flStop:
            start = time.time()
            self.f(*self.args)
            end = time.time()

            diff = (end - start)
            waitTime = self.period - diff

            if waitTime < 0:
                continue # uhoh, took too long!

            time.sleep(waitTime)

    def stop(self):
        self.flStop = True
        self.join(self.period*5)

        assert not self.isAlive(), \
                'Could not join thread after 5 periods'
