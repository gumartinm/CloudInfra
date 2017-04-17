#!/usr/bin/python
# coding: utf-8
#
# troposhpere does not seem to work with python 3 :(
#
# Run: python SimpleTemplate.py
# Debug: python -m pdb SimpleTemplate.py
#

from troposphere import Parameter, Template, Ref, Tags, Output, GetAtt
import troposphere.ec2 as ec2
import troposphere.sqs as sqs
import troposphere.sns as sns

t = Template(Description='Simple template example with one instance')
t.AWSTemplateFormatVersion = '2010-09-09'


keyname = t.add_parameter(
            Parameter(
                'KeyName',
                Type='AWS::EC2::KeyPair::KeyName',
                ConstraintDescription=('must be the name of an existing EC2 '
                                       'KeyPair.'),
                Description=('Name of an existing EC2 KeyPair to enable SSH '
                             'access to the instance')
            )
        )


vpc = t.add_resource(
        ec2.VPC(
            'vpcgus',
            CidrBlock='192.168.96.0/22',
            InstanceTenancy='default',
            EnableDnsSupport=True,
            EnableDnsHostnames=True,
            Tags=Tags(Name='VPC GUS')
        )
    )


subnet = t.add_resource(
            ec2.Subnet(
                'subnetgus',
                CidrBlock='192.168.97.0/26',
                AvailabilityZone='eu-west-1a',
                VpcId=Ref(vpc),
                Tags=Tags(Name='PublicGUS')
            )
        )


queue = t.add_resource(
            sqs.Queue(
                'QueueGus',
                QueueName='QueueGus',
                DelaySeconds=0,
                # Long polling. See: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-long-polling.html#sqs-long-polling-console
                # 20 seconds
                ReceiveMessageWaitTimeSeconds=20,
                # 256KiB (bytes)
                MaximumMessageSize=262144,
                # 30 seconds
                VisibilityTimeout=30,
                # 14 days (seconds)
                MessageRetentionPeriod=1209600
            )
        )


topic = t.add_resource(
        sns.Topic(
            'gussnstopic',
            # Required when using SMS
            DisplayName='gussnstopic',
            TopicName='gussnstopic',
            Subscription=[
                sns.Subscription(
                    Endpoint=GetAtt(queue, "Arn"),
                    Protocol='sqs'
                )
            ]
        )
    )


t.add_resource(
    sns.TopicPolicy(
        'TopicPolicyGus',
        Topics=[Ref(topic)],
        PolicyDocument={
            "Version": "2008-10-17",
            "Id": "TopicPolicyGusPolicyDocumentId",
            "Statement": [
                {
                    "Sid": "Allow-OnlyOwner-SubscriptAndPublic-To-Topic",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": [
                        "SNS:GetTopicAttributes",
                        "SNS:SetTopicAttributes",
                        "SNS:AddPermission",
                        "SNS:RemovePermission",
                        "SNS:DeleteTopic",
                        "SNS:Subscribe",
                        "SNS:ListSubscriptionsByTopic",
                        "SNS:Publish",
                        "SNS:Receive"
                    ],
                    "Resource": Ref(topic),
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceOwner": "ACCOUNT-ID"
                        }
                    }
                }
            ]
        }
    )
)


t.add_resource(
    sqs.QueuePolicy(
        'QueuePolicyGus',
        Queues=[Ref(queue)],
        PolicyDocument={
            "Version": "2012-10-17",
            "Id": "QueuePolicyGusPolicyDocumentId",
            "Statement": [
                {
                    "Sid": "Allow-SendMessage-FromTopic",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "SQS:SendMessage",
                    "Resource": GetAtt(queue, "Arn"),
                    "Condition": {
                        "ArnEquals": {
                            "aws:SourceArn": Ref(topic)
                        }
                    }
                },
                {
                    "Sid": "Allow-Everything-FromEverywhere",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "SQS:*",
                    "Resource": GetAtt(queue, "Arn")
                }
            ]
        }
    )
)


security_group = t.add_resource(
                    ec2.SecurityGroup(
                        'securitygroupgus',
                        GroupDescription='default VPC security group',
                        VpcId=Ref(vpc),
                        Tags=Tags(Name='SecurityGroup GUS')
                    )
                )


t.add_resource(
    ec2.SecurityGroupIngress(
        'ingressSSH',
        GroupId=Ref(security_group),
        IpProtocol='tcp',
        FromPort='22',
        ToPort='22',
        CidrIp='YOUR.IP.V4.ADDRES/32'
    )
)


instance = ec2.Instance('SimpleServerInstance')
instance.DisableApiTermination = False
instance.InstanceInitiatedShutdownBehavior = 'stop'
instance.ImageId = 'ami-ae0937c8'
instance.InstanceType = 'm3.large'
instance.KernelId = 'aki-dc9ed9af'
instance.KeyName = Ref(keyname)
instance.Monitoring = False
instance.Tags = Tags(Name='instanceGUS')
instance.NetworkInterfaces = [
    ec2.NetworkInterfaceProperty(
        DeleteOnTermination=True,
        Description='GUS Network Interface',
        DeviceIndex='0',
        SubnetId=Ref(subnet),
        PrivateIpAddresses=[
            ec2.PrivateIpAddressSpecification(
                Primary=True,
                PrivateIpAddress='192.168.97.30'
            )
        ],
        GroupSet=[
            Ref(security_group)
        ],
        AssociatePublicIpAddress=True
    )
]
t.add_resource(instance)


t.add_output([
    Output(
        "QueueURL",
        Description="URL of SQS Queue",
        Value=Ref(queue)
    ),
    Output(
        "QueueARN",
        Description="ARN of SQS Queue",
        Value=GetAtt(queue, "Arn")
    ),
    Output(
        "QueueName",
        Description="Name of SQS Queue",
        Value=GetAtt(queue, "QueueName")
    )
])

print(t.to_json())
