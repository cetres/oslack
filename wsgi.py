#
#

import logging
import time
import threading
from flask import Flask
import atexit
import yaml
import asyncio
import websockets

DEFAULT_CONFIG_FILE = "oslack.conf"

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

class Oslack(threading.Thread):
    config = {"slack": {}, "openshift": {}}
    
    def load_config(self):
        global DEFAULT_CONFIG_FILE
        self.config["slack"]["url"] = os.environ.get("SLACK_URL", None)
        self.config["slack"]["token"] = os.environ.get("SLACK_TOKEN", None)
        if os.path.exists(DEFAULT_CONFIG_FILE):
            self.config.update(yaml.load(open(CONFIG_FILE, "r")))
        else:
            logging.warning('Config file not found')
        if self.config["slack"].get("url", None) is None:
            logging.critical('Slack URL not found')
        if self.config["slack"].get("token", None) is None:
            logging.critical('Slack Token not found')
    
    def interrupt(self):
        logging.info('Exiting Oslack')
        self.cancel()

    async def os_listen(self):
        url = "%s/" % self.config["openshift"]["url"]
        async with websockets.connect(url) as websocket:
            name = input("What's your name? ")
            await websocket.send(name)
            print("> {}".format(name))
            greeting = await websocket.recv()
            print("< {}".format(greeting))

    def run(self):
        logging.debug('Running Thread Oslack...')
        while True:
            asyncio.get_event_loop().run_until_complete(os_listen())
            logging.error('Async has stopped unexpectedly')
            time.sleep(10)


def main():
    app = Flask(__name__)
    oslack = Oslack()
    oslack.start()
    
    @app.route('/healthz', methods=['GET'])
    def healthz():
        return "OK"

    atexit.register(oslack.interrupt)
    return app



if __name__ == "__main__":
    app = create_app()
    app.run()