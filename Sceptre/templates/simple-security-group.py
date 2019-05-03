#!/usr/bin/python
# coding: utf-8
#
from iam.home_office import HomeOffice
from iam.security_group_resource_builder import SecurityGroupResourceBuilder
from troposphere import Template, Output, Export, Join, Ref, StackName, GetAtt


class SimpleSecurityGroup(object):

    def __init__(self, sceptre_user_data):
        self.sceptre_user_data = sceptre_user_data
        self._template = Template(Description='Simple Security Group')
        self._template.AWSTemplateFormatVersion = '2010-09-09'
        self.__add_security_group()
        self.__add_outputs()

    def __add_security_group(self):
        vpc_id = self.sceptre_user_data.get('VpcId')
        security_group_description = self.sceptre_user_data.get('SecurityGroupDescription')
        security_group_name = self.sceptre_user_data.get('SecurityGroupName')
        postgresql_port = self.sceptre_user_data.get('PostgreSQLPort')

        home_office = HomeOffice()
        home_office.from_port = postgresql_port
        home_office.to_port = postgresql_port

        self.__security_group_resource =\
            SecurityGroupResourceBuilder(vpc_id=vpc_id, security_group_description=security_group_description)\
            .with_name(security_group_name)\
            .allow_access_from(home_office)\
            .build()
        self._template.add_resource(self.__security_group_resource)

    def __add_outputs(self):
        self._template.add_output(
            Output(
                self.sceptre_user_data.get('SecurityGroupName'),
                Value=Ref(self.__security_group_resource),
                Export=Export(Join("-", [StackName, "security-group"]))

            )
        )


def sceptre_handler(sceptre_user_data):
    simple_security_group = SimpleSecurityGroup(sceptre_user_data)
    return simple_security_group._template.to_json()
