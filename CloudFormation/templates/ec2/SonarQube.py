#!/usr/bin/python
# coding: utf-8
#
# troposhpere does not seem to work with python 3 :(
#
# Run: python SonarQube.py
# Debug: python -m pdb SonarQube.py
#

from troposphere import Parameter, Template, Ref, Tags, Select, GetAZs, Join, Output, GetAtt, Base64
from troposphere.iam import InstanceProfile, Role
from troposphere import cloudformation
from troposphere.rds import DBInstance, DBParameterGroup
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
db_user = t.add_parameter(
            Parameter(
                'DBUser',
                NoEcho=True,
                Type='String',
                MinLength=1,
                MaxLength=16,
                AllowedPattern='[a-zA-Z][a-zA-Z0-9]*',
                ConstraintDescription=('Must begin with a letter and contain only alphanumeric characters.'),
                Description=('The database admin account username')
            )
        )
db_password = t.add_parameter(
            Parameter(
                'DBPassword',
                NoEcho=True,
                Type='String',
                MinLength=8,
                MaxLength=41,
                AllowedPattern='[a-zA-Z0-9]*',
                ConstraintDescription=('Must contain only alphanumeric characters.'),
                Description=('The database admin account password')
            )
        )
db_name = t.add_parameter(
        Parameter(
             'DBName',
             Default='sonarqube',
             Description='The database name',
             Type='String',
             MinLength=1,
             MaxLength=64,
             AllowedPattern='[a-zA-Z][a-zA-Z0-9]*',
             ConstraintDescription=('must begin with a letter and contain only'
                                    ' alphanumeric characters.')
        )
    )


db_backup_retention = t.add_parameter(
            Parameter(
                'DBBackupRetention',
                Default='31',
                Type='Number',
                MinValue=31,
                MaxValue=365,
                ConstraintDescription=('Days between 31 and 365.'),
                Description=('Days backups will be stored.')
            )
        )

db_storage_size = t.add_parameter(
            Parameter(
                'DBStorageSize',
                Default='10',
                Type='Number',
                MinValue=10,
                MaxValue=30,
                ConstraintDescription=('Value between 10Gb and 30Gb'),
                Description=('Database size in Gb')
            )
        )



# See: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.html#Appendix.PostgreSQL.CommonDBATasks.Parameters
db_parameters = t.add_resource(
                    DBParameterGroup(
                        'DBParamGroup',
                         Family='postgres9.6',
                         Description='Database Parameter Group',
                         Parameters={
                            'application_name': 'SonarQube'
                         }
                    )
            )

sonarqube_instance_profile = InstanceProfile(
                                "SonarqubeInstanceProfile",
                                Path='/',
                                Roles=['AdminEC2']
                            )
t.add_resource(sonarqube_instance_profile)

# See: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html
database = t.add_resource(
            DBInstance(
                'SonarQubeDatabase',
                DBName=Ref(db_name),
                Engine='postgres',
                EngineVersion='9.6',
                StorageType='gp2',
                MasterUsername=Ref(db_user),
                MasterUserPassword=Ref(db_password),
                AllocatedStorage=Ref(db_storage_size),
                DBInstanceClass='db.m3.xlarge',
                PreferredBackupWindow='02:00-04:00',
                PreferredMaintenanceWindow='Mon:04:00-Mon:08:00',
                BackupRetentionPeriod=Ref(db_backup_retention),
                AutoMinorVersionUpgrade=True,
                PubliclyAccessible=False,
                DBParameterGroupName=Ref(db_parameters)
            )
        )
t.add_output(Output(
    'JDBCConnectionString',
    Description='JDBC connection string for database',
    Value=Join('', [
                'jdbc:postgresql://',
                GetAtt(database, 'Endpoint.Address'),
                ':',
                GetAtt(database, 'Endpoint.Port'),
                '/',
                Ref(db_name)
            ])
        ))


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
                    'command': 'unzip ' + SONARQUBE_PATH + '/opt/sonarqube/'
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
        GroupSet=[
            Ref(security_group)
        ],
        AssociatePublicIpAddress=False
    )
]
instance.UserData = Base64(Join('', [
                            "",
                            [
                                "#!/bin/bash -xe\n",
                                "yum install -y aws-cfn-bootstrap\n",
                                "/opt/aws/bin/cfn-init -v ",
                                "         --stack ",
                                {
                                    "Ref": "AWS::StackName"
                                },
                                "         --resource SonarQubeInstance ",
                                "         --region ",
                                {
                                    "Ref": "AWS::Region"
                                },
                                "\n"
                            ]]
                        )
                    )

instance.IamInstanceProfile = Ref(sonarqube_instance_profile)
instance.Metadata = metadata

t.add_resource(instance)


print(t.to_json())
