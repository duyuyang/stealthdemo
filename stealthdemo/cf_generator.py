"""
This template is to create a single web tier with elb and auto scaling group.
The stack will be running in an existing VPC with existing subnets, route table, SecurityGroups and NACLs.
Users are required to select the VPC, subnets and security groups as parameters.
Make sure you have a s3 bucket created for elb access logging
By default, the elb is listen on port 80, will forward request to ElbMapToInstancePort as a parameter.
If require mulitple port mapping from load balancer to the instances, create more Listeners in load balancer
This template is using AWS linux AMI with UserData to install ansible and deploy docker containers
"""


from troposphere import FindInMap, Base64, Join, Output, GetAtt, Select
from troposphere import Parameter, Ref, Template
from troposphere import cloudformation, autoscaling
from troposphere.iam import PolicyType, Role, InstanceProfile
from troposphere.autoscaling import AutoScalingGroup, Tag, ScalingPolicy, LaunchConfiguration
from troposphere.elasticloadbalancing import LoadBalancer
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole
from awacs.s3 import GetObject, ListBucket

class ClfGenerator(object):
    def __init__(self):
        self.prefix = "dev"
        self.t = Template()
        self.t.add_version("2010-09-09")
        self.t.add_description("""EC2 instances with LoadBalancer, AutoScalingGroup and SecurityGroups """)
        self.ref_stack_id = Ref('AWS::StackId')
        self.ref_region = Ref('AWS::Region')
        self.ref_stack_name = Ref('AWS::StackName')


    def _add_ami(self, template):
        template.add_mapping("RegionMap", {
            "ap-southeast-2": {"AMI": "ami-ba3e14d9"}
        })


    def _add_parameters(self, template):
        self.instanceType = template.add_parameter(Parameter(
            "InstanceType",
            Type="String",
            Default='t2.micro',
            AllowedValues=[ "t1.micro", "t2.nano", "t2.micro",
                            "t2.small", "t2.medium", "t2.large",
                            "m1.small", "m1.medium", "m1.large",
                            "m1.xlarge", "m2.xlarge", "m2.2xlarge",
                            "m2.4xlarge", "m3.medium", "m3.large",
                            "m3.xlarge", "m3.2xlarge", "m4.large",
                            "c1.medium", "c1.xlarge", "c3.large" ],
            Description="Selection of instance types availabe",
        ))
        self.key_name = template.add_parameter(Parameter(
            "SSHKey",
            Type='AWS::EC2::KeyPair::KeyName',
            Description="Name of an existing EC2 KeyPair to enable SSH access",
            ConstraintDescription="can contain only ASCII characters.",
        ))
        self.public_subnet = template.add_parameter(Parameter(
            "PublicSubnet",
            Type="List<AWS::EC2::Subnet::Id>",
            Description="Public VPC subnet ID for the load balancer.",
        ))

        self.private_subnet = template.add_parameter(Parameter(
            "PrivateSubnet",
            Type="List<AWS::EC2::Subnet::Id>",
            Description="Private VPC subnet ID for the web app.",
        ))

        self.web_port = template.add_parameter(Parameter(
            "ElbMapToInstancePort",
            Type="String",
            Default="80",
            Description="TCP/IP port of the web server",
        ))
        self.scale_capacity_max = template.add_parameter(Parameter(
            "ScaleCapacityMax",
            Default="1",
            Type="String",
            Description="Maximum Number of instances to run",
        ))
        self.scale_capacity_min = template.add_parameter(Parameter(
            "ScaleCapacityMin",
            Default="1",
            Type="String",
            Description="Minimum Number of instances to run",
        ))
        self.scale_capacity_Desire = template.add_parameter(Parameter(
            "ScaleCapacityDesire",
            Default="1",
            Type="String",
            Description="Desired Number of instances to run",
        ))
        self.elb_security_group = template.add_parameter(Parameter(
            "ELBSecurityGroup",
            Type="List<AWS::EC2::SecurityGroup::Id>",
            Description="Security Groups for Load Balancer",
        ))
        self.web_security_group = template.add_parameter(Parameter(
            "InstanceSecurityGroup",
            Type="List<AWS::EC2::SecurityGroup::Id>",
            Description="Security Groups for Web Instances",
        ))


    def _add_resources(self, template):
        self.instance_iam_role = template.add_resource(Role(
            "InstanceIamRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
                    )
                ]
            ),
            Path="/"
        ))

        self.instance_iam_role_instance_profile = template.add_resource(InstanceProfile(
            "InstanceIamRoleInstanceProfile",
            Path="/",
            Roles=[Ref(self.instance_iam_role)]
        ))

        self.loadBalancer = template.add_resource(LoadBalancer(
            "LoadBalancer",
            ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=120,
            ),
            AccessLoggingPolicy=elb.AccessLoggingPolicy(
                EmitInterval=5,
                Enabled=True,
                S3BucketName="duy-logging",
                S3BucketPrefix="ELB",
            ),
            Subnets=Ref(self.public_subnet),
            HealthCheck=elb.HealthCheck(
                Target="HTTP:80/",
                HealthyThreshold="5",
                UnhealthyThreshold="2",
                Interval="20",
                Timeout="15",
            ),
            Listeners=[
                elb.Listener(
                    LoadBalancerPort="80",
                    InstancePort=Ref(self.web_port),
                    Protocol="HTTP",
                    InstanceProtocol="HTTP",
                ),
            ],
            CrossZone=True,
            SecurityGroups=Ref(self.elb_security_group),
            LoadBalancerName="duy%sELB" % self.prefix,
            Scheme="internet-facing",
        ))

        self.launchConfiguration = template.add_resource(LaunchConfiguration(
            "LaunchConfiguration",
            Metadata=autoscaling.Metadata(
                cloudformation.Init({
                    "config": cloudformation.InitConfig(
                        files=cloudformation.InitFiles({
                            '/etc/cfn/cfn-hup.conf': cloudformation.InitFile(content=Join('',
                                                                           ['[main]\n',
                                                                            'stack=',
                                                                            self.ref_stack_id,
                                                                            '\n',
                                                                            'region=',
                                                                            self.ref_region,
                                                                            '\n',
                                                                            ]),
                                                              mode='000400',
                                                              owner='root',
                                                              group='root'),
                            '/etc/cfn/hooks.d/cfn-auto-reloader.conf': cloudformation.InitFile(
                                content=Join('',
                                             ['[cfn-auto-reloader-hook]\n',
                                              'triggers=post.update\n',
                                              'path=Resources.WebServerInstance.\
            Metadata.AWS::CloudFormation::Init\n',
                                              'action=/opt/aws/bin/cfn-init -v ',
                                              '         --stack ',
                                              self.ref_stack_name,
                                              '         --resource WebServerInstance ',
                                              '         --region ',
                                              self.ref_region,
                                              '\n',
                                              'runas=root\n',
                                              ]))}),
                        services={
                            "sysvinit": cloudformation.InitServices({
                                "rsyslog": cloudformation.InitService(
                                    enabled=True,
                                    ensureRunning=True,
                                    files=['/etc/rsyslog.d/20-somethin.conf']
                                )
                            })
                        }
                    )
                })
            ),
            UserData=Base64(Join('', [
                "#!/bin/bash\n",
                "sudo apt-get update -y", "\n",
                "sudo apt-get install -y nginx", "\n",
                "sudo update-rc.d nginx defaults", "\n",
                "sudo service nginx start"
            ])),
            ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
            KeyName=Ref(self.key_name),
            IamInstanceProfile=Ref(self.instance_iam_role_instance_profile),
            BlockDeviceMappings=[
                ec2.BlockDeviceMapping(
                    DeviceName="/dev/sda1",
                    Ebs=ec2.EBSBlockDevice(
                        VolumeSize="8"
                    )
                ),
            ],
            SecurityGroups=Ref(self.web_security_group),
            InstanceType=Ref(self.instanceType),
        ))

        self.auto_scaling_group = template.add_resource(AutoScalingGroup(
            "duy%sAutoscalingGroup" % self.prefix,
            DesiredCapacity=Ref(self.scale_capacity_Desire),
            Tags=[
                Tag("Name", "duy-%s" % self.prefix, True),
                Tag("Environment", self.prefix, True),
                Tag("PropagateAtLaunch", "true", True)
            ],
            LaunchConfigurationName=Ref(self.launchConfiguration),
            MinSize=Ref(self.scale_capacity_min),
            MaxSize=Ref(self.scale_capacity_max),
            VPCZoneIdentifier=Ref(self.private_subnet),
            LoadBalancerNames=[Ref(self.loadBalancer)],
            HealthCheckType="EC2",
            HealthCheckGracePeriod="300",
            TerminationPolicies=[
                "OldestInstance",
                "Default"
            ],
            UpdatePolicy=UpdatePolicy(
                AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                    PauseTime='PT5M',
                    MinInstancesInService="1",
                    MaxBatchSize='1',
                    WaitOnResourceSignals=True
                )
            )
        ))

        self.scaling_policy = template.add_resource(ScalingPolicy(
            "duy%sScalingPolicy" % self.prefix,
            AdjustmentType="ExactCapacity",
            PolicyType="SimpleScaling",
            Cooldown="60",
            AutoScalingGroupName=Ref(self.auto_scaling_group),
            ScalingAdjustment="1",
        ))


        self.instance_iam_role_policy = template.add_resource(PolicyType(
            "InstanceIamRolePolicy",
            PolicyName="AppInstanceIamRolePolicy",
            PolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[GetObject],
                        Resource=[
                                "arn:aws:s3:::duy-logging/*",
                                "arn:aws:s3:::duy-site/*",
                                "arn:aws:s3:::duy-automation/*"
                                ]
                    ),
                    Statement(
                        Effect=Allow,
                        Action=[ListBucket],
                        Resource=[
                                "arn:aws:s3:::duy-logging",
                                "arn:aws:s3:::duy-site",
                                "arn:aws:s3:::duy-automation"
                                ]
                    )
                ]
            ),
            Roles=[Ref(self.instance_iam_role)]
        ))


    def _add_outputs(self, template):
        template.add_output(
            [Output('ELBURL',
                    Description='Newly created ELB URL',
                    Value=Join('',
                               ['http://',
                                GetAtt('LoadBalancer',
                                       'DNSName')]))]
        )

    def main(self):

        self._add_ami(self.t)

        self._add_parameters(self.t)

        self._add_resources(self.t)

        self._add_outputs(self.t)

        print(self.t.to_json())


if __name__ == '__main__':
    My_Template = MyCloudformationTemplate()
    My_Template.main()
