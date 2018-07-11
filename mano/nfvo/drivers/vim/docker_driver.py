import pdb
import time
from collections import namedtuple
#from ...catalogs.nfv.vnf.vnf import VNFInstance, VDUInstance

import docker
from abstract_vim_driver import AbstractInfrastructureManager
from docker.types.services import ServiceMode
from docker import types
from docker.types.services import ContainerSpec, TaskTemplate, Placement
import json
import requests_unixsocket
import subprocess
import urllib   
import pprint

client = docker.from_env()
APIClient = docker.APIClient(version='1.32')

#Containers = client.containers
#Networks = client.networks
#Swarm = client.swarm
#Services = client.services

VDU = namedtuple('VDU', ['name',
                         'id',
                         'sw_image',
                         'network_addresses'])

class InfrastructureManager(AbstractInfrastructureManager):
    def __init__(self, mtu=1400):
        self.overlay_opt_dict = dict()
        self.overlay_opt_dict["com.docker.network.driver.mtu"] = "1400"
        self.vl_count = 1

    def init_nfvi(self):
        pass

    def get_name(self):
        return "Docker"

    def get_type(self):
        return "Container"

    def create_admin_net(self):
        ipam_pool = docker.types.IPAMPool(subnet="10.10.0.0/24",
                                          iprange="10.10.0.0/24",
                                          gateway="10.10.0.1")
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        client.networks.create("admin_net",
                               driver="overlay",
                               ipam=ipam_config,
                               options=self.overlay_opt_dict)


    def create_network(self, name, protocol_type):
        """

        :param name: string
        :param protocol_type: string
        :return: None
        """
        def generate_subnet_ip():
            net_ip = "10.0.net.gateway/24"
            net_ip = net_ip.replace("net", str(self.vl_count))
            gateway = net_ip.replace("gateway", "1")
            gateway = gateway.split("/")[0]
            net_ip = net_ip.replace("gateway", "0")
            self.vl_count+=1
            return net_ip, gateway


        net_ip, gateway = generate_subnet_ip()
        ipam_pool = docker.types.IPAMPool(subnet=net_ip,
                                          iprange=net_ip,
                                          gateway=gateway)

        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

        if protocol_type == "VXLAN":
            driver = "overlay"
            client.networks.create(name,
                                   driver="overlay",
                                   ipam=ipam_config,
                                   options=self.overlay_opt_dict)
        else:
            raise TypeError("only VXLAN protocol type is supported")

    def get_service(self, name):
        while True:
            try:
                service = client.services.get(name)
                if service.tasks()[0][u'Status'][u'State'] != u'running':
                    time.sleep(.500)
                    service = client.services.get(name)
                return service
                break
            except IndexError:
                print "Docker API not available yet!"

    def get_network_config(self, name):
        """
        get network configuration after deployment
        :param name: string
        :return: dict with subnet IP and gateway IP address
        """
        net = APIClient.inspect_network(name)
        subnet = net[u'IPAM'][u'Config'][0][u'Subnet']
        gateway = net[u'IPAM'][u'Config'][0][u'Gateway']
        return {'Subnet':subnet, 'Gateway':gateway}

    def get_vdu(self, name):
        service = self.get_service(name)
        vdu_networks_addresses = []
        vdu_name = service.name
        service_vdu_list = []
        while True:
            try:
                for container in service.tasks():
                    vdu_sw_image = container[u'Spec'][u'ContainerSpec'][u'Image']
                    vdu_id = container[u'Status'][u'ContainerStatus'][u'ContainerID']
                    for net_attachments in container[u'NetworksAttachments']:
                        vdu_networks_addresses.append(net_attachments[u'Addresses'][0])
                    service_vdu_list.append(VDU(vdu_name,
                                                vdu_id,
                                                vdu_sw_image,
                                                vdu_networks_addresses))
                break
            except KeyError:
                # to update information from docker engine
                del service_vdu_list[:]
                service = client.services.get(name)
        return service_vdu_list

    def get_short_id(self, log_id):
        self.check_service_running()
        for service in client.services.list():
            VDU_id = container[u'Status'][u'ContainerStatus'][u'ContainerID']


    def check_service_running(self):
        services = client.services.list()
        for service in services:
            if service.tasks()[0][u'Status'][u'State'] != u'running':
                time.sleep(.500)
                services = client.services.list()
        return

    def get_VDUs_instances(self):

        VDU = namedtuple('VDU', ['name',
                                 'id',
                                 'sw_image',
                                 'network_addresses'])

        def check_service_running():
            services = client.services.list()
            for service in services:
                if service.tasks()[0][u'Status'][u'State'] != u'running':
                    time.sleep(.500)
                    services = client.services.list()
            return

        vdu_instances = []
        check_service_running()
        services = client.services.list()
        for service in services:
            VDU_networks_addresses = []
            VDU_name = service.name
            container = service.tasks()[0]
            VDU_sw_image = container[u'Spec'][u'ContainerSpec'][u'Image']
            VDU_id = container[u'Status'][u'ContainerStatus'][u'ContainerID']
            for net_attachments in container[u'NetworksAttachments']:
                VDU_networks_addresses.append(net_attachments[u'Addresses'])
            vdu_instances.append(VDU(VDU_name,
                                     VDU_id,
                                     VDU_sw_image,
                                     VDU_networks_addresses))
        return vdu_instances


    def deploy_VDU(self, name,
                   sw_image,
                   networks,
                   placement_policy,
                   app="sleep infinity",
                   arguments=None,
                   endpoint=None,
                   mode="replicated",
                   replicas=1):
        """

        :param name:
        :param sw_image:
        :param networks:
        :param placement_policy:
        :param mode:
        :param replicas:
        :return:
        """
        placement_constraints = []
        if placement_policy is not None:
            for constraint in placement_policy:
                label, value = constraint.split("==")
                label = "node.labels."+label
                placement_constraints.append(label+"=="+value)
        oneRep = ServiceMode(mode, replicas)
        service_port = None
        if endpoint is not None:
            service_port = docker.types.EndpointSpec(mode='vip', ports={endpoint:endpoint})
        docker_vdu = client.services.create(sw_image,
                                            command=app,
                                            args=arguments,
                                            name=name,
                                            networks=networks,
                                            mode=oneRep,
                                            constraints=placement_constraints,
                                            endpoint_spec=service_port)

    def low_level_get_service(self, service_name):
        services = APIClient.services()
        for service in services:
            if service['Spec']['Name'] == service_name:
                return service

    def low_level_get_service_tasks(self, service_id):
        tasks = APIClient.tasks()
        service_tasks = []
        for task in tasks:
            if task['ServiceID'] == service_id:
                service_tasks.append(task)
        return service_tasks

    def scale_service(self, target_service_name, replicas, arguments):
        services = APIClient.services()
        target_service = None
        for service in services:
            if service["Spec"]["Name"] == target_service_name:                
                str_command = "sudo docker service scale "+str(service["ID"])+"="+str(replicas)
                print(str_command);
                subprocess.call(args=str_command, shell=True)

    def scale_service_bk_2(self, target_service_name, replicas, arguments):
        new_mode = {'replicated': {'Replicas': replicas}}#global
        services = APIClient.services()
        target_service = None
        for service in services:
            if service["Spec"]["Name"] == target_service_name:
                session = requests_unixsocket.Session()
                r1 = session.get('http+unix://'+urllib.quote_plus('/var/run/docker.sock')+'/v1.25/services/'+service["ID"])
                #pprint.pprint(r1.json())
                target_service=r1.json()
                break
        if not target_service is None:
            task_template = types.TaskTemplate(service["Spec"]["TaskTemplate"])
            old_constraints = service['Spec']['TaskTemplate']['Placement']['Constraints']
            placement_constraints = Placement(old_constraints)
            container_image = task_template['ContainerSpec']['ContainerSpec']['Image']
            container_command = task_template['ContainerSpec']['ContainerSpec']['Command']
            container_spec = ContainerSpec(image=container_image,
                                           command=container_command
                                           ,args=arguments)#
            # Issue between Docker engine API and docker Python API !!!
            adapted_template = TaskTemplate(container_spec, placement=placement_constraints)
            networks = target_service["Spec"]['Networks']
            print(adapted_template);
            #print(replicas)
            #print(json.dumps(target_service));
            data={'Name': target_service_name,'TaskTemplate':adapted_template,'Mode': {'Replicated': {'Replicas': replicas}},'Endpoint': service['Endpoint'],'Networks': service['Spec']['Networks']}       
            #print(json.dumps(data));
            headers = {}
            headers['Content-Type'] = 'application/json';
            session = requests_unixsocket.Session()
            r = session.post('http+unix://'+urllib.quote_plus('/var/run/docker.sock')+'/v1.25/services/'+str(target_service["ID"])+'/update?version='+str(target_service["Version"]["Index"]),json=data,headers=headers);
            pprint.pprint(r.json())
        else:
            print "can't scale service :"+str(target_service_name)

    def scale_service_bk(self, target_service_name, replicas, arguments):
        new_mode = {'replicated': {'Replicas': replicas}}#global
        services = APIClient.services()
        target_service = None
        for service in services:
            if service["Spec"]["Name"] == target_service_name:
                target_service = service
                break
        if not target_service is None:
            task_template = types.TaskTemplate(service["Spec"]["TaskTemplate"])
            old_constraints = service['Spec']['TaskTemplate']['Placement']['Constraints']
            placement_constraints = Placement(old_constraints)
            container_image = task_template['ContainerSpec']['ContainerSpec']['Image']
            container_command = task_template['ContainerSpec']['ContainerSpec']['Command']
            container_spec = ContainerSpec(image=container_image,
                                           command=container_command,
                                           args=arguments)
            # Issue between Docker engine API and docker Python API !!!
            adapted_template = TaskTemplate(container_spec, placement=placement_constraints)
            networks = target_service["Spec"]['Networks']
            APIClient.update_service(target_service_name,
                                  version=target_service["Version"]["Index"],
                                  task_template=adapted_template,
                                  mode=new_mode,
                                  networks=networks,
                                  name=target_service_name)
        else:
            print "can't scale service :"+str(target_service_name)

