from __future__ import absolute_import

from urlparse import urlparse as std_urlparse
from plantmeter.schemes.base import BaseScheme

_AVAILABLE_SCHEMES = {}


def register(name, cls):
    """Register a scheme 

    :param name: Scheme name
    :param class cls: Scheme class
    """
    _AVAILABLE_SCHEMES[name] = cls


def urlparse(url):
    url = std_urlparse(url)
    config = {
        'scheme': url.scheme,
        'username': url.username,
        'password': url.password,
        'hostname': url.hostname,
        'port': url.port,
        'path': url.path.lstrip('/')
    }
    return config


def get_scheme(uri):
    """Get the scheme class by and URI.

    :param url: URI for identify an scheme
    """
    config = urlparse(uri)
    scheme = config['scheme']
    if scheme not in _AVAILABLE_SCHEMES:
        raise Exception(
            'Scheme {} is not available/registered'.format(scheme)
        )
    return _AVAILABLE_SCHEMES[scheme]

# Import schemes 
from plantmeter.schemes.tfm import TFMScheme 
from plantmeter.schemes.csv import CSVScheme 
