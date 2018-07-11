from egress_gateway_client import EgressGatewayClient
import subprocess
import time


class EgressGatewayEM(object):

    def __init__(self, logger, vnfm_host, vnfm_port):
        self.logger = logger
        print  ("creating vnf client with: %s, %s", vnfm_host, vnfm_port)
        self.client = EgressGatewayClient(logger, vnfm_host, vnfm_port)

    def notify_vnfm(self, listening_interface, containerID):
        self.client.notify_vnfm(listening_interface, containerID)

    def enforce_initial_configuration(self, config):
        print  ("enforcing initial configuration")
        print  (str(config))
        for key, face_list in config.iteritems():
            for face in face_list:
                prefix=key
                interface = " tcp://"+face
                str_command = "nfdc register "+prefix+interface
                subprocess.call(args=str_command, shell=True)
                print  ("installing rule"+str_command)
                time.sleep(2)

