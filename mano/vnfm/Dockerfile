FROM maouadj/vnfm_base_image:latest
MAINTAINER Messaoud Aouadj
ADD launch_vnfm.sh /doctor/
RUN chmod u+x /doctor/launch_vnfm.sh
ADD vnf/vnfm_client.py /doctor/vnfm/
ADD vnf/vnfm_server.py /doctor/vnfm/
ADD vnf/nfd_vnfm.py /doctor/vnfm/
