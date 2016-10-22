# Specify the provider and access details
provider "aws" {
  region = "${var.aws_region}"
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
}

resource "aws_elb" "web" {
  name = "duy-terraform-elb"

  subnets         = ["subnet-7146ee15", "subnet-2272a454"]
  security_groups = ["sg-296c574d"]
  instances       = ["${aws_instance.web.id}"]

  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }
}

resource "aws_instance" "web" {
  # The connection block tells our provisioner how to
  # communicate with the resource (instance)
  connection {
    # The default username for our AMI
    user = "ubuntu"
    private_key = "${file("/home/ubuntu/.ssh/duy-demo.pem")}"
    # The connection will use the local SSH agent for authentication.
  }

  instance_type = "t2.micro"

  # Lookup the correct AMI based on the region
  # we specified
  ami = "${lookup(var.aws_amis, var.aws_region)}"

  # The name of our SSH keypair we created above.
  key_name = "${var.key_name}"

  # Our Security group to allow HTTP and SSH access
  vpc_security_group_ids = ["sg-6f6c570b", "sg-086c576c"]

  # We're going to launch into a private subnet
  subnet_id = "subnet-2746ee43"

  # We run a remote provisioner on the instance after creating it.
  # In this case, we just install docker and start it.
  provisioner "remote-exec" {
    inline = [
      "sudo su",
      "apt-get -y update",
      "apt-get -y install apt-transport-https ca-certificates",
      "apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D",
      "echo 'deb https://apt.dockerproject.org/repo ubuntu-trusty main' > /etc/apt/sources.list.d/docker.list",
      "apt-get -y update",
      "apt-cache policy docker-engine",
      "apt-get -y update",
      "apt-get install -y linux-image-extra-$(uname -r) linux-image-extra-virtual",
      "gpasswd -a ubuntu docker",
      "service docker restart"
    ]
  }
}
