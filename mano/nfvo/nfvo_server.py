from werkzeug.serving import run_simple
from flask import Flask,json,request,Response
import sys
from orchestrator import Orchestrator
import threading
import time
import pdb
import logging
from logging.handlers import RotatingFileHandler
from collections import namedtuple
import pprint
import base64
from subprocess import Popen

_deployment_duration = int(round(time.time() * 1000))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('activity.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)
logger.addHandler(stream_handler)

# WSGI Application
app = Flask(__name__)

#launch NDN orchestrator
tosca_file_path = sys.argv[1]
nfvo_host, nfvo_port = sys.argv[2].split(":")
#vnfm_port = sys.argv[3]

nfvo = Orchestrator(logger, nfvo_host, nfvo_port)
logger.debug('NFVO is UP!')
nfvo.create_vnffg(tosca_file_path)

PoisonedContentAlert = namedtuple('PoisonedContentAlert', ['probe_id', 'poisoned_content_list'])

#def handle_cpa(alert):
#    nfvo.apply_cpa_policy(alert)

#################################################################
#################################################################

@app.route('/vnfm/notifications/vnfsUP', methods=['POST'])
def vnfsUP():
    data = json.loads(request.data)
    deploy_log = open("deploy_log", "a")         
    deploy_log.write(base64.b64decode(data))
    global _deployment_duration
    _deployment_duration = int(round(time.time() * 1000)) - _deployment_duration
    print('\x1b[6;30;42m' + "deployment duration == "+str(_deployment_duration)+ '\x1b[0m')
    return 'OK'


@app.route('/vnfm/notifications/vnfmUP')
def vnfmUP():
    logger.debug('VNFM UP notification received')
    thread = threading.Thread(target=sendConfigToVnfm, args=())
    thread.start()
    logger.debug('sending ACK for VNFM UP notification')
    return 'OK'


def sendConfigToVnfm():
    logger.debug('sending vnfs initial configuration to VNFM')
    nfvo.send_VDUs_configs_to_vnfm()

#################################################################
#################################################################

@app.route('/vnfm/notifications/CPA', methods=['POST'])
def cpa_detected():
    data = json.loads(request.data)
    if data['alert_id'] == 102:
        logger.debug('CPA notification received')
        threading.Thread(target=handle_cpa, args=([data['probe_id']])).start()
    else:
        logger.debug('no corresponding alert_id to : {0}'.format(data['alert_id']))
    return 'OK'


def handle_cpa(probe_id):
    nfvo.handle_cpa_alert(probe_id)

#################################################################
#################################################################


@app.route('/vnfm/sv/report', methods=['POST'])
def poisoned_content_alert():
    #print 'sv report in'
    data = json.loads(request.data)
    #print 'sv report {0}'.format(data)
    threading.Thread(target=handle_poisoned_content_alert, args=([data])).start()
    return 'OK'


def handle_poisoned_content_alert(data):
    report = {'invalid_signature_packet_name': data['invalid_signature_packet_name'],
              'probe_id': int(data['name'])}
    nfvo.handle_sv_report(report)


#################################################################
#################################################################

@app.route('/vnfm/notifications/pit_stats_in', methods=['POST'])
def stats_in():
    data = json.loads(request.data)
    if data['alert_id'] == 103:
        threading.Thread(target=handle_pit_stats_in, args=([data])).start()
    else:
        logger.debug('no corresponding alert_id to : {0}'.format(data['alert_id']))
    return 'OK'


def handle_pit_stats_in(data):
    probe_id = data['probe_id']
    count_metric = data['count_metric']
    ip = data['ip']
    nfvo.handle_pit_stats_in(probe_id, count_metric, ip)

#################################################################
#################################################################

def notifyVNFM():
    logger.debug('sending notification NFVO is up to VNFM')
    time.sleep(5)
    nfvo.vnfm_client.notify_vnfm()


if __name__ == '__main__':
    thread = threading.Thread(target=notifyVNFM, args=())
    thread.start()
    logger.debug('starting NFVO Server')
    run_simple(nfvo_host, nfvo_port, app,
               use_reloader=False, use_debugger=True, use_evalex=True)

"""
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3999, use_reloader=False)
"""
