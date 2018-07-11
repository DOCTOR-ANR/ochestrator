FROM maouadj/ndn_router_base_image
MAINTAINER Messaoud Aouadj
# ******* Round Robin Strategy ******
ADD strategy/rr-strategy.cpp /NFD/daemon/fw/
ADD strategy/rr-strategy.hpp /NFD/daemon/fw/
RUN cd /NFD && ./waf configure
RUN cd /NFD && ./waf
RUN cd /NFD && ./waf install
#####################################

# ******* signature verfication module ******
ADD SV_ST /SV_ST
RUN cd /SV_ST && cmake . && make
#####################################

RUN apt-get install python-flask -y
RUN apt-get install netcat -y
RUN apt-get install vim -y
RUN apt-get install tcpdump -y

# ******* Montimage *******
RUN mkdir /root/pgmpy
RUN git clone https://github.com/pgmpy/pgmpy /root/pgmpy
RUN pip install -r /root/pgmpy/requirements.txt
RUN pip install pgmpy
RUN pip install pandas
RUN rm -r /root/mmt
ADD mmt /root/mmt
ADD vnf/nfd_restart.py /doctor/vnf/
ADD nfd_conf /root/
#########################

RUN rm /run/nfd.sock; exit 0
ADD launch_nfd_router.sh /doctor/
RUN chmod u+x /doctor/launch_nfd_router.sh
ADD vnf/nfd_router_client.py /doctor/vnf/
ADD vnf/nfd_router_server.py /doctor/vnf/
ADD vnf/nfd_router_em.py /doctor/vnf/
# main file for SV_api
ADD sv_rest_api.py /doctor/
