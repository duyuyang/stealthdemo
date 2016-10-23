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

cloudci Usage:

```
$ cloudci -v
$ cloudci -i config/cloudformation/demo.yml

```

cloud-automation Usage:

```
$ scripts/cloud-automation.sh wordpress dev 2 t2.micro
```

clean up
```
$ scripts/destroy.sh
```

Terraform:
  1. provisioning load balancer and ec2 instance
  2. create aws resources

Terraform python lib:
  https://github.com/jrbudnack/pterraform

Ansible:
  To instnall wordpress on server or used in dockerfile
  ```
  $ ansible-playbook -i config/ansible/hosts config/ansible/wordpress/playbook.yml
  ```
  To install docker on Ubuntu
  ```
  $ ansible-playbook -i config/ansible/hosts config/ansible/docker/playbook.yml
  ```
  To spin up docker-compose
  ```
  $ ansible-playbook -i config/ansible/hosts config/ansible/wp_docker/playbook.yml
  ```
  To spin up ansible docker server as a compose
  ```
  $ ansible-playbook -i config/ansible/hosts config/ansible/wp_compose/wordpress.yml
  ```

Note
====

This project has been set up using PyScaffold 2.5.7. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
