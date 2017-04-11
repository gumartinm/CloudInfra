#
# Run python SimpleTemplate.py
#

from troposphere import Parameter, Template, Ref, Tags
import troposphere.ec2 as ec2

t = Template(Description='Simple template example with one instance')

t.add_parameter(Parameter(
    'KeyName',
    Type='AWS::EC2::KeyPair::KeyName',
    ConstraintDescription='must be the name of an existing EC2 KeyPair.',
    Description=('Name of an existing EC2 KeyPair to enable SSH '
                 'access to the instance')
))

instance = ec2.Instance('SimpleServerInstance')
instance.DisableApiTermination = False
instance.InstanceInitiatedShutdownBehavior = 'stop'
instance.ImageId = 'ami-ae0937c8'
instance.InstanceType = 'm3.large'
instance.KernelId = 'aki-dc9ed9af'
instance.KeyName = Ref('KeyName')
instance.Monitoring = False
instance.Tags = Tags(Name='instanceGUS')

network_interfaces = []
network_interface = ec2.NetworkInterfaceProperty()
network_interface.DeleteOnTermination = True
network_interface.Description = 'GUS Network Interface'
network_interface.DeviceIndex = '0'
network_interface.SubnetId = Ref('subnetgus')

ip_address_specification = ec2.PrivateIpAddressSpecification()
network_interface.PrivateIpAddresses = [
    ec2.PrivateIpAddressSpecification(
        Primary=True,
        PrivateIpAddress='192.168.97.30')
]
network_interface.GroupSet = Ref('securitygroupgus')
network_interface.AssociatePublicIpAddress = True
network_interfaces.append(network_interface)
instance.NetworkInterfaces = network_interfaces
t.add_resource(instance)


vpc = ec2.VPC('vpcgus')
vpc.CidrBlock = '192.168.96.0/22'
vpc.InstanceTenancy = 'default'
vpc.EnableDnsSupport = True
vpc.EnableDnsHostnames = True
vpc.Tags = Tags(Name='VPC GUS')
t.add_resource(vpc)

subnet = ec2.Subnet('subnetgus')
subnet.CidrBlock = '192.168.97.0/26'
subnet.AvailabilityZone = 'eu-west-1a'
subnet.VpcId = 'vpcgus'
subnet.Tags = Tags(Name='PublicGUS')
t.add_resource(subnet)

security_group = ec2.SecurityGroup('securitygroupgus')
security_group.GroupDescription = 'default VPC security group'
security_group.VpcId = Ref('vpcgus')
security_group.Tags = Tags(Name='SecurityGroup GUS')
t.add_resource(security_group)

ingress_ssh = ec2.SecurityGroupIngress('ingressSSH')
ingress_ssh.GroupId = Ref('securitygroupgus')
ingress_ssh.IpProtocol = 'tcp'
ingress_ssh.FromPort = '22'
ingress_ssh.ToPort = '22'
ingress_ssh.CidrIp = 'YOUR.IP.V4.ADDRES/32'
t.add_resource(ingress_ssh)

print(t.to_json())
