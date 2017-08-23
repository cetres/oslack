# -*- coding: utf-8 -*-
#
#
import os
import logging
import time
import threading
import yaml
import asyncio
from kubernetes import client, config, watch

DEFAULT_CONFIG_FILE = "oslack.conf"


class KubeWatch(threading.Thread):
    config = None
    ioloop = None
    watch_pods = None
    watch_deployments = None
    
    def load_config(self):
        global DEFAULT_CONFIG_FILE
        if self.config is None:
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
    
    def interrupt(self):
        logging.info('Exiting KubeWatch')
        self.watch_pods.stop()
        self.watch_deployments.stop()
        self.ioloop.stop()
        self.ioloop.close()

    async def pods(self):
        v1 = client.CoreV1Api()
        self.watch_pods = watch.Watch()
        for event in self.watch_pods.stream(v1.list_pod_for_all_namespaces):
            logging.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            await asyncio.sleep(1.0)
        logging.error("Exiting watch pods")
    
    async def deployments(self):
        v1ext = client.ExtensionsV1beta1Api()
        self.watch_deployments = watch.Watch()
        for event in self.watch_deployments.stream(v1ext.list_deployment_for_all_namespaces):
            logging.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            await asyncio.sleep(1.0)
        logging.error("Exiting watch deployments")
    
    def run(self):
        self.load_config()
        logging.debug('Running Thread KubeWatch...')
        if self.ioloop is None:
            logging.debug('Initializing ioloop...')
            kcli = config.new_client_from_config(config_file=self.config["openshift"].get("kube_config"))
            client.configuration.host = self.config["openshift"]["url"]
            client.configuration.api_key['authorization'] = "Bearer %s" % self.config["openshift"]["token"]
            logging.debug("Token: %s" % self.config["openshift"]["token"])
            if self.config["openshift"]["insecure"]:
                client.configuration.verify_ssl = False
            #self.v1 = client.CoreV1Api()
            #self.v1ext = client.ExtensionsV1beta1Api()
            self.ioloop = asyncio.new_event_loop()
            self.ioloop.create_task(self.pods())
            self.ioloop.create_task(self.deployments())
            self.ioloop.run_forever()