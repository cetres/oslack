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

import os
from datetime import datetime
import logging
import time
import queue
from threading import Thread, Event
from pprint import pformat

from slackclient import SlackClient

import yaml

class WorkerSender(Thread):
    ''' Class to send a message to slack
    '''
    _channels = None
    _config = None
    _queue = None
    _sc = None
    
    def __init__(self, config, m_queue, channels):
        super(WorkerSender, self).__init__()
        self._config = config
        self._queue = m_queue
        self._channels = channels
        self.stoprequest = Event()
        self._sc = SlackClient(self._config["token"])


    def run(self):
        while not self.stoprequest.isSet():
            try:
                as_user = False
                message = self._queue.get(True, 0.05)
                logging.info("Sending: %s" % message)
                channel = message["channel"]
                if channel in self.channels:
                    as_user = self.channels[channel]["is_member"]
                else:
                    logging.error("Cannot send a message to a non existent channel: %s" % channel)
                    
                ret = self._sc.api_call(
                        "chat.postMessage",
                        channel="#%s" % message["channel"],
                        text=message["text"],
                        as_user=as_user)
                logging.debug("Send result: %s" % pformat(ret))
                
            except queue.Empty:
                continue

    def update_channels(self):
        self._sc.api_call(
            "channels.list",
            exclude_archived=1
        )
    
    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerSender, self).join(timeout)

class SlackSender(object):
    _channels = {}
    _config = None
    _queue = None
    _pool = None
    
    def __init__(self, config, num_workers=1):
        self._config = config
        self._verify_channels()
        self._queue = queue.Queue()
        self._pool = [ WorkerSender(self._config.slack, self._queue, self._channels) for i in range(num_workers) ]
        for w in self._pool:
            w.start()
    
    def _verify_channels(self):
        conf_channels = set([a["channel"] for a in self._config.alerts])
        sc = SlackClient(self._config.slack["token"])
        slack_channels = sc.api_call(
            "channels.list",
            exclude_archived=1
        )
        if slack_channels["ok"] == "False":
            logging.critical("Error logging at Slack: %s" % cs["error"])
            return
        for c in slack_channels["channels"]:
            self._channels[c["name"]] = c
        logging.debug("Channels: %s" % pformat(slack_channels))
        for c in conf_channels:
            if c not in slack_channels:
                logging.error("Slack channel %s does not exist" % c)
                continue
            if slack_channels[c]["is_archived"]:
                logging.warning("Channel %s is marked as archived" % c)
            if not slack_channels[c]["is_member"]:
                logging.warning("Bot is not member of channel %s" % c)
                
    
    def send(self, event, channel=None):
        self._queue.put(event)
        
    def terminate(self):
        for t in self._pool:
            t.join()