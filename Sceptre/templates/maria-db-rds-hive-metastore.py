#!/usr/bin/python
# coding: utf-8
#

from troposphere import Parameter, Template, Ref, Output, Export, Join, StackName, GetAtt
import troposphere.rds as rds
import troposphere.ec2 as ec2


class MariaDBRDSHiveMetastore(object):

    def __init__(self, sceptre_user_data):
        self.__db_instance_name = 'MariaDBRDSHiveMetastore'
        self._template = Template(Description='MariaDB RDS Hive Metastore')
        self._template.AWSTemplateFormatVersion = '2010-09-09'
        self.sceptre_user_data = sceptre_user_data
        self.__add_arguments()
        self.__add_rds()
        self.__add_outputs()

    def __add_arguments(self):
        self.project = self._template.add_parameter(Parameter(
            "Project",
            Type="String",
            Description="Project Name",
            MinLength="1",
            MaxLength="255",
            Default='MariaDB RDS Hive Metastore Project',
            AllowedPattern="[\\x20-\\x7E]*",
            ConstraintDescription="can contain only ASCII characters.",
        ))
        self.__vpc = self._template.add_parameter(
            Parameter(
                'Vpc',
                Type='AWS::EC2::VPC::Id',
                ConstraintDescription='must be the id of an existing vpc.',
                Description='Id of an existing vpc '
            )
        )
        self.__master_user_password = self._template.add_parameter(
            Parameter(
                'MasterUserPassword',
                Type='String',
                ConstraintDescription='master user password for data base.',
                Description='Master user password for data base ',
                NoEcho=True
            )
        )
        self.__master_user_name = self._template.add_parameter(
            Parameter(
                'MasterUserName',
                Type='String',
                ConstraintDescription='master user name for data base',
                Description='Master user name for data base ',
                Default='dbadmin'
            )
        )
        self.__subnet_ids = self._template.add_parameter(
            Parameter(
                'SubnetIds',
                Type='List<AWS::EC2::Subnet::Id>',
                ConstraintDescription='must be the ids of existing subnets.',
                Description='Ids of existing subnets '
            )
        )
        self.__db_instance_class = self._template.add_parameter(
            Parameter(
                'DB2InstanceClass',
                Type='String',
                ConstraintDescription='must be the name of some db instance class',
                Description='https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html '
            )
        )
        self.__db_instance_identifier = self._template.add_parameter(
            Parameter(
                'DB2InstanceIdentifier',
                Type='String',
                ConstraintDescription='must be the name of the created RDS',
                Description='Name of the created RDS '
            )
        )
        self.__allocated_storage = self._template.add_parameter(
            Parameter(
                'AllocatedStorage',
                Type='Number',
                ConstraintDescription='allocated storage',
                Description='Allocated storage ',
                Default=50
            )
        )
        self.__iops = self._template.add_parameter(
            Parameter(
                'IOPS',
                Type='Number',
                ConstraintDescription='provisioned iops',
                Description='Provisioned IOPS ',
                Default=50
            )
        )

    # Create cloudformation for security groups, export its outputs and use them here.
    # This security group can be used by RDS, EC2, etc, etc.
    def __add_database_security_group(self):
        security_group_ingress = ec2.SecurityGroupRule(
            'MariaDBRDSSecurityGroupIngress',
            IpProtocol='tcp',
            FromPort=5432,
            ToPort=5432,
            CidrIp='192.168.1.0/24'
        )
        return ec2.SecurityGroup(
            'MariaDBRDSSecurityGroup',
            GroupDescription='Access to RDS',
            SecurityGroupIngress=[
                security_group_ingress],
            VpcId=Ref(self.__vpc)
        )

    # Should I share this subnet group with more data bases? Should it be located in its own cloudformation?
    # This stuff can only be reused by other data bases :(
    def __add_database_subnet_group(self):
        return rds.DBSubnetGroup(
            'MariaDBRDSSubnetGroup',
            DBSubnetGroupDescription="MariaDB RDS subnet groups",
            SubnetIds=Ref(self.__subnet_ids)
        )

    # Should I share this parameter group with more data bases? Should it be located in its own cloudformation?
    # This stuff can only be reused other data bases :(
    def __add_parameter_group(self):
        return rds.DBParameterGroup(
            'MariaDBRDSParameterGroup',
            Description="MariaDB RDS parameters group",
            Family="mariadb10.3",
            Parameters={
                'slow_query_log': '1',
                'long_query_time': '5',
                'log_output': 'FILE'}
        )

    def __add_rds(self):
        database_parameter_group = self.__add_parameter_group()
        self._template.add_resource(database_parameter_group)

        database_subnet_group = self.__add_database_subnet_group()
        self._template.add_resource(database_subnet_group)

        database_security_group = self.__add_database_security_group()
        self._template.add_resource(database_security_group)

        db_instance = rds.DBInstance(self.__db_instance_name)
        db_instance.AllocatedStorage = Ref(self.__allocated_storage)
        db_instance.AllowMajorVersionUpgrade = False
        db_instance.AutoMinorVersionUpgrade = True
        db_instance.DBName = "rootdatabase"
        db_instance.DBParameterGroupName = Ref(database_parameter_group)
        db_instance.DBSubnetGroupName = Ref(database_subnet_group)
        db_instance.DBInstanceClass = Ref(self.__db_instance_class)
        db_instance.DBInstanceIdentifier = Ref(self.__db_instance_identifier)
        db_instance.Engine = "mariadb"
        db_instance.EngineVersion = "10.3.13"
        db_instance.MasterUsername = Ref(self.__master_user_name)
        db_instance.MasterUserPassword = Ref(self.__master_user_password)
        db_instance.MultiAZ = False
        db_instance.PubliclyAccessible = False
        db_instance.StorageType = "gp2"
        db_instance.VPCSecurityGroups = Ref(database_security_group)
        self._template.add_resource(db_instance)

    def __add_outputs(self):
        self._template.add_output(
            Output(
                "RDSAddress",
                Value=GetAtt(self.__db_instance_name, "Endpoint.Address"),
                Export=Export(Join("-", [StackName, "endpoint"]))

            )
        )
        self._template.add_output(
            Output(
                "RDSPort",
                Value=GetAtt(self.__db_instance_name, "Endpoint.Port"),
                Export=Export(Join("-", [StackName, "port"]))

            )
        )

def sceptre_handler(sceptre_user_data):
    simple_rds = MariaDBRDSHiveMetastore(sceptre_user_data)
    return simple_rds._template.to_json()


if __name__ == '__main__':
    print(sceptre_handler(""))
