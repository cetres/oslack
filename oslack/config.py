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
import logging

import yaml


DEFAULT_CONFIG_FILE = "oslack.conf"


class Config(object):
    def __init__(self):
        self._config = { "slack": {}, "openshift": {"insecure": False}, "alerts": [] }
        self._config["slack"]["url"] = os.environ.get("SLACK_API_URL", None)
        self._config["slack"]["token"] = os.environ.get("SLACK_API_TOKEN", None)
        if os.path.exists(DEFAULT_CONFIG_FILE):
            self._config.update(yaml.load(open(DEFAULT_CONFIG_FILE, "r")))
            logging.info('Config file loaded - %s' % DEFAULT_CONFIG_FILE)
        else:
            logging.warning('Config file not found - %s' % DEFAULT_CONFIG_FILE)
        if "token" not in self._config["slack"]:
            logging.critical('Slack Token not found')
        logging.debug(self._config)
    
    
    @property
    def alerts(self):
        return self._config["alerts"]

    @property
    def openshift(self):
        return self._config["openshift"]
    
    @property
    def slack(self):
        return self._config["slack"]