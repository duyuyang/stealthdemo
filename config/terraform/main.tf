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
    connection {
      user = "ubuntu"
   }
    inline = [
      "sudo apt-get -y update",
      "sudo apt-get -y install apt-transport-https ca-certificates",
      "sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D",
      "sudo touch /etc/apt/sources.list.d/docker.list",
      "sudo chmod 0666 /etc/apt/sources.list.d/docker.list",
      "sudo echo 'deb https://apt.dockerproject.org/repo ubuntu-trusty main' > /etc/apt/sources.list.d/docker.list",
      "sudo apt-get -y update",
      "apt-cache policy docker-engine",
      "sudo apt-get -y update",
      "sudo apt-get install -y linux-image-extra-$(uname -r) linux-image-extra-virtual",
      "sudo apt-get install -y docker-engine",
      "sudo gpasswd -a ubuntu docker",
      "sudo service docker restart",
      "sudo apt-add-repository ppa:ansible/ansible -y",
      "sudo apt-get -y update",
      "sudo apt-get install -y ansible python-pip",
      "sudo pip install docker-compose==1.8.1",
      "sudo pip install docker-py==1.10.4",
      "sudo pip install requests==2.7.0"      
    ]
  }
  provisioner "remote-exec" {
    inline = [
      "git clone git://github.com/duyuyang/stealthdemo.git",
      "docker-compose -f stealthdemo/config/ansible/wp_compose/docker-compose.yml up -d"
    ]
  }
}
