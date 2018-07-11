from abc import ABCMeta, abstractmethod

class AbstractInfrastructureManager(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        """TODO"""
        self.client = docker.from_env()
        self.overlay_opt_dict = {}

    @abstractmethod
    def init_nfvi(self):
        """

        :return:
        """
        return

    @abstractmethod
    def get_name(self):
        """

        :return:
        """
        return

    @abstractmethod
    def get_type(self):
        """

        :return:
        """
        return

    @abstractmethod
    def get_service(self, name):
        """

        :param name:
        :return:
        """
        return

    @abstractmethod
    def get_network_config(self, name):
        """

        :param name:
        :return:
        """
        return

    @abstractmethod
    def get_vdu(self, name):
        """

        :param name:
        :return:
        """
        return

    @abstractmethod
    def get_VDUs_instances(self):
        """

        :return:
        """
        return

    @abstractmethod
    def create_network(self, name, protocol_type):
        """

        :param name:
        :param protocol_type:
        :return:
        """
        return

    @abstractmethod
    def deploy_VDU(self, name,
                   sw_image,
                   networks,
                   placement_policy,
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
        return

    #TODO: methodes to get information on resources
