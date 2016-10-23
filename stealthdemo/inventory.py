import json


class InventoryGenerator(object):

    def __init__(self, host, tfstate):
        self.tfstate = tfstate
        self.host = host

    def _readtfstate(self):
        with open(self.tfstate) as data_file:
            data = json.load(data_file)
        return data

    def _writeInventory(self, ip_list):
        l = []
        l.append('[all_servers:vars]')
        l.append('ansible_ssh_private_key_file =\
                 /home/ubuntu/.ssh/duy-demo.pem')
        l.append('')
        l.append('[all_servers:children]')
        l.append('wordpress')
        l.append('')
        l.append('[wordpress]')
        for ip in ip_list:
            l.append(ip)
        data = '\n'.join(l)
        with open(self.host, 'w') as data_file:
            data_file.write(data)

    def _get_resource(self):
        data = self._readtfstate()
        return data['modules'][0]['resources']

    def _get_instance_private_ip(self):
        resources = self._get_resource()
        try:
            """ 1 server behind elb"""
            return [resources['aws_instance.web']\
                    ['primary']['attributes']['private_ip']]
        except KeyError:
            """ multiple servers behind elb"""
            ip = []
            index = 0
            while  True:
                try:
                    key = "aws_instance.web.%s" % index
                    ip.append(resources[key]['primary']\
                              ['attributes']['private_ip'])
                    index = index + 1
                except KeyError:
                    return ip


    def main(self):
        private_ip_list = self._get_instance_private_ip()
        self._writeInventory(private_ip_list)


if __name__ == '__main__':
    IG = InventoryGenerator('config/ansible/hosts',
                            'terraform.tfstate.backup')
    IG.main()
