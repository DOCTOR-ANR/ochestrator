from vnfm_client import NFVOClient, VNFClient
from timeit import default_timer
import time
import pdb


class NFD_VNFM(object):

    def __init__(self, nfvo_host, nfvo_port, logger):
        self.logger = logger
        self.logger.debug("creating nfvo client with:")
        self.logger.debug("nfvo host : %s", nfvo_host)
        self.logger.debug("nfvo host : %s", nfvo_port)
        self.nfvo_client = NFVOClient(nfvo_host, nfvo_port, logger)
        self.vnf_clients = {}
        self.vnfs_configuration = None
        self.ready = False
        self.vnfs_counter = 0
        self.total_vnfs_to_configure = 0
        self.managed_vnfs = None

    def set_managed_vnfs_list(self, vnfs_id_list):
        self.managed_vnfs = vnfs_id_list
        self.logger.debug('managed vnfs: '+str(self.managed_vnfs))
        self.total_vnfs_to_configure = len(self.managed_vnfs)
        self.logger.debug('Total number of vnfs to be managed == '+str(self.total_vnfs_to_configure))




    def embed_vnfs_initial_configuration(self, config):
        """

        :param config:
        :return:
        """
        self.configuration = config
        self.vnfs_configuration = self.extract_sfc_configuration(config)
        self.firewall_configurations = {}
        self.firewall_configurations = self.extract_firewall_configuration(config)
        self.logger.debug("*************************")
        self.logger.debug("***********")
        self.logger.debug(str(self.firewall_configurations))
        self.logger.debug("***********")
        self.logger.debug("*************************")

        if self.total_vnfs_to_configure == self.vnfs_counter:
            self.send_firewall_initial_configuration()
            self.logger('all VNFs to configure are ready')
            self.send_vnfs_initial_configuration()
            self.nfvo_client.all_vnfs_up()
            #self.nfvo_client.cpa_alert_tmp()
        return

    def send_vnfs_initial_configuration(self):
        """

        :return:
        """
        for router_ID in self.vnfs_configuration.keys():
            self.logger.debug('sending initial configuration to: '+str(router_ID))
            config = self.get_vnf_init_config(router_ID)
            if config is not None:
                self.vnf_clients[router_ID].send_vnf_initial_config(config)
        return

    def send_firewall_initial_configuration(self):
        """

        :return:
        """
        for firewall_ID in self.firewall_configurations.keys():
            self.logger.debug('sending firewall initial configuration to: '+str(firewall_ID))
            config = self.firewall_configurations[firewall_ID]
            if config is not None:
                self.vnf_clients[firewall_ID].send_firewall_initial_config(config)
        return

    def update_firewall_config(self, firewall_id, config, mode="append-drop"):
        if mode == 'append-drop':
            self.vnf_clients[firewall_id].send_firewall_config(config)

    def handle_RouterJoin(self, router_ID, listening_interface, listening_port):
        """

        :param router_ID:
        :param listening_interface:
        :param listening_port:
        :return:
        """
	deploy_log = open("deploy_log","a") 
        if not (router_ID in self.vnf_clients.keys()):
            self.vnf_clients[router_ID] = VNFClient(listening_interface, listening_port, self.logger)
            self.logger.debug("client for vnf: %s - interface: %s (created)", str(router_ID),str(listening_interface))
            self.vnfs_counter+=1
            self.logger.debug('vnfs_counter =='+str(self.vnfs_counter))
	    ts = time.time()
            deploy_log.write(str(ts)+":"+str(router_ID)+"\n")
	    if self.vnfs_counter == self.total_vnfs_to_configure and \
                            self.vnfs_configuration is not None:
		self.logger.debug("all vnfs to configure are ready!")
                self.send_firewall_initial_configuration()
                self.send_vnfs_initial_configuration()
                self.nfvo_client.all_vnfs_up()
                #self.nfvo_client.cpa_alert_tmp()
            elif self.vnfs_counter > self.total_vnfs_to_configure:
                self.logger.debug('routerIn event after vnfs configuration')
        return


    def get_vnf_init_config(self, containerID):
        """

        :param containerID:
        :return:
        """
        try:
            config = self.vnfs_configuration[containerID]
            return config
        except Exception,e:
            self.logger.debug('can not get config: '+ str(e))
            return

    def extract_sfc_configuration(self, configurations):
        """

        :param configurations:
        :return:
        """
        routers_configs = {}
        for router_ID in configurations.keys():
            routers_configs[router_ID] = {}
            for key, value in configurations[router_ID].iteritems():
                if key != "firewall":
                    routers_configs[router_ID][key] = value
        return routers_configs

    def extract_firewall_configuration(self, configurations):
        """

        :param configurations:
        :return:
        """
        fw_configs = {}
        for router_ID in configurations:
            for key, value in configurations[router_ID].iteritems():
                if key == "firewall":
                    fw_configs[router_ID] = value
        return fw_configs

    def update_service(self, container_down, ingress_configs, replicas_config):

        # delete old service client
        if len(container_down) > 0:
         for vnf_id, config in replicas_config.iteritems():
            while True:
                try:
		    config['ingress']=ingress_configs
		    config['container_down']=container_down
                    self.vnf_clients[vnf_id].send_vnf_initial_config(config)
                    break
                except KeyError:
                    self.logger.debug('vnf client for container {0} not ready yet'.format(vnf_id))
                    #time.sleep(0.500)
        else:
		for ingress_vnf, update in ingress_configs.iteritems():
        	    self.vnf_clients[ingress_vnf].send_update_config(update)
	
		#if len(container_down) > 0:
        	#    del self.vnf_clients[container_down]

    def update_service_prefix(self, ingress_configs):

        for ingress_vnf, update in ingress_configs.iteritems():
            self.vnf_clients[ingress_vnf].send_update_config(update)

    def finish_scale_out(self, container_down, ingress_configs, replicas_config):
        self.logger.debug('finish scale out')
	    # delete old service client
        for ingress_vnf, update in ingress_configs.iteritems():
            self.vnf_clients[ingress_vnf].send_update_config(update)
        #if len(container_down) > 0:
        #    del self.vnf_clients[container_down]
