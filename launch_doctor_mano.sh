#!/bin/bash

# Usage
#-------
if [ $# -ne 2 ]
then
    echo Usage: $0 tosca_template nfvo_host:nfvo_port
    exit 1
fi


TOSCA_FILE_PATH=$1
NFVO_HOST_PORT=$2
NFVO_DIR=/home/maouadj/mano_v3/mano/nfvo
pkill node
pkill npm
source ~/.nvm/nvm.sh
nvm use v9.8.0
cd /home/maouadj/operator/mmt-operator/www
npm start &> log_ope &
cd ../../../mano_v3
echo "Starting doctor MANO ... "
echo "Starting doctor Orchestrator ... "
rm deploy_log
python $NFVO_DIR/nfvo_server.py $TOSCA_FILE_PATH $NFVO_HOST_PORT
