#!/usr/bin/python
# coding: utf-8
#
# troposhpere does not seem to work with python 3 :(
#
# Run: python SonarQube.py
# Debug: python -m pdb SonarQube.py
#

from troposphere import Parameter, Template, Ref, Tags, Select, GetAZs, Join
from troposphere import cloudformation
import troposphere.ec2 as ec2

SONARQUBE_PATH = '/opt/sonarqube/sonarqube.zip'


t = Template(Description='SonarQube instance')
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

your_ip_address = t.add_parameter(
            Parameter(
                'YourIpAddress',
                Type='String',
                MinLength='9',
                MaxLength='18',
                Default='127.0.0.1/32',
                AllowedPattern="(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})",
                ConstraintDescription=('must be your IPv4 address'),
                Description=('your IPv4 address')
            )
        )

sonarqube_download_url = t.add_parameter(
            Parameter(
                'SonarQubeDownloadURL',
                Type='String',
                Default='https://sonarsource.bintray.com/Distribution/sonarqube/sonarqube-6.7.1.zip',
                ConstraintDescription=('SonarQube download URL'),
                Description=('SonarQube download URL')
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

availability_zones = GetAZs(Ref('AWS::Region'))
availability_zone = Select('0', availability_zones)
subnet = t.add_resource(
            ec2.Subnet(
                'SubnetGus',
                CidrBlock='192.168.97.0/26',
                AvailabilityZone=availability_zone,
                VpcId=Ref(vpc),
                Tags=Tags(Name='PublicGUS')
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
        CidrIp=Ref(your_ip_address)
    )
)

metadata = cloudformation.Metadata(
    cloudformation.Init(
        cloudformation.InitConfigSets(
            ascending=['config1', 'config2'],
            descending=['config2', 'config1']
        ),
        config1=cloudformation.InitConfig(
            files=cloudformation.InitFiles({
                SONARQUBE_PATH: cloudformation.InitFile(
                    source=Ref(sonarqube_download_url),
                    mode='000664',
                    owner='root',
                    group='root'
                    ),
                '/etc/cfn/cfn-hup.conf': cloudformation.InitFile(
                    content=Join(
                      '',
                      [
                        '[main]\n',
                        'stack=', Ref('AWS::StackId'), '\n',
                        'region=', Ref('AWS::Region'), '\n'
                      ]),
                    mode='000400',
                    owner='root',
                    group='root'
                  )
            }),
            commands={
                '01-unzip-sonarqube': {
                    'command': 'unzip ' + SONARQUBE_PATH
                }
            }
        )
    )
)


instance = ec2.Instance('SonarQubeInstance')
instance.DisableApiTermination = False
instance.InstanceInitiatedShutdownBehavior = 'stop'
instance.ImageId = 'ami-ae0937c8'
instance.InstanceType = 'm3.large'
instance.KernelId = 'aki-dc9ed9af'
instance.KeyName = Ref(keyname)
instance.Monitoring = False
instance.Tags = Tags(Name='sonarQubeInstance')
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
instance.Metadata = metadata

t.add_resource(instance)


print(t.to_json())
