#!/usr/bin/python
# coding: utf-8
#
# Run: python SimpleTemplate.py
# Debug: python -m pdb SimpleTemplate.py
#

from troposphere import Parameter, Template, Ref
from troposphere.constants import M3_XLARGE
import troposphere.emr as emr


t = Template(Description='EMR Instance Group')
t.AWSTemplateFormatVersion = '2010-09-09'


key_name = t.add_parameter(
            Parameter(
                'KeyName',
                Type='AWS::EC2::KeyPair::KeyName',
                ConstraintDescription=('must be the name of an existing '
                                       'KeyPair.'),
                Description='Name of an existing KeyPair to enable SSH'
            )
        )


additional_master_security_group = t.add_parameter(
            Parameter(
                'AdditionalMasterSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )

master_security_group = t.add_parameter(
            Parameter(
                'MasterSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )

additional_slave_security_group = t.add_parameter(
            Parameter(
                'AdditionalSlaveSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )

slave_security_group = t.add_parameter(
            Parameter(
                'SlaveSecurityGroup',
                Type='AWS::EC2::SecurityGroup::Id',
                ConstraintDescription='must be the id of an existing security group.',
                Description='Id of an existing security group '
            )
        )

ec2_subnet_id = t.add_parameter(
            Parameter(
                'EC2SubnetId',
                Type='AWS::EC2::Subnet::Id',
                ConstraintDescription='must be the id of an existing subnet.',
                Description='Id of an existing subnet '
            )
        )

ec2_instance_profile_role = t.add_parameter(
            Parameter(
                'EC2InstanceProfileIamRole',
                Type='String',
                ConstraintDescription='must be EMR_EC2_DefaultRole',
                Description='IAM Role EMR_EC2_DefaultRole ',
                Default='EMR_EC2_DefaultRole'
            )
        )

emr_role = t.add_parameter(
            Parameter(
                'EMRRole',
                Type='String',
                ConstraintDescription='must be EMR_DefaultRole',
                Description='IAM Role EMR_DefaultRole ',
                Default='EMR_DefaultRole'
            )
        )

emr_autoscaling_role = t.add_parameter(
            Parameter(
                'EMRAutoScalingRole',
                Type='String',
                ConstraintDescription='must be EMR_AutoScaling_DefaultRole',
                Description='IAM Role EMR_AutoScaling_DefaultRole ',
                Default='EMR_AutoScaling_DefaultRole'
            )
        )

release_label = t.add_parameter(
            Parameter(
                'ReleaseLabel',
                Type='String',
                ConstraintDescription='must be EMR release label',
                Description='EMR release label ',
                Default='emr-5.23.0'
            )
        )

emr_log_uri = t.add_parameter(
            Parameter(
                'EMRLogUri',
                Type='String',
                ConstraintDescription='must be S3 bucket',
                Description='EMR log URI '
            )
        )

cluster = emr.Cluster('GusInstanceGroupCloudFormation')
cluster.Name = 'Gus InstanceGroup CloudFormation'
cluster.LogUri = Ref(emr_log_uri)
cluster.ReleaseLabel = Ref(release_label)
cluster.JobFlowRole = Ref(ec2_instance_profile_role)
cluster.ServiceRole = Ref(emr_role)
cluster.VisibleToAllUsers = True
cluster.Applications = [
    emr.Application(
        Name='Hadoop'
    ),
    emr.Application(
        Name='Pig'
    ),
    emr.Application(
        Name='Spark'
    ),
    emr.Application(
        Name='Livy'
    ),
    emr.Application(
        Name='Ganglia'
    )
]
cluster.Configurations = [
    emr.Configuration(
        Classification="emrfs-site",
        ConfigurationProperties={
            "fs.s3.consistent": "true",
            "fs.s3.consistent.metadata.tableName": "GusInstanceGroupEmrFSMetadata",
            "fs.s3.consistent.retryCount": "5",
            "fs.s3.consistent.retryPeriodSeconds": "10",
            "fs.s3.consistent.notification.CloudWatch": "true",
            "fs.s3.consistent.notification.SQS": "true",
            "fs.s3.consistent.notification.SQS.queueName": "GusInstanceGroupEmrFSMetadata"
        }
    )
]
cluster.AutoScalingRole = Ref(emr_autoscaling_role)
cluster.ScaleDownBehavior = "TERMINATE_AT_TASK_COMPLETION"
cluster.EbsRootVolumeSize = 10
cluster.Instances = emr.JobFlowInstancesConfig(
    AdditionalMasterSecurityGroups=[
        Ref(additional_master_security_group)
    ],
    AdditionalSlaveSecurityGroups=[
        Ref(additional_slave_security_group)
    ],
    Ec2KeyName=Ref(key_name),
    Ec2SubnetId=Ref(ec2_subnet_id),
    EmrManagedMasterSecurityGroup=Ref(master_security_group),
    EmrManagedSlaveSecurityGroup=Ref(slave_security_group),
    KeepJobFlowAliveWhenNoSteps=True,
    TerminationProtected=False,
    MasterInstanceGroup=emr.InstanceGroupConfigProperty(
        "MasterInstanceGroup",
        Name="Master Instance Group",
        InstanceCount="1",
        InstanceType=M3_XLARGE,
        Market="SPOT"
    ),
    CoreInstanceGroup=emr.InstanceGroupConfigProperty(
        "CoreInstanceGroup",
        Name="Core Instance Group",
        Market="SPOT",
        InstanceType=M3_XLARGE,
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
)
t.add_resource(cluster)

instance_group_config = emr.InstanceGroupConfig(
    'TaskInstanceGroup',
    Name="Task Instance Group",
    JobFlowId=Ref(cluster),
    InstanceCount=0,
    InstanceType=M3_XLARGE,
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
t.add_resource(instance_group_config)

print(t.to_json())
