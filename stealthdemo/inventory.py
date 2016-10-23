import json


class InventoryGenerator(object):

    def __init__(self, host, tfstate):
        self.tfstate = tfstate
        self.host = host

    def _readtfstate(self):
        with open(self.tfstate) as data_file:
            data = json.load(data_file)
        return data

    def _writeInventory(self, ip):
        l = []
        l.append('[all_servers:vars]')
        l.append('ansible_ssh_private_key_file = /home/ubuntu/.ssh/duy-demo.pem')
        l.append('')
        l.append('[all_servers:children]')
        l.append('wordpress')
        l.append('')
        l.append('[wordpress]')
        l.append(ip)
        data = '\n'.join(l)
        with open(self.host, 'w') as data_file:
            data_file.write(data)

    def _get_resource(self):
        data = self._readtfstate()
        return data['modules'][0]['resources']

    def _get_instance_private_ip(self):
        resources = self._get_resource()
        return resources['aws_instance.web']['primary']['attributes']['private_ip']


    def main(self):
        private_ip = self._get_instance_private_ip()
        self._writeInventory(private_ip)


if __name__ == '__main__':
    IG = InventoryGenerator('config/ansible/hosts', 'terraform.tfstate')
    IG.main()
