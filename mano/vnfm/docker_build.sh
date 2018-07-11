#!/bin/bash

docker rmi maouadj/ndn_virtual_manager:v1
docker build -t="maouadj/ndn_virtual_manager:v1" .
