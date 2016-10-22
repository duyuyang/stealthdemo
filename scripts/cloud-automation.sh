#!/bin/bash

set -e

# cloud-automation.sh <app> <environment> <num_servers> <server_size>
if [ "$#" != '4' ]; then
  echo "USAGE:"
  echo "cloud-automation.sh <app> <environment> <num_servers> <server_size>"
  exit 1
fi

if [[ -n ${AWS_ACCESS_KEY} || -n ${AWS_SECRET_KEY} ]]; then
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
ansible-playbook config/ansible/wordpress/wordpress.yml
