#!/usr/bin/python
# coding: utf-8
#

from troposphere import Parameter, Template, Ref, Output, Export, Join, StackName, GetAtt
import troposphere.rds as rds


class AuroraServerless(object):

    def __init__(self, sceptre_user_data):
        self.__db_cluster_name = 'AuroraClusterServerless'
        self._template = Template(Description='Aurora RDS Serverless')
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
            Default='Aurora Serverless',
            AllowedPattern="[\\x20-\\x7E]*",
            ConstraintDescription="can contain only ASCII characters.",
        ))
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
        self.__security_group_id = self._template.add_parameter(
            Parameter(
                'SecurityGroupId',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the ids of existing security group.',
                Description='Ids of existing security group '
            )
        )
        self.__db_cluster_identifier = self._template.add_parameter(
            Parameter(
                'DBClusterIdentifier',
                Type='String',
                ConstraintDescription='must be the name of the created RDS',
                Description='Name of the created RDS '
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

    # Should I share this subnet group with more data bases? Should it be located in its own cloudformation?
    # This stuff can only be reused by other data bases :(
    def __add_database_subnet_group(self):
        return rds.DBSubnetGroup(
            'AuroraServerless',
            DBSubnetGroupDescription="Aurora serverless",
            SubnetIds=Ref(self.__subnet_ids)
        )

    # Should I share this parameter group with more data bases? Should it be located in its own cloudformation?
    # This stuff can only be reused by other data bases :(
    @staticmethod
    def __add_parameter_group():
        return rds.DBParameterGroup(
            'AuroraServerlessParameterGroup',
            Description="Aurora serverless parameters group",
            Family="aurora5.6",
            Parameters={
                'slow_query_log': '1',
                'long_query_time': '5',
                'log_output': 'FILE'}
        )

    @staticmethod
    def __scaling_configuration():
        return rds.ScalingConfiguration(
            AutoPause=True,
            MaxCapacity=2,
            MinCapacity=2,
            SecondsUntilAutoPause=300
        )

    def __add_rds(self):
        # database_parameter_group = self.__add_parameter_group()
        # self._template.add_resource(database_parameter_group)

        database_subnet_group = self.__add_database_subnet_group()
        self._template.add_resource(database_subnet_group)

        database_name = self.sceptre_user_data.get('DatabaseName')

        db_cluster = rds.DBCluster(self.__db_cluster_name)
        db_cluster.BackupRetentionPeriod = 1
        db_cluster.DatabaseName = database_name
        db_cluster.DBClusterIdentifier = Ref(self.__db_cluster_identifier)
        # db_cluster.DBClusterParameterGroupName = Ref(database_parameter_group)
        db_cluster.DBSubnetGroupName = Ref(database_subnet_group)
        db_cluster.DeletionProtection = False
        db_cluster.Engine = "aurora"
        db_cluster.EngineMode = "serverless"
        db_cluster.EngineVersion = "5.6.10a"
        db_cluster.MasterUsername = Ref(self.__master_user_name)
        db_cluster.MasterUserPassword = Ref(self.__master_user_password)
        db_cluster.Port = 3306
        db_cluster.ScalingConfiguration = self.__scaling_configuration()
        db_cluster.VpcSecurityGroupIds = [Ref(self.__security_group_id)]
        self._template.add_resource(db_cluster)

    def __add_outputs(self):
        self._template.add_output(
            Output(
                "DatabaseAddress",
                Value=GetAtt(self.__db_cluster_name, "Endpoint.Address"),
                Export=Export(Join("-", [StackName, "endpoint"]))

            )
        )
        self._template.add_output(
            Output(
                "DatabasePort",
                Value=GetAtt(self.__db_cluster_name, "Endpoint.Port"),
                Export=Export(Join("-", [StackName, "port"]))

            )
        )

def sceptre_handler(sceptre_user_data):
    aurora_serverless = AuroraServerless(sceptre_user_data)
    return aurora_serverless._template.to_json()


if __name__ == '__main__':
    print(sceptre_handler(""))
