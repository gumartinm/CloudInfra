#!/usr/bin/python
# coding: utf-8
#

from troposphere import Parameter, Template, Output, GetAtt, StackName, Export, Ref, Join
import troposphere.emr as emr


class HBaseInstanceGroup(object):

    def __init__(self, sceptre_user_data):
        self._template = Template(Description='HBase EMR Instance Group')
        self._template.AWSTemplateFormatVersion = '2010-09-09'
        self.sceptre_user_data = sceptre_user_data
        self.__add_arguments()
        self.__add_emr()

    def __add_arguments(self):
        self.project = self._template.add_parameter(Parameter(
            "Project",
            Type="String",
            Description="Project Name",
            MinLength="1",
            MaxLength="255",
            Default='HBASE EMR Instance Group',
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
                Default='emr-5.27.0'
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
        self.__ec2_instance_type = self._template.add_parameter(
            Parameter(
                'EC2InstanceType',
                Type='String',
                ConstraintDescription='EC2 instance type',
                Description='EC2 instance type: https://aws.amazon.com/ec2/instance-types/ '
            )
        )

    def __add_outputs(self):
        self._template.add_output(
            Output(
                "HBaseEMRAddress",
                Value=GetAtt("HBaseEMR", "MasterPublicDNS"),
                Export=Export(Join("-", [StackName, "address"]))

            )
        )

    def __add_emr(self):
        cluster = emr.Cluster('HBaseEMR')
        cluster.Name = 'HBaseEMR'
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
                Name='HBase'
            )
        ]
        cluster.Configurations = [
            emr.Configuration(
                Classification="hbase-site",
                ConfigurationProperties={
                    "hbase.rootdir": "s3://gumartinm-hbase/"
                }
            ),
            emr.Configuration(
                Classification="hbase",
                ConfigurationProperties={
                    "hbase.emr.storageMode": "s3"
                }
            ),
            emr.Configuration(
                Classification="emrfs-site",
                ConfigurationProperties={
                    "fs.s3.consistent": "true",
                    "fs.s3.consistent.metadata.tableName": "HBaseInstanceGroupEmrFSMetadata",
                    "fs.s3.consistent.retryCount": "5",
                    "fs.s3.consistent.retryPeriodSeconds": "10",
                    "fs.s3.consistent.notification.CloudWatch": "true",
                    "fs.s3.consistent.metadata.autoCreate": "true",
                    "fs.s3.consistent.notification.SQS": "true"
                }
            )
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
                InstanceCount="3",
                InstanceType=Ref(self.__ec2_instance_type),
                Market="ON_DEMAND"
            ),
            CoreInstanceGroup=emr.InstanceGroupConfigProperty(
                "CoreInstanceGroup",
                Name="Core Instance Group",
                Market="SPOT",
                InstanceType=Ref(self.__ec2_instance_type),
                InstanceCount=2,
                AutoScalingPolicy=emr.AutoScalingPolicy(
                    Constraints=emr.ScalingConstraints(
                        MinCapacity="1",
                        MaxCapacity="2"
                    ),
                    Rules=[
                        emr.ScalingRule(
                            Name='YARNMemory-scale-out',
                            Description='',
                            Action=emr.ScalingAction(
                                SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                    AdjustmentType='CHANGE_IN_CAPACITY',
                                    ScalingAdjustment=1,
                                    CoolDown=300
                                )
                            ),
                            Trigger=emr.ScalingTrigger(
                                CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                    ComparisonOperator="LESS_THAN",
                                    EvaluationPeriods=1,
                                    MetricName="YARNMemoryAvailablePercentage",
                                    Namespace="AWS/ElasticMapReduce",
                                    Period=300,
                                    Statistic="AVERAGE",
                                    Threshold=15,
                                    Unit="PERCENT",
                                    Dimensions=[
                                        emr.MetricDimension(
                                            "JobFlowId", "${emr.clusterId}"
                                        )
                                    ]
                                )
                            )
                        ),
                        emr.ScalingRule(
                            Name='ContainerPending-scale-out',
                            Description='',
                            Action=emr.ScalingAction(
                                SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                    AdjustmentType='CHANGE_IN_CAPACITY',
                                    ScalingAdjustment=1,
                                    CoolDown=300
                                )
                            ),
                            Trigger=emr.ScalingTrigger(
                                CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                    ComparisonOperator="GREATER_THAN",
                                    EvaluationPeriods=1,
                                    MetricName="ContainerPendingRatio",
                                    Namespace="AWS/ElasticMapReduce",
                                    Period=300,
                                    Statistic="AVERAGE",
                                    Threshold=0.75,
                                    Unit="COUNT",
                                    Dimensions=[
                                        emr.MetricDimension(
                                            "JobFlowId", "${emr.clusterId}"
                                        )
                                    ]
                                )
                            )
                        ),
                        emr.ScalingRule(
                            Name='YARNMemory-scale-in',
                            Description='',
                            Action=emr.ScalingAction(
                                SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                    AdjustmentType='CHANGE_IN_CAPACITY',
                                    ScalingAdjustment=-1,
                                    CoolDown=300
                                )
                            ),
                            Trigger=emr.ScalingTrigger(
                                CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                    ComparisonOperator="GREATER_THAN",
                                    EvaluationPeriods=1,
                                    MetricName="YARNMemoryAvailablePercentage",
                                    Namespace="AWS/ElasticMapReduce",
                                    Period=300,
                                    Statistic="AVERAGE",
                                    Threshold=75.0,
                                    Unit="PERCENT",
                                    Dimensions=[
                                        emr.MetricDimension(
                                            "JobFlowId", "${emr.clusterId}"
                                        )
                                    ]
                                )
                            )
                        )
                    ]
                )
            )
        )
        self._template.add_resource(cluster)

        instance_group_config = emr.InstanceGroupConfig(
            'TaskInstanceGroup',
            Name="Task Instance Group",
            JobFlowId=Ref(cluster),
            InstanceCount=0,
            InstanceType=Ref(self.__ec2_instance_type),
            InstanceRole='TASK',
            Market='SPOT',
            AutoScalingPolicy=emr.AutoScalingPolicy(
                Constraints=emr.ScalingConstraints(
                    MinCapacity="1",
                    MaxCapacity="2"
                ),
                Rules=[
                    emr.ScalingRule(
                        Name='YARNMemory-scale-out',
                        Description='',
                        Action=emr.ScalingAction(
                            SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                AdjustmentType='CHANGE_IN_CAPACITY',
                                ScalingAdjustment=1,
                                CoolDown=300
                            )
                        ),
                        Trigger=emr.ScalingTrigger(
                            CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                ComparisonOperator="LESS_THAN",
                                EvaluationPeriods=1,
                                MetricName="YARNMemoryAvailablePercentage",
                                Namespace="AWS/ElasticMapReduce",
                                Period=300,
                                Statistic="AVERAGE",
                                Threshold=15,
                                Unit="PERCENT",
                                Dimensions=[
                                    emr.MetricDimension(
                                        "JobFlowId", "${emr.clusterId}"
                                    )
                                ]
                            )
                        )
                    ),
                    emr.ScalingRule(
                        Name='ContainerPeding-scale-out',
                        Description='',
                        Action=emr.ScalingAction(
                            SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                AdjustmentType='CHANGE_IN_CAPACITY',
                                ScalingAdjustment=1,
                                CoolDown=300
                            )
                        ),
                        Trigger=emr.ScalingTrigger(
                            CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                ComparisonOperator="GREATER_THAN",
                                EvaluationPeriods=1,
                                MetricName="ContainerPendingRatio",
                                Namespace="AWS/ElasticMapReduce",
                                Period=300,
                                Statistic="AVERAGE",
                                Threshold=0.75,
                                Unit="COUNT",
                                Dimensions=[
                                    emr.MetricDimension(
                                        "JobFlowId", "${emr.clusterId}"
                                    )
                                ]
                            )
                        )
                    ),
                    emr.ScalingRule(
                        Name='YARNMemory-scale-in',
                        Description='',
                        Action=emr.ScalingAction(
                            SimpleScalingPolicyConfiguration=emr.SimpleScalingPolicyConfiguration(
                                AdjustmentType='CHANGE_IN_CAPACITY',
                                ScalingAdjustment=-1,
                                CoolDown=300
                            )
                        ),
                        Trigger=emr.ScalingTrigger(
                            CloudWatchAlarmDefinition=emr.CloudWatchAlarmDefinition(
                                ComparisonOperator="GREATER_THAN",
                                EvaluationPeriods=1,
                                MetricName="YARNMemoryAvailablePercentage",
                                Namespace="AWS/ElasticMapReduce",
                                Period=300,
                                Statistic="AVERAGE",
                                Threshold=75.0,
                                Unit="PERCENT",
                                Dimensions=[
                                    emr.MetricDimension(
                                        "JobFlowId", "${emr.clusterId}"
                                    )
                                ]
                            )
                        )
                    )
                ]
            )
        )
        self._template.add_resource(instance_group_config)


def sceptre_handler(sceptre_user_data):
    emr_instance_group = HBaseInstanceGroup(sceptre_user_data)
    return emr_instance_group._template.to_json()


if __name__ == '__main__':
    print(sceptre_handler(""))
