#!/bin/bash

docker rmi maouadj/egress_gateway:v1
docker build -t="maouadj/egress_gateway:v1" .
