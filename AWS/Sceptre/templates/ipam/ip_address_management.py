# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod


class IpAddressManagement(metaclass=ABCMeta):
    default_protocol = 'tcp'

    def __init__(self):
        self.protocol = self.default_protocol
        self.from_port = None
        self.to_port = None

    @abstractmethod
    def get_cidr(self):
        pass

    @abstractmethod
    def get_description(self):
        pass
