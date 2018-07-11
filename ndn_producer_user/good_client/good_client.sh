#!/bin/bash

RATE=$1
LOG_FILE=$2

CONTAINER_ID="$(docker ps -aqf 'name=VDU1')"
echo "${CONTAINER_ID}"
VAR0="$(docker exec ${CONTAINER_ID} ifconfig | grep 172.18.0)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
R1_IP="${myarray0[0]}"
echo "${R1_IP}"

#java -jar NewUser_oldlib.jar -g 180 4000 $RATE 100 "$R1_IP" 10000 /com/google $LOG_FILE 1 5
java -jar oldUser_remake.jar -g 600000 4000 $RATE -1 -1 "$R1_IP" 1000000 $LOG_FILE
