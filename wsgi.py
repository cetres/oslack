# -*- coding: utf-8 -*-
#
#
import os
import logging
from flask import Flask

DEFAULT_CONFIG_FILE = "oslack.conf"

application = Flask(__name__)


@application.route('/healthz', methods=['GET'])
def healthz():
    return "OK"


if __name__ == "__main__":
#    application = main()
    application.run()
