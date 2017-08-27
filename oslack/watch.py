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
from datetime import datetime, timezone
import logging
import time
from threading import Thread
from pprint import pformat
from urllib3.exceptions import MaxRetryError

from kubernetes import client, config, watch


class KubeWatch(Thread):
    _start_time = None
    _config = None
    watch = None
    sender = None
    
    def __init__(self, conf, sender):
        Thread.__init__(self)
        global DEFAULT_CONFIG_FILE
        self._start_time = datetime.now(timezone.utc)
        self._config = conf
        self._sender = sender
        logging.debug("Starting time: %s" % self._start_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.connect()
    
    def terminate(self):
        logging.info('Exiting KubeWatch')
        self.watch.stop()
    
    def connect(self):
        logging.debug('Running Thread KubeWatch...')
        if "kube_config" in self._config.openshift:
            kcli = config.new_client_from_config(config_file=self._config.openshift["kube_config"])
            client.configuration.host = self._config.openshift["url"]
        else:
            client.configuration.host = "https://openshift.default.svc.cluster.local"
            client.configuration.ssl_ca_cert = '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'
        client.configuration.api_key_prefix['authorization'] = 'Bearer'
        client.configuration.api_key['authorization'] = self._config.openshift["token"]
        logging.debug("Token: %s" % self._config.openshift["token"])
        if self._config.openshift["insecure"]:
            client.configuration.verify_ssl = False
        self.watch = watch.Watch()

    def send(self, msg_time, message, source):
        if msg_time < self._start_time:
            return
        for a in self._config.alerts:
            if source.startswith(a["app"]):
                self._sender.send({"channel": a["channel"], "text": message})
        

class EventsWatch(KubeWatch):
    def run(self):
        api = client.CoreV1Api()
        logging.debug("Watching events")
        try:
            for event in self.watch.stream(api.list_event_for_all_namespaces):
                src = event['object'].involved_object.name
                message = "%s [%s]: %s" % (src,
                                           event['object'].involved_object.namespace,
                                           event['object'].message)
                self.send(event['object'].first_timestamp, message, src)
                logging.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
                #logging.info(message)
                #logging.info(pformat(event['object']))
            logging.warning("Exiting events watch")
        except MaxRetryError as err:
            logging.critical("Error connecting: %s" % str(err))


class PodsWatch(KubeWatch):
    def run(self):
        api = client.CoreV1Api()
        logging.debug("Watching pods")
        for event in self.watch.stream(api.list_pod_for_all_namespaces):
            logging.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            #logging.info(pformat(event['object']))
        logging.warning("Exiting pods watch")

class DeploymentsWatch(KubeWatch):
    def run(self):
        api = client.ExtensionsV1beta1Api()
        logging.debug("Watching deployments")
        for event in self.watch.stream(api.list_deployment_for_all_namespaces):
            logging.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            #logging.info(pformat(event['object']))
        logging.warning("Exiting deployments watch")