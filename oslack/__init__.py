# -*- coding: utf-8 -*-
#
# Copyright 2017 Apartamento 101
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

from __future__ import absolute_import

import logging
from .config import Config
from .watch import EventsWatch
from .sender import SlackSender

__version__ = "1.0"

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

class Oslack(object):
    _watcher = None
    _sender = None
    
    def __init__(self):
        global __version__
        logging.info("Initializing Oslack version %s" % __version__)
        config = Config()
        self._sender = SlackSender(config)
        self._watcher = EventsWatch(config, self._sender)
        self._watcher.start()

    
    def terminate(self):
        self._watcher.terminate()
        self._sender.terminate()
        logging.info('Oslack terminated')