from nfd_router_client import RouterClient
import subprocess
import time
import socket
import json

class FirewallEM(object):

    def __init__(self, logger, vnfm_host, vnfm_port):
        #TODO: keep trace of configuration
        self.configuration = {"append-drop":[]}
        self.logger = logger
        print  ("creating vnf client with: %s, %s", vnfm_host, vnfm_port)

    def enforce_initial_configuration(self, config):
        print  ("enforcing firewall initial configuration")
        print  (str(config))
        str_command = "/home/NDN/ndnfirewall/bin/ndnfirewall "+config["next_router"]+" &"
        subprocess.call(args=str_command, shell=True)
        time.sleep(2)


        configuration = {}
        configuration["post"] = {}
        configuration["post"]["mode"] = [config["firewall_rules"]["mode"]]
        firewall_rules = config["firewall_rules"]["rules"]
        if len(firewall_rules) > 0:
            for rule in firewall_rules:
                configuration["post"][rule["action"]] = rule["prefix"]

            json_config = json.dumps(configuration)

            UDP_IP = "127.0.0.1"
            UDP_PORT = 6362
            COMMAND = json_config

            print  ("UDP target IP: "+UDP_IP)
            print  ("UDP target port: "+str(UDP_PORT))
            print  ("message: "+str(COMMAND))

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(COMMAND, (UDP_IP, UDP_PORT))

    def update_configuration(self, new_configuration):

        #print  ("*** enforcing firewall new configuration ***")
        configuration = {}
        configuration["post"] = {}
        configuration["post"]["append-drop"] = new_configuration
        print  (configuration)
        json_config = json.dumps(configuration)
        UDP_IP = "127.0.0.1"
        UDP_PORT = 6362
        COMMAND = json_config
        #print  ("UDP target IP: "+UDP_IP)
        #print  ("UDP target port: "+str(UDP_PORT))
        #print  ("message: "+str(COMMAND))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(COMMAND, (UDP_IP, UDP_PORT))
