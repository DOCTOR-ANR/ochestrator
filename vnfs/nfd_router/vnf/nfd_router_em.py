from nfd_router_client import RouterClient
from subprocess import check_output
import subprocess
import time
import socket
import json

class RouterEM(object):

    def __init__(self, logger, vnfm_host, vnfm_port, sv_mode, probe_id):
        self.mode = 'no_SV'
        self.probe_id = probe_id
        self.logger = logger
        self.vnfm_host = vnfm_host
        self.vnfm_port = vnfm_port
        self.logger.debug("creating vnf client with: %s, %s", vnfm_host, vnfm_port)
        self.client = RouterClient(logger, vnfm_host, vnfm_port)
        self.update_mode(sv_mode)

    def notify_vnfm(self, listening_interface, containerID):
        self.client.notify_vnfm(listening_interface, containerID)

    def enforce_initial_configuration(self, config):
	time.sleep(10)
        self.logger.debug("enforcing initial configuration")
        cf={}
	if(config.get('ingress','null')!='null'):
		cf['ingress_configurations']=config['ingress']
        	cf['container_down']=config['container_down']
        	cf['replicas_configurations']=''
		del config['ingress']
        	del config['container_down']
	cf['to_add']=config
	cf['strategy']='multicast'
	with open('/root/nfd_conf', 'a') as outfile:
                json.dump(cf, outfile)
		outfile.write('\n')
	self.logger.debug(str(config))
        for key, face_list in config.iteritems():
            for face in face_list:
                prefix=key
                interface = " tcp://"+face
                str_command = "nfdc register "+prefix+interface
                subprocess.call(args=str_command, shell=True)
                self.logger.debug("installing rule"+str_command)
                time.sleep(1)
            strategy_command = "nfdc strategy set {0} /localhost/nfd/strategy/multicast/%FD%03".format(key)
            subprocess.call(args=strategy_command, shell=True)
            self.logger.debug("changing strategy to multicast")

    def update_configuration(self, new_config):
        # config == {"prefix":[list_of_ip_addr_in_string]}
	cf=new_config
        cf['strategy']='round'
        self.logger.debug("updating configuration")
	with open('/root/nfd_conf', 'a') as outfile:
                json.dump(cf, outfile)
		outfile.write('\n')
        self.logger.debug(str(new_config))
        new_rules = new_config['to_add']
        for key, face_list in new_rules.iteritems():
            prefix =key
            for face in face_list:
                interface = " tcp://"+face
                str_command = "nfdc register "+prefix+interface
		ping_command = "ping -c 5 "+face.split(':')[0]
                subprocess.call(args=ping_command, shell=True)
		subprocess.call(args=str_command, shell=True)
		self.logger.debug("installing rule "+str_command)
                time.sleep(2)
            strategy_command = "nfdc strategy set {0} /localhost/nfd/strategy/round-robin/%FD%01".format(prefix)
            subprocess.call(args=strategy_command, shell=True)
            self.logger.debug("changing strategy to :"+strategy_command)

    def register_face(self, prefix, remote_face):
        self.logger.debug('registring face')
        self.logger.debug('prefix: {0} -- remote_face: {1}'.format(prefix, remote_face))
        cmd = 'nfdc register {0} tcp://{1}'.format(prefix, remote_face)
        subprocess.call(args=cmd, shell=True)
        self.logger.debug('face registred')

    def unregister_face(self, prefix, deprecated_face):

        self.logger.debug('unregistring faces')
        self.logger.debug('prefix: {0} -- face: {1}'.format(prefix, deprecated_face))

        out = check_output('nfd-status')
        faceid_list = [face for face in out.split('\n') if face.startswith('  faceid=')]

        for face in faceid_list:
            values = [value for value in face.split(' ') if value != '']
            if values[0].split('=')[0] == 'faceid':
                faceid = values[0].split('=')[1]
            if values[1].split('=')[0] == 'remote':
                remote_face = values[1].split('://')[1]
                if remote_face == deprecated_face:
                    self.logger.debug('remote_face == '+remote_face)
                    self.logger.debug('deprecated_face == '+deprecated_face)
                    cmd = "nfdc unregister "+prefix+' '+faceid
                    subprocess.call(args=cmd, shell=True)
                    self.logger.debug("command executed : "+cmd)
                    break


    def update_mode(self, mode):
        if mode == 'SV' and self.mode == "no_SV":
            cmd = 'cd /SV_ST/bin/ && ./SV &'
            subprocess.call(args=cmd, shell=True)

            self.mode = mode
            self.logger.debug("changing mode to SV")

#            {"action":"edit", "drop":True, "address":"127.0.0.1", "port":9999, "report_each":5}

            sv_configuration = {"action":"edit",
                                "name":str(self.probe_id),
                                "drop":True,
                                "address":"127.0.0.1",
                                "port": 9999,
                                "report_each":5
                                }

            time.sleep(2)

            json_config = json.dumps(sv_configuration)

            UDP_IP = "127.0.0.1"
            UDP_PORT = 10000
            COMMAND = json_config

            self.logger.debug("UDP target IP: "+UDP_IP)
            self.logger.debug("UDP target port: "+str(UDP_PORT))
            self.logger.debug("message: "+COMMAND)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(COMMAND, (UDP_IP, UDP_PORT))
