import httplib
import json
import time
import pdb

class GenericClient(object):
    """
    Generic client for the orchestrator
    """
    def __init__(self, logger, host,port,prefix):
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
        conn = httplib.HTTPConnection(self.host, self.port, timeout=5)
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
            print  ("can't send request")
            raise Exception


class IngressGatewayClient(GenericClient):
    """ formats and sends requests to configure faces """

    def __init__(self, logger, vnfm_host, vnfm_port=3999 ):
        GenericClient.__init__(self, logger, vnfm_host,vnfm_port,"iGW")
        print  ("ingress gateway client UP")


    def notify_vnfm(self, listening_interface, containerID):
        while True:
            try:

                config = {"container":containerID,
                        "listening_interface":listening_interface,
                        "listening_port":4999}
                self.send_request('POST', 'notifications/iGW_UP', config)
                print  ("notification sent to vnfm")
                break
            except Exception:
                print  ("waiting for vnfm ...")
                time.sleep(1)

