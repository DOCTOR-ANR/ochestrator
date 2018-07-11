import copy

class VirtualLinkInstance(object):
    """TODO:"""
    def __init__(self, name, subnet, gateway):
        """

        :param name: A string, virtual link name
        :param subnet: A string, virtual network subnet IP address
        :param gateway: A string, virtual network gateway IP address
        """
        self._name = name
        self._subnet = subnet
        self._gateway = gateway

    @property
    def name(self):
        return self._name

    @property
    def subnet(self):
        return self._subnet

    @property
    def gateway(self):
        return self._gateway

class CpdInstance(object):
    """TODO"""
    def __init__(self, name, l3address, vdu, virtual_link, protocol='mpls', l2Address=None):
        """

        :param name: A string, connexion point name
        :param l3address: A string, connexion point IP address
        :param protocol: A string, connexion point virtual communication protocol
        :param vdu: object instance
        :param virtual_link: object instance
        :param L2Address: string
        """
        self._name = name
        self._protocol_layer = protocol
        self._l3address = l3address
        self._l2address = l2Address
        self._virtual_binding = vdu
        self._virtual_link = virtual_link

    @property
    def l3address(self):
        return self._l3address

    @property
    def L2address(self):
        return self._l2address

    @property
    def name(self):
        return self._name

    @property
    def protocol_layer(self):
        return self._protocol_layer

    @property
    def virtual_binding(self):
        return self._virtual_binding

    @property
    def virtual_link(self):
        return self._virtual_link


class VDUInstance(object):
    """TODO"""
    def __init__(self, name, id, sw_image, l3addresses, flavor=None):
        """

        :param name: string
        :param id: string
        :param sw_image: string
        :param flavor: string
        """
        self._name = name
        self._infra_id = id
        self._sw_image = sw_image
        self._flavor = flavor
        self._l3addresses = l3addresses

    @property
    def name(self):
        return self._name

    @property
    def sw_image(self):
        return self._sw_image

    @property
    def infra_id(self):
        return self._infra_id

    @property
    def l3addresses(self):
        return self._l3addresses


class VNFInstance(object):
    """TODO"""
    def __init__(self, id, vdu):
        self._id = id
        self._VDU = vdu

    @property
    def id(self):
        return self._id

    @property
    def VDU(self):
        return self._VDU


class NFVInstances(object):
    """TODO :  also for ns and VNFFG"""
    def __init__(self):
        self._vnf_instances = []
        self._cpd_instances = []
        self._virtual_links = []
        self._vdu_instances = []


    def append_vnf(self, instance):
        """

        :param instance: VNFInstance object
        :return: None
        """
        self._vnf_instances.append(instance)
        return

    def append_virtual_link(self, instance):
        """

        :param instance: VirtualLinkInstance object
        :return: None
        """
        self._virtual_links.append(instance)
        return

    def append_connextion_point(self, instance):
        """

        :param instance: CpdInstance object
        :return: None
        """
        self._cpd_instances.append(instance)
        return

    def append_vdu(self, instance):
        """

        :param instance: VDUInstance object
        :return: None
        """
        self._vdu_instances.append(instance)
        return

    def get_vnf_instance(self, name):
        """

        :param name: VNF name
        :return: copy of VNFInstance object
        """
        for vnf in self._vnf_instances:
            if vnf.id == name:
                return copy.deepcopy(vnf)

    def get_cpd_instance(self, name):
        """

        :param name: cpd name
        :return: copy of CpdInstance object
        """
        for cpd in self._cpd_instances:
            if cpd.name == name:
                return copy.deepcopy(cpd)

    def get_virtual_link_instance(self, name):
        """

        :param name: virtual link's name
        :return: copy of VirtualLinkInstance object
        """
        for network in self._virtual_links:
            if network.name == name:
                return copy.deepcopy(network)

    def get_vdu_instance(self, name):
        """

        :param name: VDU's name
        :return: copy of VDUInstance object
        """
        for vdu in self._vdu_instances:
            if vdu.name == name:
                return copy.deepcopy(vdu)


    @property
    def vnf_instances(self):
        """
        :return: a copy of all (a list) vnf instances
        """
        return copy.deepcopy(self._vnf_instances)

    @property
    def cpd_instances(self):
        """
        :return: a copy of all (a list) connexion point instances
        """
        return copy.deepcopy(self._cpd_instances)

    @property
    def virtual_links(self):
        """
        :return: a copy of all (a list) virtual link instances
        """
        return copy.deepcopy(self._virtual_links)

    @property
    def vdu_instances(self):
        """
        :return: a copy of all (a list) vdu instances
        """
        return copy.deepcopy(self._vdu_instances)

    #TODO: use decorator for these function ??
