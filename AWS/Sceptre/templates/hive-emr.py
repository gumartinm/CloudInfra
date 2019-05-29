#!/usr/bin/python
# coding: utf-8
#

from troposphere import Parameter, Template, Ref, Join, Output, GetAtt, Export, StackName
from troposphere.constants import M5_2XLARGE
import troposphere.emr as emr


class HiveEMRInstanceGroup(object):

    def __init__(self, sceptre_user_data):
        self._template = Template(Description='Hive EMR Instance Group')
        self._template.AWSTemplateFormatVersion = '2010-09-09'
        self.sceptre_user_data = sceptre_user_data
        self.__add_arguments()
        self.__add_emr()
        self.__add_outputs()

    def __add_arguments(self):
        self.project = self._template.add_parameter(Parameter(
            "Project",
            Type="String",
            Description="Project Name",
            MinLength="1",
            MaxLength="255",
            Default='Hive EMR Instance Group',
            AllowedPattern="[\\x20-\\x7E]*",
            ConstraintDescription="can contain only ASCII characters.",
        ))
        self.__key_name = self._template.add_parameter(
            Parameter(
                'KeyName',
                Type='AWS::EC2::KeyPair::KeyName',
                ConstraintDescription=('must be the name of an existing '
                                       'KeyPair.'),
                Description='Name of an existing KeyPair to enable SSH'
            )
        )
        self.__additional_master_security_group = self._template.add_parameter(
            Parameter(
                'AdditionalMasterSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )
        self.__master_security_group = self._template.add_parameter(
            Parameter(
                'MasterSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )
        self.__additional_slave_security_group = self._template.add_parameter(
            Parameter(
                'AdditionalSlaveSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )
        self.__slave_security_group = self._template.add_parameter(
            Parameter(
                'SlaveSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )
        self.__ec2_subnet_id = self._template.add_parameter(
            Parameter(
                'EC2SubnetId',
                Type='AWS::EC2::Subnet::Id',
                ConstraintDescription='must be the id of an existing subnet.',
                Description='Id of an existing subnet '
            )
        )
        self.__ec2_instance_profile_role = self._template.add_parameter(
            Parameter(
                'EC2InstanceProfileRole',
                Type='String',
                ConstraintDescription='must be EMR_EC2_DefaultRole',
                Description='IAM Role EMR_EC2_DefaultRole ',
                Default='EMR_EC2_DefaultRole'
            )
        )
        self.__emr_role = self._template.add_parameter(
            Parameter(
                'EMRRole',
                Type='String',
                ConstraintDescription='must be EMR_DefaultRole',
                Description='IAM Role EMR_DefaultRole ',
                Default='EMR_DefaultRole'
            )
        )
        self.__emr_autoscaling_role = self._template.add_parameter(
            Parameter(
                'EMRAutoScalingRole',
                Type='String',
                ConstraintDescription='must be EMR_AutoScaling_DefaultRole',
                Description='IAM Role EMR_AutoScaling_DefaultRole ',
                Default='EMR_AutoScaling_DefaultRole'
            )
        )
        self.__release_label = self._template.add_parameter(
            Parameter(
                'ReleaseLabel',
                Type='String',
                ConstraintDescription='must be EMR release label',
                Description='EMR release label ',
                Default='emr-5.23.0'
            )
        )
        self.__emr_log_uri = self._template.add_parameter(
            Parameter(
                'EMRLogUri',
                Type='String',
                ConstraintDescription='must be S3 bucket',
                Description='EMR log URI '
            )
        )
        self.__database_address = self._template.add_parameter(
            Parameter(
                'DatabaseAddress',
                Type='String',
                ConstraintDescription='IP address or hostname for database',
                Description='IP address or hostname for database '
            )
        )
        self.__database_port = self._template.add_parameter(
            Parameter(
                'DatabasePort',
                Type='String',
                ConstraintDescription='TCP port for database',
                Description='TCP port for database '
            )
        )
        self.__database_password = self._template.add_parameter(
            Parameter(
                'DatabasePassword',
                Type='String',
                ConstraintDescription='password for data base.',
                Description='Password for data base ',
                NoEcho=True
            )
        )
        self.__database_user_name = self._template.add_parameter(
            Parameter(
                'DatabaseUserName',
                Type='String',
                ConstraintDescription='user name for data base',
                Description='User name for data base '
            )
        )

    def __add_emr(self):
        hive_external_metastore_conf = emr.Configuration()
        hive_external_metastore_conf.Classification = "hive-site"
        hive_external_metastore_conf.ConfigurationProperties = {
            "javax.jdo.option.ConnectionURL": Join("", ["jdbc:mysql://",
                                                        Ref(self.__database_address), ":",
                                                        Ref(self.__database_port),
                                                        "/hive?createDatabaseIfNotExist=true"]),
            "javax.jdo.option.ConnectionDriverName": "org.mariadb.jdbc.Driver",
            "javax.jdo.option.ConnectionUserName": Ref(self.__database_user_name),
            "javax.jdo.option.ConnectionPassword": Ref(self.__database_password)
        }

        hive_env_configuration = emr.Configuration()
        hive_env_configuration.Classification = "hive-env"
        hive_env_configuration.Configurations = [
            emr.Configuration(
                Classification="export",
                ConfigurationProperties={
                    "HADOOP_HEAPSIZE": "10240"
                }
            )
        ]

        cluster = emr.Cluster('HiveEMR')
        cluster.Name = 'HiveEMR'
        cluster.LogUri = Ref(self.__emr_log_uri)
        cluster.ReleaseLabel = Ref(self.__release_label)
        cluster.JobFlowRole = Ref(self.__ec2_instance_profile_role)
        cluster.ServiceRole = Ref(self.__emr_role)
        cluster.VisibleToAllUsers = True
        cluster.Applications = [
            emr.Application(
                Name='Ganglia'
            ),
            emr.Application(
                Name='Hive'
            )
        ]
        cluster.Configurations = [
            hive_external_metastore_conf,
            hive_env_configuration
        ]
        cluster.AutoScalingRole = Ref(self.__emr_autoscaling_role)
        cluster.ScaleDownBehavior = "TERMINATE_AT_TASK_COMPLETION"
        cluster.EbsRootVolumeSize = 10
        cluster.Instances = emr.JobFlowInstancesConfig(
            AdditionalMasterSecurityGroups=[
                Ref(self.__additional_master_security_group)
            ],
            AdditionalSlaveSecurityGroups=[
                Ref(self.__additional_slave_security_group)
            ],
            Ec2KeyName=Ref(self.__key_name),
            Ec2SubnetId=Ref(self.__ec2_subnet_id),
            EmrManagedMasterSecurityGroup=Ref(self.__master_security_group),
            EmrManagedSlaveSecurityGroup=Ref(self.__slave_security_group),
            KeepJobFlowAliveWhenNoSteps=True,
            TerminationProtected=False,
            MasterInstanceGroup=emr.InstanceGroupConfigProperty(
                "MasterInstanceGroup",
                Name="Master Instance Group",
                InstanceCount="1",
                InstanceType=M5_2XLARGE,
                Market="ON_DEMAND"
            )
        )
        self._template.add_resource(cluster)

    def __add_outputs(self):
        self._template.add_output(
            Output(
                "HiveEMRAddress",
                Value=GetAtt("HiveEMR", "MasterPublicDNS"),
                Export=Export(Join("-", [StackName, "address"]))

            )
        )

def sceptre_handler(sceptre_user_data):
    emr_instance_group = HiveEMRInstanceGroup(sceptre_user_data)
    return emr_instance_group._template.to_json()


if __name__ == '__main__':
    print(sceptre_handler(""))
