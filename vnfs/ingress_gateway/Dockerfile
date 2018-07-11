FROM maouadj/ingress_gw_base_image:latest
MAINTAINER Messaoud Aouadj
RUN apt-get install python-flask -y
# ******* Montimage *******
RUN mkdir /root/pgmpy
RUN git clone https://github.com/pgmpy/pgmpy /root/pgmpy
RUN pip install -r /root/pgmpy/requirements.txt
RUN pip install pgmpy
RUN pip install pandas
RUN rm -r /root/mmt
ADD mmt /root/mmt
#########################
RUN rm /run/nfd.sock; exit 0
ADD launch_ingress_gateway.sh /doctor/
RUN chmod u+x /doctor/launch_ingress_gateway.sh
ADD vnf/ingress_gateway_client.py /doctor/vnf/
ADD vnf/ingress_gateway_server.py /doctor/vnf/
ADD vnf/ingress_gateway_em.py /doctor/vnf/
