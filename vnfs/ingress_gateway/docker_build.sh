#!/bin/bash

docker rmi maouadj/ingress_gateway:v1
docker build -t="maouadj/ingress_gateway:v1" .
