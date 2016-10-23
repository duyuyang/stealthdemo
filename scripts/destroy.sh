#!/bin/bash

terraform destroy -var "aws_access_key=${AWS_ACCESS_KEY}" \
                  -var "aws_secret_key=${AWS_SECRET_KEY}" \
                  config/terraform/
