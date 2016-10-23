import logging, argparse
import yaml, sys
from stealthdemo.cf_generator import ClfGenerator
from stealthdemo import __version__

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

    def main(self, args=None):
        if args is None:
            args = sys.argv[1:]
        parser = self._create_parser()
        parsed_args, remaining = parser.parse_known_args(args)
        data = self._get_config(parsed_args.input)
        print data

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
