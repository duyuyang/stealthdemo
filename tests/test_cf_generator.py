import unittest, json
from stealthdemo.cf_generator import ClfGenerator
from troposphere import Template
from mock import patch

class TestClfGenerator(unittest.TestCase):
    def setUp(self):
        self.config = {'instance_port': 80,
                       'scale_min': 1,
                       'sshkey': 'duy-demo',
                       'app_sg': ['sg-6f6c570b', 'sg-086c576c'],
                       'scale_desire': 1,
                       'scale_max': 2,
                       'elb_port': 80,
                       'instance_type': 't2.micro',
                       'private_subnet': ['subnet-2746ee43',
                                          'subnet-1c72a46a'],
                       'env': 'dev',
                       'elb_sg': ['sg-296c574d'],
                       'app_version': 'latest',
                       'public_subnet': ['subnet-2272a454',
                                         'subnet-7146ee15'],
                       'app_name': 'wordpress'}
        self.template = Template()
        self.generator = ClfGenerator(self.config,
                                      self.template)

    def test_instance_iam_role(self):
        expect = json.loads("""
        {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "EC2 instances with LoadBalancer, AutoScalingGroup and SecurityGroups ",
            "Resources": {
                "InstanceIamRole": {
                    "Properties": {
                        "AssumeRolePolicyDocument": {
                            "Statement": [
                                {
                                    "Action": [
                                        "sts:AssumeRole"
                                    ],
                                    "Effect": "Allow",
                                    "Principal": {
                                        "Service": [
                                            "ec2.amazonaws.com"
                                        ]
                                    }
                                }
                            ]
                        },
                        "Path": "/"
                    },
                    "Type": "AWS::IAM::Role"
                }
            }
        }
        """)
        role = self.generator._instance_iam_role()
        my_json, my_template = self.get_template_resource_json(role)
        self.assertEqual(my_json, expect)



    def get_template_resource_json(self, obj):
        """
        Convert the resource object to json
        :param obj: the troposphere object
        :return json
        """
        self.template.add_resource(obj)
        my_template = self.template.to_json(indent=2,
                                            separators=(',', ': '))
        my_json = json.loads(my_template)
        return my_json, my_template

if __name__ == '__main__':
    unittest.main(verbosity=2)
