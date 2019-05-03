# -*- coding: utf-8 -*-
from troposphere.ec2 import SecurityGroupRule, SecurityGroup


class SecurityGroupResourceBuilder(object):

    def __init__(self, vpc_id=None, security_group_description=None):
        self.__ip_address_management_ingress_list = []
        self.__vpc_id = vpc_id
        self.__security_group_name = 'SecurityGroupDefaultName'
        self.__security_group_description = security_group_description
        self.__vpc_id = vpc_id

        if self.__vpc_id is None:
            raise Exception('VPC ID: required value')

        if self.__security_group_description is None:
            raise Exception('Security Group Description: required value')

    def allow_access_from(self, ip_address_management):
        self.__ip_address_management_ingress_list.append(ip_address_management)

        return self

    def with_name(self, security_group_name):
        self.__security_group_name = security_group_name

        return self

    def build(self):
        security_group_rule_ingress_list = []
        for ip_address_management_ingress in self.__ip_address_management_ingress_list:
            security_group_rule = SecurityGroupRule()
            security_group_rule.IpProtocol=ip_address_management_ingress.protocol
            security_group_rule.CidrIp=ip_address_management_ingress.get_cidr()
            security_group_rule.Description=ip_address_management_ingress.get_description()

            if ip_address_management_ingress.from_port is not None:
                security_group_rule.FromPort = ip_address_management_ingress.from_port

            if ip_address_management_ingress.to_port is not None:
                security_group_rule.ToPort=ip_address_management_ingress.to_port

            security_group_rule_ingress_list.append(security_group_rule)

        return SecurityGroup(
            self.__security_group_name,
            GroupDescription=self.__security_group_description,
            SecurityGroupIngress=security_group_rule_ingress_list,
            VpcId=self.__vpc_id
        )




