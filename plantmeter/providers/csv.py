# -*- coding: utf-8 -*-

from . import BaseProvider, register, urlparse
from ..isodates import localisodatetime, assertDateOrNone, daterange
from ..isodates import parseLocalTime, toLocal
import datetime
import io

class CSVProvider(BaseProvider):
    """CSV provider
    """

    def __init__(self, uri=None):
        if uri is None:
            uri = "csv://path"
        super(CSVProvider, self).__init__(uri)
        self.uri = uri
        self.res = self.uri.split(':')[1]

    def get(self, start, end=None):
        # TODO: Don't let this code survive!!

        assertDateOrNone('start', start)
        assertDateOrNone('end', end)

        def extract(line):
            items = line.rstrip().split(';')
            return {
                'datetime': parseLocalTime(items[0]+':00', items[1]=='S'),
                'ae': int(items[2]),
                }

        if not end:
            end = toLocal(datetime.datetime.now()).date()
        with io.open(self.res, 'r') as csvfile:
            content = csvfile.readlines()
            return [
                [
                measure
                for measure in (
                    extract(line)
                    for line in content[1:]
                    )
                if measure['datetime'].date() == date # TODO: la mare dels ous
                ]
                for date in daterange(start, end + datetime.timedelta(days=1))
            ]

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

register("csv", CSVProvider)

# vim: et ts=4 sw=4
