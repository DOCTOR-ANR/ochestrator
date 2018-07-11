#!/bin/bash

docker rmi maouadj/ndn_firewall:v1
docker build -t="maouadj/ndn_firewall:v1" .
