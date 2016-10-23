#!/bin/bash

set -e

# cloud-automation.sh <app> <environment> <num_servers> <server_size>
if [ "$#" != '4' ]; then
  echo "USAGE:"
  echo "cloud-automation.sh <app> <environment> <num_servers> <server_size>"
  exit 1
fi

if [[ -z ${AWS_ACCESS_KEY} || -z ${AWS_SECRET_KEY} ]]; then
  echo "Please set AWS access key and secret key as environment variables"
  exit 1
fi

app_name="$1"
environment="$2"
num_servers="$3"
server_size="$4"

echo "Running command: ${app_name}, ${environment}, ${num_servers}, ${server_size}"

terraform apply -var "aws_access_key=${AWS_ACCESS_KEY}" \
                -var "aws_secret_key=${AWS_SECRET_KEY}" \
                -var "num_servers=${num_servers}" \
                -var "server_size=${server_size}" \
                config/terraform/

echo "Generate inventory from terraform state"
python stealthdemo/inventory.py

echo "Test the available hosts"
ansible -i config/ansible/hosts -m ping all

echo "Bootstrapping on the server"
#ansible-playbook -i config/ansible/hosts config/ansible/wordpress/playbook.yml
ansible-playbook -i config/ansible/hosts config/ansible/docker/playbook.yml
ansible-playbook -i config/ansible/hosts config/ansible/wp_docker/playbook.yml
#ansible-playbook -i config/ansible/hosts config/ansible/wp_compose/wordpress.yml

echo "Get the load balancer DNS name to test"
python stealthdemo/getelb.py
