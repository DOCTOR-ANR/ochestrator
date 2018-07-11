import socket
import json

sv_configuration = {"action":"edit",
                    "drop":True,
                    "address":"10.10.1.107",
                    "port":399,
                    "report_each":5}

json_config = json.dumps(sv_configuration)

UDP_IP = "127.0.0.1"
UDP_PORT = 10000
COMMAND = json_config

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(COMMAND, (UDP_IP, UDP_PORT))

