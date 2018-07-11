import httplib
import json
import time
import pdb
import base64

class GenericClient(object):
    """
    Generic client for the orchestrator
    """
    def __init__(self,host,port,prefix, logger):
        """
            @param host   : ipAddr of the REST server
            @param port   : listening port of the REST server
            @param prefix : determines the type of the instruction
        """
        self.host = host
        self.port = port
        self.prefix = '/'+prefix+'/'
        self.logger = logger

    def send_request(self,method,action,data=None):
        """ sends requests through the httplib library """
        # initiate the connection
        conn = httplib.HTTPConnection(self.host, self.port, timeout=4)
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
                raise Exception
        except Exception:
            self.logger.debug("CLIENT : can't send request to:"+str(self.host))
            raise Exception


class NFVOClient(GenericClient):
    """ formats and sends requests to configure faces """

    def __init__(self,nfvo_host, nfvo_port, logger):
        GenericClient.__init__(self, nfvo_host,nfvo_port,"vnfm", logger)
        self.logger.debug("NFVO client UP")

    def get_VDUs_initial_configuration(self):
        configuration = None
        try:
            response = self.send_request('GET', 'faces/get_init_config')
            configuration = json.loads(response.read())
            self.logger.debug("reqsuest configuration sent to NFVO server")
        except Exception:
            self.logger.debug("can't get ue initial configuration")
        return configuration

    def notify_nfvo(self):
        while True:
            try:
                self.send_request('GET', 'notifications/vnfmUP')
                self.logger.debug("notification sent to NFVO")
                break
            except Exception:
                self.logger.debug("waiting for NFVO ...")
                time.sleep(2)

    def forward_cpa_alert(self, alert):
        while True:
            try:
                self.send_request('POST', 'notifications/CPA', alert)
                self.logger.debug("CPA alert forwarded to NFVO")
                break
            except Exception:
                self.logger.debug("waiting for NFVO to forward CPA alert...")
                time.sleep(2)

    def forward_pit_stats_in(self, alert):
        while True:
            try:
                self.send_request('POST', 'notifications/pit_stats_in', alert)
                self.logger.debug("pit stat forwarded to NFVO")
                break
            except Exception:
                self.logger.debug("waiting for NFVO to forward pit stat...")
                time.sleep(2)

    def forward_sv_report(self, report):
        while True:
            try:
                self.send_request('POST', 'sv/report', report)
                self.logger.debug("sv report forwarded to NFVO")
                break
            except Exception:
                self.logger.debug("waiting for NFVO to forward sv report...")
                time.sleep(2)

    def all_vnfs_up(self):
        try:
            with open("deploy_log","r") as f:
                encoded_string = base64.b64encode(f.read())
                self.send_request('POST', 'notifications/vnfsUP', encoded_string)
        except Exception:
            self.logger.debug("can not send notification to nfvo")

    def cpa_alert_tmp(self):
        alert1 = {u'timestamp': 1510088294, u'alert_id': 102, u'data': u'/http/content2', u'face_id': 0, u'probe_id': 2}
        alert2 = {u'timestamp': 1510088294, u'alert_id': 102, u'data': u'/http/content2 /http/content1', u'face_id': 0, u'probe_id': 2}
        try:
            self.send_request('POST', 'notifications/CPA', alert1)
            self.send_request('POST', 'notifications/CPA', alert2)
        except Exception:
            self.logger.debug("can not send notification to nfvo")

class VNFClient(GenericClient):
    """ formats and sends requests to configure faces """

    def __init__(self,vnf_host, vnf_port, logger):
        GenericClient.__init__(self, vnf_host,vnf_port,"vnfm", logger)
        self.logger.debug("VNF client UP")

    def send_vnf_initial_config(self, config):
        while True:
            try:
                self.logger.debug('sending initial configuration to: '+str(self.host))
                self.logger.debug('-----configuration: '+str(config))
                self.send_request('POST', 'init_configuration', config)
                self.logger.debug('initial config sent to VNF')
                break
            except Exception:
                self.logger.debug("can't send configuration to VNF ... retrying!")
        return

    def send_update_config(self, config):
        while True:
            try:
                self.logger.debug('sending configuration update to: '+str(self.host))
                self.logger.debug('-----configuration: '+str(config))
                self.send_request('POST', 'update_configuration', config)
                self.logger.debug('config update sent to VNF')
                break
            except Exception:
                self.logger.debug("can't send configuration to VNF ... retrying!")
        return

    def send_firewall_initial_config(self, config):
        while True:
            try:
                self.logger.debug('sending firewall initial configuration to: '+str(self.host))
                self.logger.debug('-----configuration: '+str(config))
                self.send_request('POST', 'firewall_initial_configuration', config)
                self.logger.debug('Firewall initial config sent to VNF')
                break
            except Exception:
                self.logger.debug("can't send firewall configuration to VNF ... retrying!")
        return

    def send_firewall_config(self, config):
        while True:
            try:
                self.logger.debug('sending new firewall configuration to: '+str(self.host))
                self.logger.debug('-----configuration: '+str(config))
                self.send_request('POST', 'update_configuration', config)
                self.logger.debug('Firewall config sent to VNF')
                break
            except Exception:
                self.logger.debug("can't send firewall configuration to VNF ... retrying!")
            return

    def send_update_faces(self, config):
        while True:
            try:
                self.logger.debug('sending faces update command to: '+str(self.host))
                self.logger.debug('-----faces configuration: '+str(config))
                self.send_request('POST', 'update_faces', config)
                self.logger.debug('faces updates config sent')
                break
            except Exception:
                self.logger.debug("can't send faces upates configuration to VNF ... retrying!")
            return

    def send_update_mode(self, mode):
        while True:
            try:
                self.logger.debug('sending update mode message: '+str(self.host))
                self.logger.debug('----- new mode: '+str(mode))
                self.send_request('POST', 'update_mode', mode)
                self.logger.debug('router update mode message sent')
                break
            except Exception:
                self.logger.debug("can't send router update mode message ... retrying!")
            return
