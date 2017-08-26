# -*- coding: utf-8 -*-
#
#
import logging
from .watch import EventsWatch
from .sender import SlackSender




class Oslack(object):
    _watcher = None
    _sender = None
    
    def __init__(self):
        self._sender = SlackSender()
        self._watcher = EventsWatch(self._sender)
        self._watcher.start()

    
    def terminate(self):
        self._watcher.terminate()
        self._sender.terminate()
        logging.info('KubeWatch interrupted')