#!/bin/bash

VNFM_HOST=$1
VNFM_PORT=$2
VNF_ID=$3
SV_MODE=${4:-NO_SV}

VNF_DIR=/doctor/vnf

VAR0="$(ifconfig | grep 10.10.0.)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
VNF_ADMIN_IP="${myarray0[0]}"

nfd-start &> /var/log/nfd_log
cd /root/mmt/mmt-probe/
sed -i -e "s/111/$VNF_ID/g" mmt.conf
./probe -c mmt.conf &
python restart_probe.py $VNFM_HOST $VNFM_PORT &
cd /root/mmt/mmt-security/
./mmt_sec_server -a 8080 -o 172.30.1.5:8080/doctor/api/report -s $VNFM_HOST:$VNFM_PORT/doctor/MMTenant/report -b $VNF_ID &

if [ "$SV_MODE" == "SV" ]; then
    cd /SV_ST/bin/ && ./SV &
fi

sleep 5

python $VNF_DIR/nfd_router_server.py $VNFM_HOST $VNFM_PORT "$VNF_ADMIN_IP" $HOSTNAME $SV_MODE $VNF_ID &
python /doctor/sv_rest_api.py $VNFM_HOST $VNFM_PORT &
sleep 5
python $VNF_DIR/nfd_restart.py $VNFM_HOST $VNFM_PORT &
tail -f /var/log/dmesg
