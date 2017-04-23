#!/usr/bin/python
# coding: utf-8
#
# troposhpere does not seem to work with python 3 :(
#
# Run: python SimpleTemplate.py
# Debug: python -m pdb SimpleTemplate.py
#

from troposphere import Parameter, Template, Ref, Tags, GetAtt
from troposphere.awslambda import Function, Code, Environment, VPCConfig
from troposphere.awslambda import DeadLetterConfig, Version, Alias
import troposphere.iam as iam
import troposphere.ec2 as ec2
import troposphere.sqs as sqs

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

queue = t.add_resource(
            sqs.Queue(
                'DLQLambdaQueue',
                QueueName='DLQLambdaQueue',
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
            'arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess',
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


lambda_function = t.add_resource(
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
        Runtime='java8',
        DeadLetterConfig=DeadLetterConfig(
            TargetArn=GetAtt(queue, "Arn")
        ),
        VpcConfig=VPCConfig(
            SecurityGroupIds=[
                'sg-XXXXXX'
            ],
            SubnetIds=[
                'subnet-XXXXXXXX',
                'subnet-YYYYYYYY'
            ]
        )
    )
)

# It will create the aws-lambda-gus-example version 1
# We can not choose the version numbers. They are automaticaly created
# by Amazon.
# Lambda version: 1 (the number is given by Amazon)
t.add_resource(
    Version(
        'LambdaVersion1',
        Description='Lambda Version 1',
        FunctionName=Ref(lambda_function)
    )
)


# First change set (adding new values to our cloudformation)
# New lambda version: 2
t.add_resource(
    Version(
        'LambdaVersion2',
        Description='Lambda Version 2',
        FunctionName=Ref(lambda_function)
    )
)
# Modificate template in order to create alias for version 1.
t.add_resource(
    Alias(
        'LambdaAlias',
        Name=Ref(lambda_function),
        Description='Lambda Alias 1',
        FunctionName=Ref(lambda_function),
        # Amazon will give the version 1 to the first created LambdaVersion1.
        # So, we know what number to choose here :)
        FunctionVersion='1'
    )
)


print(t.to_json())
