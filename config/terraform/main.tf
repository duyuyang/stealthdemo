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
  count           = "${var.num_servers}"

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

  instance_type = "${var.server_size}"

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
      "sudo apt-get -y update",
      "sudo apt-get install -y git",
      "git clone git://github.com/duyuyang/stealthdemo.git"
    ]
  }
}
