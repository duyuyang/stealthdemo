variable "aws_access_key" {
  description = "AWS access key."
}

variable "aws_secret_key" {
  description = "AWS secret key."
}

variable "server_size" {
  description = "EC2 instance size."
  default = "t2.micro"
}

variable "num_servers" {
  description = "Number of instance register behind ELB"
  default = 1
}

variable "env" {
  description = "environment"
  default = "dev"
}

variable "key_name" {
  description = "Desired name of AWS key pair"
  default = "duy-demo"
}

variable "aws_region" {
  description = "AWS region to launch servers."
  default     = "ap-southeast-2"
}

# Ubuntu 14.04 LTS (x64)
variable "aws_amis" {
  default = {
    ap-southeast-2 = "ami-ba3e14d9"
  }
}
