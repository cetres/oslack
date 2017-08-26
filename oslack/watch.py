# -*- coding: utf-8 -*-
#
#
import os
from datetime import datetime, timezone
import logging
import time
from threading import Thread
from pprint import pformat
from urllib3.exceptions import MaxRetryError

import yaml
from kubernetes import client, config, watch


DEFAULT_CONFIG_FILE = "oslack.conf"


class KubeWatch(Thread):
    start_time = None
    config = None
    watch = None
    sender = None
    
    def __init__(self, sender):
        Thread.__init__(self)
        global DEFAULT_CONFIG_FILE
        self.start_time = datetime.now(timezone.utc)
        self._sender = sender
        logging.debug("Starting time: %s" % self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.config = { "slack": {}, "openshift": {} }
        self.config["slack"]["url"] = os.environ.get("SLACK_URL", None)
        self.config["slack"]["token"] = os.environ.get("SLACK_TOKEN", None)
        if os.path.exists(DEFAULT_CONFIG_FILE):
            self.config.update(yaml.load(open(DEFAULT_CONFIG_FILE, "r")))
            logging.info('Config file loaded - %s' % DEFAULT_CONFIG_FILE)
        else:
            logging.warning('Config file not found - %s' % DEFAULT_CONFIG_FILE)
        if "url" not in self.config["slack"]:
            logging.critical('Slack URL not found')
        if "token" not in self.config["slack"]:
            logging.critical('Slack Token not found')
        logging.debug(self.config)
        self.connect()
    
    def terminate(self):
        logging.info('Exiting KubeWatch')
        self.watch.stop()
    
    def connect(self):
        logging.debug('Running Thread KubeWatch...')
        kcli = config.new_client_from_config(config_file=self.config["openshift"].get("kube_config"))
        client.configuration.host = self.config["openshift"]["url"]
        client.configuration.api_key['authorization'] = "Bearer %s" % self.config["openshift"]["token"]
        logging.debug("Token: %s" % self.config["openshift"]["token"])
        if self.config["openshift"]["insecure"]:
            client.configuration.verify_ssl = False
        self.watch = watch.Watch()

    def send(self, msg_time, message):
        if msg_time > self.start_time:
            self._sender.send(message)
        

class EventsWatch(KubeWatch):
    def run(self):
        api = client.CoreV1Api()
        logging.debug("Watching events")
        try:
            for event in self.watch.stream(api.list_event_for_all_namespaces):
                message = "%s %s [%s]: %s" % (event['object'].first_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                                  event['object'].involved_object.name,
                                                  event['object'].involved_object.namespace,
                                                  event['object'].message)
                self.send(event['object'].first_timestamp, message)
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