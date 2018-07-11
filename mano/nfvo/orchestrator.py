
from repositories.nfv_instances import CpdInstance, VDUInstance, \
    VNFInstance, NFVInstances, VirtualLinkInstance
from drivers.vim.docker_driver import InfrastructureManager
#from catalogs.vnf_catalog import VNFCatalog
from nfvo_client import VNFMClient
from policy import ScalingPolicy, UpdateFirewallPolicy, SignatureVerPolicy
import sys

import os
import pdb
import copy
import time
from ipaddress import IPv4Address, IPv4Network

import docker
import pprint
client = docker.from_env()

#TODO: placement for VNFM

from toscaparser.tosca_template import ToscaTemplate

class Orchestrator(object):

    def __init__(self, logger, nfvo_host, nfvo_port, vnfm_port='3999'):
        self.logger = logger
        self.policies = []
        self.sv_routers = []
        self.service_args = {}
        self.initial_deployment_template = None
        self.scaled_services_configuration = {}
        self.configuration_node_mode = {}
        vnfm_host = self.initialize_nfvi(nfvo_host, nfvo_port, vnfm_port)
        self.nfvi_instances = NFVInstances()
        self.vnfm_client = VNFMClient(logger, vnfm_host["vnfm_bridge_ip"], vnfm_port)
        self.vnfm_overlay = {'ip':vnfm_host['vnfm_overlay_ip'],
                             'port':'4999'}

    def deploy_vnfm(self, nfvo_host, nfvo_port, vnfm_port):
        # lui passer host and port du nfvo pour lancer le serveur
        self.vim.deploy_VDU(name="vnfm",
                            sw_image="maouadj/ndn_virtual_manager:v1",
                            networks=['admin_net'],
                            placement_policy=["popLocation==france"],
                            app="/doctor/launch_vnfm.sh",
                            arguments=[nfvo_host, nfvo_port, vnfm_port])

        #VNFM service has only one task (i.e., vdu)
        vnfm = self.vim.get_vdu('vnfm')[0]
        vnfm_bridge_ip = None
        for indx, val in enumerate(client.networks.list()):
            if val.name == u'docker_gwbridge':
                while True:
                    network = client.networks.list()[indx]
                    try:
                        vnfm_bridge_ip = (network.attrs[u'Containers'][vnfm.id][u'IPv4Address']).split("/")[0]
                        break
                    except KeyError:
                        time.sleep(.500)
                        network = client.networks.list()[indx]
                        print "docker API not available yet!"

        vnfm_host = {"vnfm_bridge_ip":vnfm_bridge_ip,
                     "vnfm_overlay_ip":vnfm.network_addresses[0].split("/")[0]}
        """

        vnfm_host = {"vnfm_bridge_ip":"0.0.0.0",
                     "vnfm_overlay_ip":vnfm.network_addresses[0].split("/")[0]}
        """

        return vnfm_host

    def initialize_nfvi(self, nfvo_host, nfvo_port, vnfm_port):
        """"""
        #TODO: swarm, manager and worker nodes, docker_gwbridge
        # or should be done at the VIM level ?
        self.vim = InfrastructureManager()
        self.vim.create_admin_net()
        vnfm_host = self.deploy_vnfm(nfvo_host, nfvo_port, vnfm_port)
        return vnfm_host


    def parse_tosca(self, path):
        """
        parse a yaml file and return a tosca template object
        :param path: A string:  path to the yaml file
        :return: tosca object (tosca-parser)
        """
        tosca_template = ToscaTemplate(path)
        return tosca_template

    def onboard_vnffg(self, vnffg_path):
        vnffgd = self.parse_tosca()
        return
        #put it in catalogue

    def onboard_ns(self, ns_path):
        nsd = self.parse_tosca(ns_path)
        #put it in catalogue
        #we can only deploy a service
        #I  need a function to deploy a service
        return

    def onboard_vnf(self, vnf_path):
        """comment"""
        #TODO: use a catalog
        vnfd = self.parse_tosca(vnf_path)
        self.deploy_vnfd(vnfd)
        return

    def create_cpd_instance(self, name, cpd_address, vdu_instance, vl_instance):
        """
        create a connexion point instance and add it to nfvi_instance repository
        :param name: string: instance name
        :param cpd_address:  connexion point ip address
        :param vdu_instance: connexion point vitual binding
        :param vl_instance: connexion point vityal link
        :return: connexion point instance
        """
        cpd_instance = CpdInstance(name, cpd_address, vdu_instance, vl_instance)
        self.nfvi_instances.append_connextion_point(cpd_instance)
        return cpd_instance

    def create_vnf_instance(self, graph, vnf_name):
        """
        create a vdu instance, the a vnf instance
        :param graph: topology graph object to get information about vnf node relations
        :param vnf_name: A sting, vnf name
        :return: vnf instance
        """
        vdu_name = graph.vertex(vnf_name).requirements[0]['VDU']
        print '>>>>DEPLOY VDU '+str(vdu_name)
        print '>>>>DEPLOY VNF '+str(vnf_name)
        ts = time.time()
        deploy_log = open("deploy_log", "a")         
	vdu_instance = self.create_vdu_instance(graph, vdu_name)
        vnf_instance = VNFInstance(vnf_name, vdu_instance)
        deploy_log.write(str(ts)+":"+str(vdu_instance._infra_id[0:12])+"\n")
        return vnf_instance

    def create_vdu_instance(self, graph, vdu_name):
        """
        create VDU instance, then the connexion points
        :param graph:
        :param vdu_name:
        :return:
        """

        def create_vdu_connection_points(graph, vdu_instance):
            connexion_points = []
            virtual_link = None
            virtual_binding = None
            for key, node in graph.vertices.iteritems():
                if node.type == 'tosca.nodes.nfv.doctor.Cpd':
                    connexion_points.append(node)

            for connexion in connexion_points:
                for req in connexion.requirements:
                    if "virtual_binding" in req:
                        virtual_binding = req["virtual_binding"]
                    elif "virtual_link" in req:
                        virtual_link = req["virtual_link"]

                if virtual_binding ==  vdu_instance.name:
                    vl_instance = self.create_virtual_link_instance(virtual_link)
		    print '>>>>DEPLOY VL_CP '+str(connexion.name)
                    cpd_net_address = None
                    for address in vdu_instance.l3addresses:
                        if IPv4Address(address.split('/')[0]) in IPv4Network(vl_instance.subnet):
                            cpd_net_address = address.split('/')[0]
                    cpd_instance = self.create_cpd_instance(connexion.name,
                                                            cpd_net_address,
                                                            vdu_instance,
                                                            vl_instance)

        # at starting, each service has only one task(i.e., vdu)
        deployed_vdu = self.vim.get_vdu(vdu_name)[0]
        vdu_instance = VDUInstance(vdu_name,
                                   deployed_vdu.id,
                                   deployed_vdu.sw_image,
                                   deployed_vdu.network_addresses)
        create_vdu_connection_points(graph, vdu_instance)
        self.nfvi_instances.append_vdu(vdu_instance)
        return vdu_instance

    def create_virtual_link_instance(self, name):
        config = self.vim.get_network_config(name)
        network_instance = VirtualLinkInstance(name,
                                               config['Subnet'],
                                               config['Gateway'])
        self.nfvi_instances.append_virtual_link(network_instance)
        return network_instance


    def create_vnffg_instance(self):
        pass

    def create_ns_instance(self):
        pass

    def setup_policies(self, tosca_policies):
        for policy in tosca_policies:
            if policy.type == "tosca.policies.nfv.doctor.security.signature_verification":
                self.policies.append(SignatureVerPolicy(policy.type, policy.targets, policy.triggers))
            elif policy.type == 'tosca.policies.nfv.doctor.ndn.security.update_firewall':
                self.policies.append(UpdateFirewallPolicy(policy.type, policy.targets, policy.triggers))
            elif policy.type == "tosca.policies.nfv.doctor.ndn.scaling":
                self.policies.append(ScalingPolicy(self.apply_scaling_policy, policy.type, policy.targets, policy.triggers))
            else:
                sys.exit("no matching policy")

    def get_vnf_from_id(self, id):
        """
        return VNF name that correspond to ID
        :param id: VNF's ID
        :return:
        """
        for vnf in self.VNFs:
            if id == int(vnf.get_property_value("id")):
                return vnf.name
        raise ValueError("no VNF corresponding to probe_id")


    def handle_sv_report(self, report):

        # fill to install
        prefix_parts = report['invalid_signature_packet_name'].split('/')
        prefix = '/'
        for idx in range(1, len(prefix_parts)-1, 1):
            prefix += prefix_parts[idx]+'/'
        to_install = [prefix[:-1]]
	
        vnf = self.get_vnf_from_id(report['probe_id'])
        #pprint.pprint(vnf)
	#pprint.pprint(report)
	for policy in self.policies:
            if policy.type == 'tosca.policies.nfv.doctor.ndn.security.update_firewall':
                action = policy.evaluate(vnf)
                if action is not None:
                    target_firewall = action['target_firewall']
                    firewall_vdu_id = self.nfvi_instances.get_vnf_instance(target_firewall).VDU.infra_id
                    firewall_vdu_id = firewall_vdu_id[0:12]
                    print('\x1b[6;30;42m' +'content to be blocked {0} on firewall {1}: '.format(to_install[0], target_firewall)+ '\x1b[0m')
                    if to_install:
                        self.vnfm_client.update_firewall(firewall_vdu_id, to_install, "append-drop")

    # def apply_firewall_policy(self, alert):
    #     """
    #
    #     :param alert: format: dict -> {u'timestamp': 1510069035, u'alert_id': 102, u'data': u'/http/content1 ', u'face_id': 0, u'probe_id': 4}
    #     :return:
    #     """
    #
    #     vnf = self.get_vnf_from_id(alert["probe_id"])
    #     data = alert["data"].split(" ")
    #     data = [prefix for prefix in data if not (prefix=="" or prefix==" ")]
    #     timestamp = alert["timestamp"]
    #     cpa = {"vnf":vnf, "data":data, "timestamp":timestamp}
    #
    #     action = None
    #     for policy in self.policies:
    #         if policy.type == "tosca.policies.nfv.doctor.ndn.security":
    #             if vnf in policy.get_targets():
    #                 action = policy.record_cpa_alert(cpa)
    #                 if action is not None:
    #                     # ACTION : assumption: one firewall per action!!!
    #                     #TODO: consider more then one firewall per action
    #                     self.update_firewall_configuration(action)
    #
    # def update_firewall_configuration(self, new_configuration):
    #     target_firewall = new_configuration[0]["firewall"]
    #     firewall_vdu_id = self.nfvi_instances.get_vnf_instance(target_firewall).VDU.infra_id
    #     firewall_vdu_id = firewall_vdu_id[0:12]
    #     init_dropped_prefix_list = []
    #     old_configuration = self.configurations[firewall_vdu_id]['firewall']['firewall_rules']['rules']
    #     for rule in old_configuration:
    #         if rule['action'] == 'append-drop':
    #             init_dropped_prefix_list.extend(rule['prefix'])
    #     new_dropped_prefix_list = new_configuration[1]
    #     to_install = []
    #     for new_prefix in new_dropped_prefix_list:
    #         if not (new_prefix in init_dropped_prefix_list):
    #             print "on node id {}, new prefix to be blocked {}".format(firewall_vdu_id, new_prefix)
    #             for rule in old_configuration:
    #                 if rule['action'] == 'append-drop':
    #                     rule['prefix'].append(new_prefix)
    #             to_install.append(new_prefix)
    #     if to_install:
    #         # if the list is not empty
    #         self.vnfm_client.update_firewall(firewall_vdu_id, to_install, "append-drop")


    def get_vdu_vnfs(self, vdu, vnfs):
        """
        return VNFs deployed over a target VDU
        :param vdu: target VDU
        :param vnfs: list of all vnfs
        :return: list of vnfs
        """
        vdu_vnfs = []
        for vnf in vnfs:
            for req in vnf.requirements:
                if 'VDU' in req.keys():
                    if req['VDU'] == vdu.name:
                        vdu_vnfs.append(vnf)
        return vdu_vnfs

    def deploy_vnfd(self, tosca_vnfd):
        """deploy a vnfd"""

        VNFs = []
        networks = []
        VDUs = []
        ConnectionPoints = []

        def create_virtual_networks(networks):
            """create virtual networks"""
            for net in networks:
                name = net.name
                protocol_type = net.get_property_value("connectivity_type")
                self.vim.create_network(name, protocol_type)


        def get_VDU_networks(target_vdu, cpds):
            VDU_networks = []
            virtual_binding = None
            virtual_link = None
            for cpd in cpds:
                for req in cpd.requirements:
                    if "virtual_binding" in req:
                        virtual_binding = req["virtual_binding"]
                    elif "virtual_link" in req:
                        virtual_link = req["virtual_link"]
                    else:
                        raise KeyError("cpd requirements error")
                if virtual_binding == target_vdu:
                    VDU_networks.append(virtual_link)
            return VDU_networks

        def deploy_virtual_units(VNFs, VDUs, cpds):
            """Deploy VDUs"""
            for VDU in VDUs:
                name = VDU.name
                vnf = self.get_vdu_vnfs(VDU, VNFs)[0]
                sw_image = VDU.get_property_value("sw_image")
                launch_script = VDU.get_property_value("config")
                placement_policy = VDU.get_property_value("placement_policy")
                VDU_networks = get_VDU_networks(VDU.name, cpds)
                VDU_networks.append('admin_net')
                args = None
                if launch_script != 'sleep infinity':
                    args = [self.vnfm_overlay['ip'], self.vnfm_overlay['port']]
                    vnf_id = vnf.get_property_value('id')
                    args.append(vnf_id)
                    router_mode = vnf.get_property_value('mode')
                    if router_mode is not None:
                        args.append(router_mode)
                    ndn_name = vnf.get_property_value('ndn_name')
                    if ndn_name is not None:
                        args.append(ndn_name)
                service_port = VDU.get_property_value("service_port")
                if service_port is not None:
                    args.append(str(service_port))
                self.service_args[name] = args
                instance = self.vim.deploy_VDU(name=name,
                                               sw_image=sw_image,
                                               networks=VDU_networks,
                                               placement_policy=placement_policy,
                                               app=launch_script,
                                               arguments=args,
                                               endpoint=service_port)

        #function begin here
        self.ingress_gateway_ndn_names = list()
        topology_graph = tosca_vnfd.topology_template.graph
        for key, node in topology_graph.vertices.iteritems():
            if (node.type == "tosca.nodes.nfv.doctor.VNF" or
                        node.type == "tosca.nodes.nfv.doctor.VNF.firewall" or
                        node.type == "tosca.nodes.nfv.doctor.VNF.ingressGW"):
                VNFs.append(node)
                if node.type == "tosca.nodes.nfv.doctor.VNF.ingressGW":
                    ndn_name = node.get_property_value('ndn_name')
                    self.ingress_gateway_ndn_names.append(ndn_name)
            elif node.type == 'tosca.nodes.nfv.doctor.VDU':
                VDUs.append(node)
            elif node.type == "tosca.nodes.nfv.doctor.VnfVirtualLinkDesc":
                networks.append(node)
            elif node.type == 'tosca.nodes.nfv.doctor.Cpd':
                ConnectionPoints.append(node)

        # setup policies buckets to record events from NFVI
        self.setup_policies(tosca_vnfd.policies)

        create_virtual_networks(networks)
        deploy_virtual_units(VNFs, VDUs, ConnectionPoints)


        #TODO: need to keep all this nodes
        self.VNFs = VNFs

        for vnf in VNFs:
            instance = self.create_vnf_instance(topology_graph, vnf.name)
            self.nfvi_instances.append_vnf(instance)


    def is_next_hop_firewall(self, connexion_point, tosca_vnfd):
        virtual_binding = connexion_point.virtual_binding
        VNFs = self.get_vdu_vnfs(virtual_binding, self.VNFs)
        if VNFs[0].type == "tosca.nodes.nfv.doctor.VNF.firewall":
            return True
        else:
            return False


    def is_firewall(self, vnf_name, tosca_vnfd):
        topology_graph = tosca_vnfd.topology_template.graph
        for key, node in topology_graph.vertices.iteritems():
            if node.name == vnf_name:
                if node.type == node.type == "tosca.nodes.nfv.doctor.VNF.firewall":
                    return True
        return False

    def get_firewall_rules(self, firewall_vnf_name, tosca_vnfd):
        for VNF in self.VNFs:
            if VNF.name == firewall_vnf_name:
                rules =  VNF.get_property_value("configuration")
                if rules is not None:
                    return rules
                else:
                    return list()

    def create_vnffg(self, vnffg_path):
        """
        deploy VNFD and networks, then generate network rules
        :param vnffg_path: to to the VNFFG yaml file
        :return: None
        """
        vnfd = self.parse_tosca(vnffg_path)
        self.initial_deployment_template = vnfd
        self.deploy_vnfd(vnfd)


        #rules configuration start here
        groups = vnfd.topology_template.groups
        self.configurations = {}
        for group in groups:
            vnffg_paths = group.member_nodes
            for member in vnffg_paths:
                policy = member.get_property_value("policy")
                prefix_list = policy["prefix"]
                path = member.get_property_value("path")
                for idx in range(0, len(path)-1, 2):
                    long_container_id = self.nfvi_instances.get_vnf_instance(path[idx]["forwarder"]).VDU.infra_id
                    short_container_id = long_container_id[0:12]
                    if not (short_container_id in self.configurations):
                        self.configurations[short_container_id] = {}
                        if self.is_firewall(path[idx]["forwarder"], vnfd):
                            self.configurations[short_container_id]["firewall"]={}
                            self.configurations[short_container_id]["firewall"]["firewall_rules"] = self.get_firewall_rules(path[idx]["forwarder"], vnfd)
                    cpd = self.nfvi_instances.get_cpd_instance(path[idx+1]["capability"])
                    for prefix in prefix_list:
                        if (not prefix in self.ingress_gateway_ndn_names) and self.is_next_hop_firewall(cpd, vnfd):
                            face = cpd.l3address+":6360"
                            self.configurations[short_container_id].setdefault(prefix,[]).append(face)
                        else:
                            if self.is_firewall(path[idx]["forwarder"], vnfd):
                                if not (prefix in self.ingress_gateway_ndn_names):
                                    self.configurations[short_container_id]["firewall"]["next_router"] = cpd.l3address
                            face = cpd.l3address+":6363"
                            self.configurations[short_container_id].setdefault(prefix,[]).append(face)

        return 'OK'

    def get_vdu_id_list(self):
        vdu_id_list = [vdu.infra_id for vdu in self.nfvi_instances.vdu_instances]
        return vdu_id_list


    def send_VDUs_configs_to_vnfm(self):
        config = copy.deepcopy(self.configurations)
        vdu_short_id_list= [id[0:12] for id in self.get_vdu_id_list()]
        config['vnfs_id'] = vdu_short_id_list
        self.vnfm_client.send_VDUs_configs_to_vnfm(config)
        return


    def print_vnffg(self, group):
        """
        print network rules that correspond to the graph
        :param group: group object
        :return: None
        """
        vnffg_paths = group.member_nodes
        for member in vnffg_paths:
            policy = member.get_property_value("policy")
            path = member.get_property_value("path")
            print "\n**********"
            print "prefix: "+ str(policy["prefix"])
            out = True
            for idx, val in enumerate(path):
                print "-"+val["forwarder"]
                print "---VDU'sname: " + self.nfvi_instances.get_vnf_instance(val["forwarder"]).VDU.name
                print "---Container's ID: " + self.nfvi_instances.get_vnf_instance(val["forwarder"]).VDU.infra_id
                cpd= self.nfvi_instances.get_cpd_instance(val["capability"])
                if out:
                    print "---OUTPUT interface: "+cpd.l3address
                    out = False
                else:
                    print "---INPUT interface: "+cpd.l3address
                    out = True
        return


    #TODO: scaling section
    def get_ingress_vnfs(self, target_vnf):
        """
        returns vnfs (and prefix list) that send interests to target_vnf
        :param target_vnf:
        :return: dict(ingress_vnf:(prefix_list, ingress_cpd, target_cpd))
        """
        ingress_vnfs = {}
        groups = self.initial_deployment_template.topology_template.groups
        for group in groups:
            vnffg_paths = group.member_nodes
            for member in vnffg_paths:
                policy = member.get_property_value("policy")
                prefix_list = policy["prefix"]
                path = member.get_property_value("path")
                for idx in range(len(path)):
                    if path[idx]['forwarder'] == target_vnf:
                        # i can put -1 because routers have at least a gateway behind
                        if path[idx-1]['forwarder'] != target_vnf:
                            if not (path[idx-1]['forwarder'] in ingress_vnfs.keys()):
                                ingress_vnfs[path[idx-1]['forwarder']] = ([],
                                                                          path[idx-1]['capability'],
                                                                          path[idx]['capability'])
                            ingress_vnfs[path[idx-1]['forwarder']][0].extend(prefix_list)

        return ingress_vnfs

    def handle_cpa_alert(self, probe_id):
        action = None
        router = self.get_vnf_from_id(probe_id)
        print ('\x1b[0;37;41m' +'***  cpa alert on {0}  ***'.format(router)+ '\x1b[0m')
        for policy in self.policies:
            if policy.type == "tosca.policies.nfv.doctor.security.signature_verification":
                    actions = policy.evaluate(router)
		    #pprint.pprint(actions)
                    for action in actions:
                        if not (action['target_router'] in self.sv_routers):
                            print ('\x1b[6;30;42m' +'updating {0} mode to signature_verification'.format(action['target_router'])+ '\x1b[0m')
                            self.apply_signature_verification_policy(action['target_router'])

    def apply_signature_verification_policy(self, target_router):
    	self.sv_routers.append(target_router)	
	# TODO: target VDU, delete it from VNFM
        service_vdu = self.nfvi_instances.get_vnf_instance(target_router).VDU
        ingress_vnfs = self.get_ingress_vnfs(target_router)
        service = self.vim.low_level_get_service(service_vdu.name)
        tasks = self.vim.low_level_get_service_tasks(service['ID'])
	target_router_ids=[]	
        target_interfaces=[]
	replicas_configurations = {}
	service_rules = self.configurations[service_vdu.infra_id[0:12]]
	while True:
            try:
                for task in tasks:
                   #if task['Status']['ContainerStatus']['ContainerID'] != service_vdu.infra_id:
                        #service_tasks.append(task)
			target_router_ids.append({'router_id':task['Status']['ContainerStatus']['ContainerID'][0:12], 'router_mode':'SV'})
                	replicas_configurations[task['Status']['ContainerStatus']['ContainerID'][0:12]] = service_rules
		break
            except KeyError:
                service = self.vim.low_level_get_service(service_vdu.name)
                tasks = self.vim.low_level_get_service_tasks(service['ID'])
        ingress_configurations_updates = {}
        for forwarder, value in ingress_vnfs.iteritems():
            cpd = self.nfvi_instances.get_cpd_instance(value[1])
            forwarder_vdu = self.nfvi_instances.get_vnf_instance(forwarder).VDU
            forwarder_container_id = forwarder_vdu.infra_id[0:12]
            ingress_configurations_updates[forwarder_container_id] = {
                'to_delete':[],
                'to_add':{}
            }
            container_updates = ingress_configurations_updates[forwarder_container_id]
            container_updates['to_delete'].extend(value[0])
	    for task in tasks:
                for idx in range(len(task['NetworksAttachments'])):
                    if task['NetworksAttachments'][idx]['Network']['Spec']['Name'] == cpd.virtual_link.name:
                        face = task['NetworksAttachments'][idx]['Addresses'][0]
                        #if target_interfaces in self.sv_routers:
                        face = face.split('/')[0]+':6362'
			for prefix in value[0]:
				container_updates['to_add'].setdefault(prefix, []).append(face)
	#print("target_router_ids")
	#pprint.pprint(target_router_ids)

	#get ingress_router configuration
        ingress_routers = self.get_ingress_vnfs(target_router)
        assert len(ingress_routers.keys()) == 1
        for forwarder, value in ingress_routers.iteritems():
            ingress_router = forwarder
	ingress_router_vdu = self.nfvi_instances.get_vnf_instance(ingress_router).VDU
        ingress_router_id = ingress_router_vdu.infra_id[0:12]
        ingress_router_configuration = self.configurations[ingress_router_id]
	for target_router_mode in target_router_ids:
		self.vnfm_client.send_update_router_mode(target_router_mode)
	scaled_service_configuration = {'container_down':"",
                                        'ingress_configurations':ingress_configurations_updates,
                                        'replicas_configurations': replicas_configurations}
        print  (ingress_configurations_updates)

        self.vnfm_client.send_scaled_service_config(scaled_service_configuration)

    def bk_apply_signature_verification_policy(self, target_router):

        #TODO: if the service is scaled, this function do not
        #TODO: use another ID (container ID) istead of probe_id
	self.sv_routers.append(target_router)
	# get ingress grouter. SV module can have only one ingress router
        ingress_routers = self.get_ingress_vnfs(target_router)
        #pprint.pprint(ingress_routers)
	#pprint.pprint(target_router)
	assert len(ingress_routers.keys()) == 1
        for forwarder, value in ingress_routers.iteritems():
            ingress_router = forwarder
            prefix_list = value[0]
            ingress_interface = self.nfvi_instances.get_cpd_instance(value[1]).l3address
            target_interface = self.nfvi_instances.get_cpd_instance(value[2]).l3address
	    pprint.pprint(target_interface)
	    pprint.pprint(self.nfvi_instances.get_cpd_instance(value[2]))

        #get target_router_id
        target_router_vdu = self.nfvi_instances.get_vnf_instance(target_router).VDU
        target_router_id = target_router_vdu.infra_id[0:12]
        target_router_mode = {'router_id':target_router_id, 'router_mode':'SV'}
	

        #get ingress_router configuration
        ingress_router_vdu = self.nfvi_instances.get_vnf_instance(ingress_router).VDU
        ingress_router_id = ingress_router_vdu.infra_id[0:12]
        ingress_router_configuration = self.configurations[ingress_router_id]

        # list to keep faces to be deleted from ingress vnfs
        to_update = {}

        for prefix, face_list in ingress_router_configuration.iteritems():
            if prefix in prefix_list:
                for idx in range(len(face_list)):
                    if face_list[idx].split(':')[0] == (target_interface):
                        # list are passed by reference, so i updated the configuration
                        face_list[idx] = target_interface + ':6362'
                        to_update[prefix] = copy.deepcopy(face_list[idx])
                        break
        self.vnfm_client.send_update_router_mode(target_router_mode)
        self.vnfm_client.send_update_faces(ingress_router_id, to_update)


    def handle_pit_stats_in(self, probe_id, count_metric, ip):
        vnf = self.get_vnf_from_id(probe_id)
        #print "VNF ID {0} --> PIT_VALUE == {1}".format(probe_id, count_metric)
        for policy in self.policies:
            if policy.type == 'tosca.policies.nfv.doctor.ndn.scaling':
                for target in policy.targets:
                    if target == vnf:
                        print "VNF({0}) --> PIT_SIZE == {1} -> From {2}".format(vnf, count_metric, ip)
                        deploy_log = open("deploy_log", "a")         
                        ts = time.time()
                        deploy_log.write(str(ts)+":"+str(vnf)+":"+str(ip)+":"+str(count_metric)+"\n")
                        policy.meter_in('PIT', vnf, count_metric)

    #TODO: I need a real service class, not only VDU
    def apply_scaling_policy(self, target, replicas):

        print ('\x1b[6;30;42m' +'applying scaling policy for service {0}'.format(target)+ '\x1b[0m')
        # TODO: target VDU, delete it from VNFM
        service_vdu = self.nfvi_instances.get_vnf_instance(target).VDU
        vdu_short_id= service_vdu.infra_id[0:12]
        dontainer_down = vdu_short_id
	
        # rules to be installed on the scalled service, do not change
        service_rules = self.configurations[vdu_short_id]

        # vnfs to be update to send flows to service replicas
        # format: dict(ingress_vnf:(prefix_list, ingress_cpd, target_cpd))
        ingress_vnfs = self.get_ingress_vnfs(target)
	
        # scale the service
        service_arguments = self.service_args[service_vdu.name]
        if target in self.sv_routers:
            service_arguments.append('SV')
            self.scale_service(service_vdu.name, replicas, service_arguments)
        else:
            self.scale_service(service_vdu.name, replicas, service_arguments)

        # get replicas configurations
        #TODO: keep trace of scaled services
        self.scaled_services_configuration[service_vdu.name] = []
        service = self.vim.low_level_get_service(service_vdu.name)
	
        # ensure that all replicas are up
        tasks = self.vim.low_level_get_service_tasks(service['ID'])
        while True:
            tasks = self.vim.low_level_get_service_tasks(service['ID'])
            if len(tasks) >= replicas:
                break

        replicas_configurations = {}
        
        while True:
            try:
                service_tasks= []
                for task in tasks:
                   #if task['Status']['ContainerStatus']['ContainerID'] != service_vdu.infra_id:
                       service_tasks.append(task)
                       replicas_configurations[task['Status']['ContainerStatus']['ContainerID'][0:12]] = service_rules
                break
            except KeyError:
                service = self.vim.low_level_get_service(service_vdu.name)
                tasks = self.vim.low_level_get_service_tasks(service['ID'])

        ingress_configurations_updates = {}
        for forwarder, value in ingress_vnfs.iteritems():
            cpd = self.nfvi_instances.get_cpd_instance(value[1])
            forwarder_vdu = self.nfvi_instances.get_vnf_instance(forwarder).VDU
            forwarder_container_id = forwarder_vdu.infra_id[0:12]
            ingress_configurations_updates[forwarder_container_id] = {
                'to_delete':[],
                'to_add':{}
            }
            container_updates = ingress_configurations_updates[forwarder_container_id]
            container_updates['to_delete'].extend(value[0])
            for task in service_tasks:
                for idx in range(len(task['NetworksAttachments'])):
                    if task['NetworksAttachments'][idx]['Network']['Spec']['Name'] == cpd.virtual_link.name:
                        face = task['NetworksAttachments'][idx]['Addresses'][0]
                        #if target in self.sv_routers:
                        face = face.split('/')[0]+':6362'
                        for prefix in value[0]:
                            container_updates['to_add'].setdefault(prefix, []).append(face)

        scaled_service_configuration = {'container_down':vdu_short_id,
                                        'ingress_configurations':ingress_configurations_updates,
                                        'replicas_configurations': replicas_configurations}

        #print  ("---update scaled service configuration---")
        print  ("---ingress-config---")
        pprint.pprint(scaled_service_configuration)
        #print  ('---replicas-config---')
        #print  (replicas_configurations)
        #print  ("---container down ---")
        #print  (vdu_short_id)

        self.vnfm_client.send_scaled_service_config(scaled_service_configuration)
        print 'service {0} scaled to {1} replicas'.format(target, replicas)
        if target in self.sv_routers:
            time.sleep(20)
            self.apply_signature_verification_policy(target)
        #TODO: need to delete old container



    def scale_service(self, target_service, replicas, args):
        scaling_op = self.vim.scale_service(target_service,replicas, args)
        if scaling_op == True:
            print str(target_service)+" has been scaled"

        #donc, il me faut une classe service!!!
        #pass the command to docker vim
        #retrive new container information
        #call get_ingress_vnfs
        #transforme get_ingress_vnfs into {container_short_id: {prefix:[list_short_container_id}}
        #normalement il a deja le prefix, il faut juste ajouter une nouvelle face pour le prefix
        #compare with old configuration (perhaps not the first sclaup)
        #retrive target vnf configuration (the new container)
        #send configuration to configure new container
        #configure ingress vnfs to send interests also to new container
        pass

    def handle_poisoned_content_alert(self):
        pass

