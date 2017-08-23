# -*- coding: utf-8 -*-
#
#
import os
import logging
import urllib3
import time
import threading
from flask import Flask
import yaml
import asyncio
from kubernetes import client, config, watch

DEFAULT_CONFIG_FILE = "oslack.conf"

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

class KubeWatch(threading.Thread):
    config = { "slack": {}, "openshift": {} }
    v1 = None
    v1ext = None
    watch_pods = None
    watch_deployments = None
    
    def load_config(self):
        global DEFAULT_CONFIG_FILE
        self.config["slack"]["url"] = os.environ.get("SLACK_URL", None)
        self.config["slack"]["token"] = os.environ.get("SLACK_TOKEN", None)
        if os.path.exists(DEFAULT_CONFIG_FILE):
            self.config.update(yaml.load(open(DEFAULT_CONFIG_FILE, "r")))
        else:
            logging.warning('Config file not found')
        if self.config["slack"].get("url", None) is None:
            logging.critical('Slack URL not found')
        if self.config["slack"].get("token", None) is None:
            logging.critical('Slack Token not found')
    
    def interrupt(self):
        logging.info('Exiting KubeWatch')
        self.watch_pods.stop()
        self.watch_deployments.stop()
        self.cancel()

    async def pods(self):
        self.watch_pods = watch.Watch()
        for event in self.watch_pods.stream(self.v1.list_pod_for_all_namespaces):
            logger.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            await asyncio.sleep(0)
    
    async def deployments(self):
        self.watch_deployments = watch.Watch()
        for event in self.watch_deployments.stream(self.v1ext.list_deployment_for_all_namespaces):
            logger.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
            await asyncio.sleep(0)
    
    def run(self):
        self.load_config()
        logging.debug('Running Thread KubeWatch...')
        kcli = config.new_client_from_config(config_file=self.config["openshift"].get("kube_config"))
        client.configuration.host = self.config["openshift"]["url"]
        client.configuration.api_key['authorization'] = "Bearer %s" % self.config["openshift"]["token"]
        if self.config["openshift"]["insecure"]:
            client.configuration.verify_ssl = False
        self.v1 = client.CoreV1Api()
        self.v1ext = client.ExtensionsV1beta1Api()
        ioloop = asyncio.get_event_loop()
        ioloop.create_task(self.pods())
        ioloop.create_task(self.deployments())
        ioloop.run_forever()


application = Flask(__name__)
kubeWatch = KubeWatch()
kubeWatch.start()

@application.route('/healthz', methods=['GET'])
def healthz():
    return "OK"


if __name__ == "__main__":
#    application = main()
    application.run()
