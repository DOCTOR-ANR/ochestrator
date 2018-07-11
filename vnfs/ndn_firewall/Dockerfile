FROM maouadj/ndn_firewall_base_image
MAINTAINER Messaoud Aouadj
#new version of ndn firewall
RUN rm /home/NDN/ndnfirewall/ndn-firewall.cpp
RUN rm /home/NDN/ndnfirewall/bin/ndnfirewall
ADD ndn-firewall.cpp /home/NDN/ndnfirewall/
RUN cd /home/NDN/ndnfirewall && cmake . && make clean && make
#
RUN apt-get update
RUN apt-get install python-flask -y
RUN rm /run/nfd.sock; exit 0
ADD launch_ndn_firewall.sh /doctor/
RUN chmod u+x /doctor/launch_ndn_firewall.sh
ADD vnf/nfd_router_client.py /doctor/vnf/
ADD vnf/nfd_router_em.py /doctor/vnf/
ADD vnf/ndn_firewall_server.py /doctor/vnf/
ADD vnf/ndn_firewall_em.py /doctor/vnf/

