import logging, argparse
import yaml, sys
from util import AwsUtils
from stealthdemo.cf_generator import ClfGenerator
from stealthdemo import __version__
from troposphere import Template

def setup_logging(level):
    """
    Convert log level string to an actual
    level and return a logger object

    :param level: Log level as a string
    :return: logger object
    """
    numeric_level = getattr(logging,
                            level.upper(),
                            None)
    if not isinstance(numeric_level, int):
        print 'Invalid log level: %s' % level
        exit(1)
    formatter = '%(asctime)s: %(processName)s: %(message)s'
    logging.basicConfig(format=formatter,
                    level=numeric_level)
    return logging.getLogger(__name__)

def main():
    driver = CFDriver()
    return driver.main()

HELP_BLURB = (
    "To see optional text, you can run:\n"
    "\n"
    "  cloudci\n"
    "  cloudci <arguments>\n"
)

USAGE = (
    "cloudci <arguments> \n"
    "%s" % HELP_BLURB
)

class CFDriver(object):

    def __init__(self):
        self._logger = setup_logging("debug")
        self._aws_util = AwsUtils('duy', self._logger)

    def _create_parser(self):
        parser = CLIArgParser()
        return parser

    def _get_config(self, data_file):
        try:
            with open(data_file) as data_file:
                data = yaml.load(data_file)
            return data
        except IOError:
            self._logger.info("No such file or directory: %s"
                              % data_file)

    def _save_template(self, template):
        local_file = '/tmp/my_template.json'
        try:
            with open(local_file, 'w') as data_file:
                data_file.write(template)
            self._logger.info("CloudFormation template saved!")
        except IOError:
            self._logger.info("Failed to write the template to: %s"
                              % local_file)

    def _create_stack(self, template):
        self._client = self._aws_util.get_clf_connection()
        #try:
        response = self._client.create_stack(
            StackName='test-stack',
            TemplateBody=template,
            DisableRollback=True,
            TimeoutInMinutes=123,
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=[
                {
                    'Key': 'Owner',
                    'Value': 'Du Y'
                }
            ]
        )
        self._logger.info("created stack: %s" % response)
        #except:
        #    self._logger.info("Create stack failed!")

    def main(self, args=None):
        if args is None:
            args = sys.argv[1:]
        parser = self._create_parser()
        parsed_args, remaining = parser.parse_known_args(args)
        self.data = self._get_config(parsed_args.input)
        self._logger.info("Input config data: %s"
                          % self.data)
        if self.data:
            self.t = Template()
            generator = ClfGenerator(config=self.data,
                                     template=self.t)
            self._logger.info("Template generated")
            template = generator.generated_template().to_json()
            #self._save_template(template)
            self._logger.info("Print out template: %s" % str(template))
            if len(template) > 0:
                self._create_stack(str(template))


class CLIArgParser(argparse.ArgumentParser):
    Formatter = argparse.RawTextHelpFormatter

    def __init__(self):
        super(CLIArgParser, self).__init__(
            formatter_class=self.Formatter,
            usage=USAGE)
        self._build()

    def parse_known_args(self,
                         args,
                         namespace=None):
        parsed, remaining = super(CLIArgParser, self)\
            .parse_known_args(args, namespace)
        return parsed, remaining

    def _build(self):
        self.add_argument('-v', '--version',
                          action="version",
                          version=__version__,
                          help="Display the version")
        self.add_argument('-i', '--input',
                          help="Provide the input data YAML",
                          required=True)
