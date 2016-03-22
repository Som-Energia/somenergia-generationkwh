from __future__ import absolute_import
import os

#from osconf import config_from_environment

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution(__name__).version
except Exception as e:
    VERSION = 'unknown'


#from plantmeter.logging import setup_logging
#logging_config = config_from_environment('PLANETMETER_LOGGING')
#logger = setup_logging(**logging_config)


_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)

from . import mongotimecurve
from . import resource 
