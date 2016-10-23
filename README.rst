===========
stealthdemo
===========

cloudci is a command line tool to automatically generate a cloudformation template
and provision the stack in a certain VPC.
A YAML configuration is required as an input to pre-setup VPC environment, including
public / private subnets, security groups, internet gateway, and net gateway.
So that we can provision our stack or multi-tier application into a provided VPC
in AWS account.


Description
===========

Terraform:
  1. does not create a cloudformation template to provision a stack
  2. hard to clean up the environment
  3. hard to manage per project or billing

Terraform python lib:
  https://github.com/jrbudnack/pterraform

ansible-playbook -i config/ansible/hosts config/ansible/wordpress/playbook.yml

ansible-playbook -i config/ansible/hosts config/ansible/docker/playbook.yml

ansible-playbook -i config/ansible/hosts config/ansible/wp_docker/playbook.yml

ansible-playbook -i config/ansible/hosts config/ansible/wp_compose/wordpress.yml

Note
====

This project has been set up using PyScaffold 2.5.7. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
