from werkzeug.serving import run_simple
from flask import Flask,json,request,Response
from nfd_vnfm import NFD_VNFM
import sys
from threading import Thread
import time
import copy


import logging

from logging.handlers import RotatingFileHandler


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

#TODO: get vnfm_overlay_ip by docker, not by bash
#import docker
#client = docker.from_env()

import pdb

# WSGI Application
front_app = Flask('front_app')
back_app = Flask('back_app')

#launch NDN vnfm
nfvo_host = sys.argv[1]
nfvo_port = sys.argv[2]
vnfm_bridge_ip = sys.argv[3]
vnfm_overlay_ip = sys.argv[4]
vnfm_port = sys.argv[5]

vnfm = NFD_VNFM(nfvo_host, nfvo_port, logger)
logger.debug('VNFM is UP!')

id_list=list()
id_list.append("EmptyList")

#TODO: all functions with threads to minimise request waiting

def vnfm_handle_egressGatewayJoin(container, interface, port):
    vnfm.handle_RouterJoin(container, interface, port)

@front_app.route('/eGW/notifications/eGW_UP', methods=['POST'])
def handle_eGW_up():
    logger.debug("eGW UP notification received")
    router_infos = json.loads(request.data)
    container = router_infos[u'container']
    interface = router_infos[u'listening_interface']
    port = router_infos[u'listening_port']
    Thread(target=vnfm_handle_egressGatewayJoin, args=[container, interface, port]).start()
    logger.debug("sending ACK for eGW")
    return 'OK'


def vnfm_handle_ingressGatewayJoin(container, interface, port):
    vnfm.handle_RouterJoin(container, interface, port)

@front_app.route('/iGW/notifications/iGW_UP', methods=['POST'])
def handle_iGW_up():
    logger.debug("iGW UP notification received")
    router_infos = json.loads(request.data)
    container = router_infos[u'container']
    interface = router_infos[u'listening_interface']
    port = router_infos[u'listening_port']
    Thread(target=vnfm_handle_ingressGatewayJoin, args=[container, interface, port]).start()
    logger.debug("sending ACK for iGW")
    return 'OK'


def vnfm_handle_RouterJoin(container, interface, port):
    vnfm.handle_RouterJoin(container, interface, port)

@front_app.route('/router/notifications/router_UP', methods=['POST'])
def handle_vnf_up():
    logger.debug("vnf UP notification received")
    router_infos = json.loads(request.data)
    container = router_infos[u'container']
    interface = router_infos[u'listening_interface']
    port = router_infos[u'listening_port']
    Thread(target=vnfm_handle_RouterJoin, args=[container, interface, port]).start()
    return 'OK'

def notifyNFVO():
    logger.debug('sending VNFM UP notification to NFVO')
    vnfm.nfvo_client.notify_nfvo()

@back_app.route('/nfvo/notifications/nfvoUP')
def nfvoUP():
    logger.debug("NFVO UP notification received")
    Thread(target=notifyNFVO).start()
    return 'OK'


@back_app.route('/nfvo/faces/configuration', methods=['POST'])
def initial_configuration():
    if not initial_configuration.received:
        logger.debug("VNFs initial configuration received from NFVO")
        data = json.loads(request.data)
        vnfm.set_managed_vnfs_list(data['vnfs_id'])
        config = {key:data[key] for key in data.keys() if key != 'vnfs_id'}
        vnfm.embed_vnfs_initial_configuration(config)
        logger.debug(str(config))
        initial_configuration.received = True
    else:
        logger.debug("initial configuration already received")
    return 'OK'
initial_configuration.received=False

@back_app.route('/nfvo/firewall/update', methods=['POST'])
def update_firewall():
    data = json.loads(request.data)
    vnfm.update_firewall_config(data["vdu_id"], data['prefix_list'])
    logger.debug(str(data))
    initial_configuration.received = True
    return 'OK'

@front_app.route('/doctor/MMTenant/report', methods=['POST'])
def mmt_report():
    data = request.values.to_dict()['data']
    data = json.loads(data)
    data["ip"]=request.remote_addr
    logger.debug(str(data))
    print data

    if data['alert_id'] == 102:
        vnfm.nfvo_client.forward_cpa_alert(data)
    elif data['alert_id'] == 103:
        logger.debug(data)
        vnfm.nfvo_client.forward_pit_stats_in(data)

    return 'OK'


def forward_sv_report(data):
    vnfm.nfvo_client.forward_sv_report(data)


@front_app.route('/sv/report', methods=['POST'])
def handle_sv_report():
    logger.debug("SV notification received")
    data = json.loads(request.data)
    Thread(target=forward_sv_report, args=(data, )).start()
    return 'OK'


def update_service(config):
    vnfm.update_service(config['container_down'],
                        config['ingress_configurations'],
                        config['replicas_configurations'])

@back_app.route('/nfvo/update_service', methods=['POST'])
def handle_update_service():
    data = json.loads(request.data)
    Thread(target=update_service, args=(data, )).start()
    return 'OK'

def finish_scale_out(config):
    vnfm.finish_scale_out(config['container_down'],
                        config['ingress_configurations'],
                        config['replicas_configurations'])

@front_app.route('/router/notifications/finish_scale_out', methods=['POST'])
def handle_finish_scale_out():
    data = json.loads(request.data)
    Thread(target=finish_scale_out, args=(data, )).start()
    return 'OK'

def update_faces(data):
    router_id = data['router_id']
    faces = data['faces']
    vnfm.vnf_clients[router_id].send_update_faces(faces)

@back_app.route('/nfvo/update_faces', methods=['POST'])
def handle_update_faces():
    data = json.loads(request.data)
    Thread(target=update_faces, args=(data, )).start()
    return 'OK'

def update_router_mode(router_mode):
    router_id = router_mode['router_id']
    mode = router_mode['router_mode']
    vnfm.vnf_clients[router_id].send_update_mode(mode)

@back_app.route('/nfvo/update_router_mode', methods=['POST'])
def handle_update_router_mode():
    data = json.loads(request.data)
    Thread(target=update_router_mode, args=(data, )).start()
    return 'OK'


def start_front_app():
    logger.debug("starting VNFM server on admin_net(VNFM<-->VNFs)")
    front_app.run(host=vnfm_overlay_ip, port=4999, debug=False)

def start_back_app():
    logger.debug("starting VNFM server on bridge_net (VNFM<-->NFVO)")
    back_app.run(host=vnfm_bridge_ip, port=vnfm_port, debug=False)

if __name__ == '__main__':
    Thread(target=start_back_app).start()
    start_front_app()

"""
if __name__ == '__main__':
    app.run(host=vnfm_host, port=vnfm_port, use_reloader=False)
"""
