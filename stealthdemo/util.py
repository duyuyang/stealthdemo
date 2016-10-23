import boto3

class AwsUtils(object):
    def __init__(self, profile_name, logger):
        self.profile = boto3.session.Session(profile_name=profile_name)
        self.logger = logger


    def get_clf_connection(self):
        """
        setup aws connection to Cloudformation
        :return: clf client
        """
        return boto3.client('cloudformation')
