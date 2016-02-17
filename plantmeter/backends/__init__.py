from __future__ import absolute_import

from urlparse import urlparse as std_urlparse
from plantmeter.backends.base import BaseBackend

_AVAILABLE_BACKENDS = {}


def register(name, cls):
    """Register a backend

    Use this function to register a Backend class for and schema. If you want
    to register your own backend you can do::

        class YourAwesomeBackend(BaseBackend):
            pass

        register('awesome', YourAwsomeBackend)

    Then with the URL ``awesome://user:pass@host/db`` with the function
    :func:`get_backend`

    :param name: Backend name
    :param class cls: Backend class
    """
    _AVAILABLE_BACKENDS[name] = cls


def urlparse(url):
    url = std_urlparse(url)
    config = {
        'backend': url.scheme,
        'username': url.username,
        'password': url.password,
        'hostname': url.hostname,
        'port': url.port,
        'db': url.path.lstrip('/')
    }
    return config


def get_backend(url):
    """Get the backend class by and URL.

    :param url: URL for identify a backend.
    """
    config = urlparse(url)
    backend = config['backend']
    if backend not in _AVAILABLE_BACKENDS:
        raise Exception(
            'Backend {} is not available/registered'.format(backend)
        )
    return _AVAILABLE_BACKENDS[backend]

# Import Backends
from plantmeter.backends.mongodb import MongoDBBackend
