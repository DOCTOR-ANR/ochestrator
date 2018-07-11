#!/bin/bash

NFVO_HOST=$1
NFVO_PORT=$2
VNFM_PORT=$3
VNFM_DIR=/doctor/vnfm


VAR0="$(ifconfig eth0 | grep inet)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
VNFM_OVERLAY_IP="${myarray0[0]}"

VAR1="$(ifconfig eth1 | grep inet)"
IFS=':' read -a myarray1 <<< "$VAR1"
IFS=' ' read -a myarray1 <<< "${myarray1[1]}"
VNFM_BRIDGE_IP="${myarray1[0]}"

echo "Starting doctor virtual network function manager ....... "
python $VNFM_DIR/vnfm_server.py $NFVO_HOST $NFVO_PORT "$VNFM_BRIDGE_IP" "$VNFM_OVERLAY_IP" $VNFM_PORT &
tail -f /var/log/dmesg
