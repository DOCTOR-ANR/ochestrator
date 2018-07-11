#!/bin/bash

RATE=$1

CONTAINER_ID="$(docker ps -aqf 'name=VDU1')"
echo "${CONTAINER_ID}"
VAR0="$(docker exec ${CONTAINER_ID} ifconfig | grep 172.18.0)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
R1_IP="${myarray0[0]}"
echo "${R1_IP}"

#java -jar newUser.jar -a 180 4000 $RATE 100 "$R1_IP" 100 /com/google log_bad_client.log 1 10
java -jar oldUser_remake.jar -a 600000 4000 $RATE -1 -1  "$R1_IP" 1000000 10000 0 
