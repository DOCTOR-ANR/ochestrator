#!/bin/bash


CONTAINER_ID="$(docker ps -aqf 'name=VDU9')"
echo "${CONTAINER_ID}"

docker exec "$CONTAINER_ID" nfdc strategy set /com/google /localhost/nfd/strategy/round-robin/%FD%01

VAR0="$(docker exec ${CONTAINER_ID} ifconfig | grep 172.18.0)"
IFS=':' read -a myarray0 <<< "$VAR0"
IFS=' ' read -a myarray0 <<< "${myarray0[1]}"
R1_IP="${myarray0[0]}"
echo "${R1_IP}"


sleep 3
java -jar NewProducer_oldlib.jar -g 4000 -1 10000 3600 good_provider_normal.log "$R1_IP" /com/google 100 0 &
sleep 3
java -jar NewProducer_oldlib.jar -g 4000 -1 10000 3600 good_provider_normal.log "$R1_IP" /com/google 100 0 &
sleep 3
java -jar NewProducer_oldlib.jar -g 4000 -1 10000 3600 good_provider_normal.log "$R1_IP" /com/google 100 0 &
sleep 2
java -jar NewProducer_oldlib.jar -g 4000 -1 10000 3600 good_provider_normal.log "$R1_IP" /com/google 100 0 &
sleep 2
java -jar NewProducer_oldlib.jar -g 4000 -1 10000 3600 good_provider_normal.log "$R1_IP" /com/google 100 0 &

#java -jar oldProducer_remake.jar -g 4000 -1 10000 3600000 good_provider_normal.log "$R1_IP"
