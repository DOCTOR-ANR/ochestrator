from flask import Flask,json,request,Response
from nfd_router_em import RouterEM
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
sv_mode = sys.argv[5]
probe_id = sys.argv[6]

router_em = RouterEM(logger, vnfm_host, vnfm_port, sv_mode, probe_id)
logger.debug('VNF EM is UP')

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


def update_configuration(config):
    router_em.update_configuration(config)

@app.route('/vnfm/update_configuration', methods=['POST'])
def handle_update_configuration():
    logger.debug("VNFM update configuration command")
    config = json.loads(request.data)
    Thread(target=update_configuration, args=(config, )).start()
    return 'OK'

def update_faces(faces):
    for prefix, face in faces.iteritems():
        logger.debug('VNFM -- update faces')
        logger.debug('prefix: {0} -- face: {1}'.format(prefix, face))
        deprectad_face = (face.split(':')[0])+(':6363')
        #TODO: I need to keep the same order of the best route
        router_em.unregister_face(prefix, deprectad_face)
        router_em.register_face(prefix, face)


@app.route('/vnfm/update_faces', methods=['POST'])
def handle_update_faces():
    logger.debug("faces update command")
    config = json.loads(request.data)
    Thread(target=update_faces, args=(config, )).start()
    return 'OK'


def update_mode(mode):
    router_em.update_mode(mode)

@app.route('/vnfm/update_mode', methods=['POST'])
def handle_update_mode():
    logger.debug("mode update message")
    config = json.loads(request.data)
    Thread(target=update_mode, args=(config, )).start()
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