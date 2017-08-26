# -*- coding: utf-8 -*-
#
#
import os
from datetime import datetime
import logging
import time
import queue
from threading import Thread, Event
from pprint import pformat

import yaml

class WorkerSender(Thread):
    _queue = None
    
    def __init__(self, m_queue):
        super(WorkerSender, self).__init__()
        self._queue = m_queue
        self.stoprequest = Event()

    def run(self):
        while not self.stoprequest.isSet():
            try:
                message = self._queue.get(True, 0.05)
                logging.info("Sending: %s" % message)
            except queue.Empty:
                continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerSender, self).join(timeout)

class SlackSender(object):
    _queue = None
    _pool = None
    
    def __init__(self, num_workers=1):
        self._queue = queue.Queue()
        self._pool = [ WorkerSender(self._queue) for i in range(num_workers) ]
        for w in self._pool:
            w.start()
    
    def send(self, event, channel=None):
        self._queue.put(event)
        
    def terminate(self):
        for t in self._pool:
            t.join()