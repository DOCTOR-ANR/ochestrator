#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests_unixsocket
import urllib   
import pprint

def list_services():
    
    try:
        session = requests_unixsocket.Session()
        r = session.get('http+unix://'+urllib.quote_plus('/var/run/docker.sock')+'/v1.32/services')
        pprint.pprint(r.json())
    except Exception:
        print  ('error')
    return

def update_service():
    
    try:
        session = requests_unixsocket.Session()
        r1 = session.get('http+unix://'+urllib.quote_plus('/var/run/docker.sock')+'/v1.25/services/x3wldgbdq2n8')
        pprint.pprint(r1.json())
        service=r1.json()        
        data={
  'Name': service['Spec']['Name'],
  'TaskTemplate':service['Spec']['TaskTemplate'],
  'Mode': {u'Replicated': {u'Replicas': 3}},
  u'Endpoint': service['Endpoint'],
'Networks': service['Spec']['Networks']
}       
        print(json.dumps(data));
        headers = {}
        headers['Content-Type'] = 'application/json';
        r = session.post('http+unix://'+urllib.quote_plus('/var/run/docker.sock')+'/v1.25/services/'+str(service["ID"])+'/update?version='+str(service["Version"]["Index"]),json=data,headers=headers);
        pprint.pprint(r.json())
    except Exception:
        print  ('error')
    return

if __name__ == "__main__":
    #list_services()
    update_service()