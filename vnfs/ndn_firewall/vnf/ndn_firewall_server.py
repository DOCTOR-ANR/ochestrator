from flask import Flask,json,request,Response
from nfd_router_em import RouterEM
from ndn_firewall_em import FirewallEM
import sys
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread


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

router_em = RouterEM(logger, vnfm_host, vnfm_port)
logger.debug('VNF EM is UP')
firewall_em = FirewallEM(logger, vnfm_host, vnfm_port)
logger.debug('Firewall EM is UP')

def enforce_initial_config(config):
    router_em.enforce_initial_configuration(config)


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

def setup_firewall(config):
    firewall_em.enforce_initial_configuration(config)

@app.route('/vnfm/firewall_initial_configuration', methods=['POST'])
def firewall_initial_configuration():
    if not initial_configuration.received:
        logger.debug("firewall initial configuration received from VNFM")
        config = json.loads(request.data)
        Thread(target=setup_firewall, args=(config, )).start()
        firewall_initial_configuration.received = True
    else:
        logger.debug("initial configuration already received")
    return 'OK'
firewall_initial_configuration.received=False

@app.route('/vnfm/update_configuration', methods=['POST'])
def update_configuration():
    logger.debug("new configuration received from VNFM")
    config = json.loads(request.data)
    firewall_em.update_configuration(config)
    return 'OK'

def start_app():
    logger.debug("starting router server")
    app.run(host=server_ip, port=4999, debug=False)

if __name__ == '__main__':
    Thread(target=start_app).start()
    router_em.notify_vnfm(server_ip, host_name)


"""
if __name__ == '__main__':
    app.run(host=vnfm_host, port=vnfm_port, use_reloader=False)
"""
