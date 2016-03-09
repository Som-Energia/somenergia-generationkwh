# -*- coding: utf-8 -*-
"""
    plantmeter.logging
    ~~~~~~~~~~~~~~~

    Implements the logging support for plantmeter 

    You can use logging everywhere using::

        from plantmeter import logger
        logger.info('Info message')
"""
from __future__ import absolute_import

import logging

#from raven import Client as SentryClient
#from raven.handlers.logging import SentryHandler
from plantmeter import VERSION

LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'


def setup_logging(level=None, logfile=None):
    """
    Setups plantmeter logging system.

    It will setup sentry logging if SENTRY_DSN environment is defined

    :param level: logging.LEVEL to set to logger (defaults INFO)
    :param logfile: File to write the log
    :return: logger
    """
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter(LOG_FORMAT))

    logger = logging.getLogger('plantmeter')
    del logger.handlers[:]
    logger.addHandler(stream)

    if logfile:
        hdlr = logging.FileHandler(logfile)
        formatter = logging.Formatter(LOG_FORMAT)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    #sentry = SentryClient()
    #sentry.tags_context({'version': VERSION})
    #sentry_handler = SentryHandler(sentry, level=logging.ERROR)
    #logger.addHandler(sentry_handler)

    if isinstance(level, basestring):
        level = getattr(logging, level.upper(), None)

    if level is None:
        level = logging.INFO

    logger.setLevel(level)

    return logger
