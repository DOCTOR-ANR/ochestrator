from flask import Flask,json,request,Response
from ingress_gateway_em import IngressGatewayEM
import sys
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread

#TODO: change in client url (ingress_gw not router)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('activity.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

# WSGI Application
app = Flask(__name__)

vnfm_host = sys.argv[1]
vnfm_port = sys.argv[2]
server_ip = sys.argv[3]
host_name = sys.argv[4]

iGW_em = IngressGatewayEM(logger, vnfm_host, vnfm_port)
logger.debug('ingress_gw EM is UP')

def enforce_initial_config(config):
    iGW_em.enforce_initial_configuration(config)


@app.route('/vnfm/init_configuration', methods=['POST'])
def initial_configuration():
    if not initial_configuration.received:
        logger.debug("Initial configuration received from VNFM")
        config = json.loads(request.data)
        Thread(target=enforce_initial_config, args=(config, )).start()
        initial_configuration.received = True
    else:
        logger.debug("initial configuration already received")
    return 'OK'
initial_configuration.received=False


def start_app():
    logger.debug("starting ingress_gw server")
    app.run(host=server_ip, port=4999, debug=False)

if __name__ == '__main__':
    Thread(target=start_app).start()
    iGW_em.notify_vnfm(server_ip, host_name)


"""
if __name__ == '__main__':
    app.run(host=vnfm_host, port=vnfm_port, use_reloader=False)
"""
