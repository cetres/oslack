import os
import sys
import logging

workers = int(os.environ.get('GUNICORN_PROCESSES', '3'))
threads = int(os.environ.get('GUNICORN_THREADS', '1'))

forwarded_allow_ips = '*' 
secure_scheme_headers = { 'X-Forwarded-Proto': 'https' }

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

def on_starting(server):
    sys.path.append(os.getcwd())
    logging.debug("Caminho: %s" % os.getcwd())
    from oslack.watch import KubeWatch
    server.kubeWatch = KubeWatch()
    server.kubeWatch.start()
    
def on_exit(server):
    server.kubeWatch.interrupt()
    logging.info('KubeWatch interrupted')