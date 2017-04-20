#!/usr/bin/python
# coding: utf-8
#
# troposhpere does not seem to work with python 3 :(
#
# Run: python SimpleTemplate.py
# Debug: python -m pdb SimpleTemplate.py
#

from troposphere import Parameter, Template, Ref, Tags, Output, GetAtt, Export
from troposphere.awslambda import Function, Code, Environment
import troposphere.iam as iam
import troposphere.ec2 as ec2
import troposphere.sqs as sqs
import troposphere.sns as sns

t = Template(Description='Simple template example with lambdas')
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
            'VPCGus',
            CidrBlock='192.168.96.0/22',
            InstanceTenancy='default',
            EnableDnsSupport=True,
            EnableDnsHostnames=True,
            Tags=Tags(Name='VPC GUS')
        )
    )


subnet = t.add_resource(
            ec2.Subnet(
                'SubnetGus',
                CidrBlock='192.168.97.0/26',
                AvailabilityZone='eu-west-1a',
                VpcId=Ref(vpc),
                Tags=Tags(Name='PublicGUS')
            )
        )

role = t.add_resource(
    iam.Role(
        'GusLambdaRole',
        RoleName='GusLambdaRole',
        # Trust relationships
        AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        },
        Path='/gus-lambda/',
        # Permissions
        # Managed Policies
        ManagedPolicyArns=[
            'arn:aws:iam::aws:policy/AmazonSQSFullAccess',
            'arn:aws:iam::aws:policy/AWSLambdaFullAccess',
            'arn:aws:iam::aws:policy/AWSLambdaExecute',
            ('arn:aws:iam::aws:policy/service-role/'
             'AWSLambdaVPCAccessExecutionRole'),
        ],
        # Inline Policies
        Policies=[
            iam.Policy(
                PolicyName='gus-inline-policy',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ec2:CreateNetworkInterface",
                                "ec2:DeleteNetworkInterface",
                                "ec2:DescribeNetworkInterfaces"
                            ],
                            "Resource": "*"
                        }
                    ]
                }
            )
        ]
    )
)


foobar_function = t.add_resource(
    Function(
        "GusLambdaFunction",
        Description='aws-lambda-gus-example',
        FunctionName='aws-lambda-gus-example',
        # size 320MB
        MemorySize='320',
        Environment=Environment(
            Variables={'ENVIRONMENT_GUS': 'GUSTAVO'}
        ),
        Code=Code(
            S3Bucket='guslambda',
            S3Key='aws-example-lambda-1.0-SNAPSHOT-jar-with-dependencies.jar'
        ),
        # time out 15 seconds
        Timeout=15,
        Handler='de.aws.example.lambda.AWSLambdaExample',
        Role=GetAtt('GusLambdaRole', 'Arn'),
        Runtime='Java 8',
    )
)


security_group = t.add_resource(
                    ec2.SecurityGroup(
                        'SecurityGroupGus',
                        GroupDescription='default VPC security group',
                        VpcId=Ref(vpc),
                        Tags=Tags(Name='SecurityGroup GUS')
                    )
                )


t.add_resource(
    ec2.SecurityGroupIngress(
        'IngressSSH',
        GroupId=Ref(security_group),
        IpProtocol='tcp',
        FromPort='22',
        ToPort='22',
        CidrIp='YOUR.IP.V4.ADDRES/32'
    )
)


print(t.to_json())
