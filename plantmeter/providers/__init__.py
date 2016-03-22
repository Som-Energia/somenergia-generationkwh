from __future__ import absolute_import

from urlparse import urlparse as std_urlparse
from plantmeter.providers.base import BaseProvider, \
        BaseProviderConnectionError, BaseProviderDownloadError

_AVAILABLE_PROVIDERS = {}


def register(name, cls):
    """Register a provider 

    :param name: Provider name
    :param class cls: Provider class
    """
    _AVAILABLE_PROVIDERS[name] = cls


def urlparse(url):
    url = std_urlparse(url)
    config = {
        'provider': url.scheme,
        'username': url.username,
        'password': url.password,
        'hostname': url.hostname,
        'port': url.port,
        'path': url.path.lstrip('/')
    }
    return config


def get_provider(uri):
    """Get the provider class by and URI.

    :param url: URI for identify a provider
    """
    config = urlparse(uri)
    provider = config['provider']
    if provider not in _AVAILABLE_PROVIDERS:
        raise Exception(
            'Provider {} is not available/registered'.format(provider)
        )
    return _AVAILABLE_PROVIDERS[provider]

# Import providers 
from plantmeter.providers.tfm import TFMProvider
from plantmeter.providers.csv import CSVProvider
from plantmeter.providers.monsol import MonsolProvider
