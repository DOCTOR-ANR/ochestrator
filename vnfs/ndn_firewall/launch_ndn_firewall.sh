#!/bin/bash

VNFM_HOST=$1
VNFM_PORT=$2
VNF_ID=$3

VNF_DIR=/doctor/vnf

#get admin_net interface's IP
VAR0="$(ifconfig | grep 10.10.0.)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
VNF_ADMIN_IP="${myarray0[0]}"

# start nfd module
nfd-start &
#> /var/log/nfd_log

#start firewall with IP address of the next nfd node
#cd /home/NDN/ndnfirewall/bin
#./ndnfirewall $NEXT_NFD &


#start MMT probe
#cd /root/mmt/mmt-probe/
#./probe -c mmt.conf &
#start MMT security with IP address and port of VNFM
#cd /root/mmt/mmt-security/
#./mmt_sec_server -a 8080 -o $VNFM_HOST:$VNFM_PORT/doctor/MMTenant/report -b $VNF_ID &

sleep 5
#start REST server
python $VNF_DIR/ndn_firewall_server.py $VNFM_HOST $VNFM_PORT "$VNF_ADMIN_IP" $HOSTNAME &
tail -f /var/log/dmesg
