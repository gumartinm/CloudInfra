# -*- coding: utf-8 -*-
from ipam.ip_address_management import IpAddressManagement


class HomeOffice(IpAddressManagement):
    CIDR = '192.168.1.0/24'
    DESCRIPTION = 'My Home Network'

    def get_cidr(self):
        return self.CIDR

    def get_description(self):
        return self.DESCRIPTION


