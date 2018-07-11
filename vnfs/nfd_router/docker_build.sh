#!/bin/bash

docker rmi maouadj/ndn_router:v2
docker build -t="maouadj/ndn_router:v2" .
