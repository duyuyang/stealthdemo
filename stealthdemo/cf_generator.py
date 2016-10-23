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
    def __init__(self, config, template):
        self.t = template
        self.config = config
        self.t.add_version("2010-09-09")
        self.t.add_description("""EC2 instances with LoadBalancer, AutoScalingGroup and SecurityGroups """)
        self.ref_stack_id = Ref('AWS::StackId')
        self.ref_region = Ref('AWS::Region')
        self.ref_stack_name = Ref('AWS::StackName')


    def _add_ami(self, template):
        template.add_mapping("RegionMap", {
            "ap-southeast-2": {"AMI": "ami-ba3e14d9"}
        })

    def _instance_iam_role(self):
        return Role(
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
                )

    def _instance_iam_role_instance_profile(self):
        return InstanceProfile(
                    "InstanceIamRoleInstanceProfile",
                    Path="/",
                    Roles=[Ref(self.instance_iam_role)]
               )

    def _load_balancer(self):
        return LoadBalancer(
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
                    Subnets=self.config['public_subnet'],
                    HealthCheck=elb.HealthCheck(
                        Target="HTTP:80/",
                        HealthyThreshold="5",
                        UnhealthyThreshold="2",
                        Interval="20",
                        Timeout="15",
                    ),
                    Listeners=[
                        elb.Listener(
                            LoadBalancerPort=self.config['elb_port'],
                            InstancePort=self.config['instance_port'],
                            Protocol="HTTP",
                            InstanceProtocol="HTTP",
                        ),
                    ],
                    CrossZone=True,
                    SecurityGroups=self.config['elb_sg'],
                    LoadBalancerName="duy%sELB" % self.config['env'],
                    Scheme="internet-facing",
                )
    def _launch_config(self):
        return LaunchConfiguration(
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
                    KeyName=self.config['sshkey'],
                    IamInstanceProfile=Ref(self.instance_iam_role_instance_profile),
                    BlockDeviceMappings=[
                        ec2.BlockDeviceMapping(
                            DeviceName="/dev/sda1",
                            Ebs=ec2.EBSBlockDevice(
                                VolumeSize="8"
                            )
                        ),
                    ],
                    SecurityGroups=self.config['app_sg'],
                    InstanceType=self.config['instance_type'],
                )

    def _auto_scaling_group(self):
        return AutoScalingGroup(
                    "duy%sAutoscalingGroup" % self.config['env'],
                    DesiredCapacity=self.config['scale_desire'],
                    Tags=[
                        Tag("Name", "duy-%s" % self.config['env'], True),
                        Tag("Environment", self.config['env'], True),
                        Tag("PropagateAtLaunch", "true", True)
                    ],
                    LaunchConfigurationName=Ref(self.launchConfiguration),
                    MinSize=self.config['scale_min'],
                    MaxSize=self.config['scale_max'],
                    VPCZoneIdentifier=self.config['private_subnet'],
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
                )

    def _scaling_policy(self):
        return ScalingPolicy(
                    "duy%sScalingPolicy" % self.config['env'],
                    AdjustmentType="ExactCapacity",
                    PolicyType="SimpleScaling",
                    Cooldown="60",
                    AutoScalingGroupName=Ref(self.auto_scaling_group),
                    ScalingAdjustment="1",
                )

    def _instance_iam_role_policy(self):
        return PolicyType(
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
                )


    def _add_resources(self, template):
        self.instance_iam_role = \
            template.add_resource(self._instance_iam_role())
        self.instance_iam_role_instance_profile = \
            template.add_resource(self._instance_iam_role_instance_profile())
        self.loadBalancer = \
            template.add_resource(self._load_balancer())
        self.launchConfiguration = \
            template.add_resource(self._launch_config())
        self.auto_scaling_group = \
            template.add_resource(self._auto_scaling_group())
        self.scaling_policy = \
            template.add_resource(self._scaling_policy())
        self.instance_iam_role_policy = \
            template.add_resource(self._instance_iam_role_policy())

    def _output_elb_dns_name(self):
        return Output('ELBURL',
                    Description='Newly created ELB URL',
                    Value=Join('',
                               ['http://',
                                GetAtt('LoadBalancer',
                                       'DNSName')]))

    def _add_outputs(self, template):
        template.add_output(
            [self._output_elb_dns_name()]
        )

    def generated_template(self):

        self._add_ami(self.t)

        self._add_resources(self.t)

        self._add_outputs(self.t)

        return self.t
