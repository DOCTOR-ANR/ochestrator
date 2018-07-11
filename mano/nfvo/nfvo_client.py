import httplib
import json
import pdb
import time

class GenericClient(object):
    """
    Generic client for the orchestrator
    """
    def __init__(self,logger, host,port,prefix):
        """
            @param host   : ipAddr of the REST server
            @param port   : listening port of the REST server
            @param prefix : determines the type of the instruction
        """
        self.logger = logger
        self.host = host
        self.port = port
        self.prefix = '/'+prefix+'/'

    def send_request(self,method,action,data=None):
        """ sends requests through the httplib library """
        # initiate the connection
        conn = httplib.HTTPConnection(self.host, self.port, timeout=3)
        url = self.prefix + action
        header = {}
        # there is data to send
        if data is not None:
            # encode it in json format
            data = json.dumps(data)
            header['Content-Type'] = 'application/json'
        try:
            # send the request and get the response
            conn.request(method,url,data,header)
            res = conn.getresponse()
            if res.status in (httplib.OK,
                              httplib.CREATED,
                              httplib.ACCEPTED,
                              httplib.NO_CONTENT):
                return res
            else:
                print res.status
                raise Exception
        except Exception:
            raise Exception

class VNFMClient(GenericClient):

    def __init__(self,logger, vnfm_host, vnfm_port):
        GenericClient.__init__(self, logger, vnfm_host, vnfm_port, "nfvo")

    def notify_vnfm(self):
        while True:
            try:
                self.send_request('GET', 'notifications/nfvoUP')
                print  ('NFVO UP notification sent to VNFM')
                break
            except Exception:
                print  ('waiting for vnfm ...')
                time.sleep(1)
        return

    def send_VDUs_configs_to_vnfm(self, configurations):
        try:
            self.send_request('POST', 'faces/configuration', configurations)
            print  ('vnfs initial configuration sent to VNFM')
        except Exception:
            print  ("can't send vnfs initial configuration to VNFM")
        return

    def update_firewall(self, firewall_vdu_id, prefix_list, mode):
        try:
            new_configuration = {'vdu_id':firewall_vdu_id,
                                 'prefix_list':prefix_list,
                                 'mode':mode}
            self.send_request('POST', 'firewall/update', new_configuration)
            print  ('firewall new configuration sent to VNFM')
        except Exception:
            print  ("can't send firewall new configuration to VNFM")
        return

    def send_scaled_service_config(self, configuration):
        try:
            self.send_request('POST', 'update_service', configuration)
            #print  ('scaled service configuration sent to VNFM')
        except Exception:
            print  ("can't send scaled service configuration to VNFM")
        return

    def send_update_faces(self, router_id, faces):
        data = {'router_id':router_id, 'faces':faces}
        try:
            self.send_request('POST', 'update_faces', data)
            print  ('faces new configuration sent to VNFM')
        except Exception:
            print  ("can't send faces new configuration to VNFM")
        return

    def send_update_router_mode(self, target_router_mode):
        try:
            self.send_request('POST', 'update_router_mode', target_router_mode)
            print  ('update router mode cmd sent to VNFM')
        except Exception:
            print  ("can't send router mode update notif to VNFM")
        return