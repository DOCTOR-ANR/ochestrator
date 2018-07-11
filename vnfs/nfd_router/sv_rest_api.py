import socket
import sys
import httplib

vnfm_host = sys.argv[1]
vnfm_port = sys.argv[2]

udp_address = ('127.0.0.1', 9999)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(udp_address)

connection = httplib.HTTPConnection(vnfm_host, vnfm_port)

while True:
    data, address = udp_socket.recvfrom(65536)
    connection.request('POST', '/sv/report', data, {'content-type': 'application/json'})
    response = connection.getresponse()
