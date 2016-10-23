import json


class Resources(object):

    def __init__(self, tfstate):
        self.tfstate = tfstate

    def _readtfstate(self):
        with open(self.tfstate) as data_file:
            data = json.load(data_file)
        return data

    def _get_resource(self):
        data = self._readtfstate()
        return data['modules'][0]['resources']

    def _get_elb(self):
        resources = self._get_resource()
        return resources['aws_elb.web']['primary']['attributes']['dns_name']


    def main(self):
        elb = self._get_elb()
        print elb

if __name__ == '__main__':
    resource = Resources('terraform.tfstate')
    resource.main()
