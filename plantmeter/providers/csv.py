from plantmeter.providers import BaseProvider, register, urlparse
from plantmeter.utils import daterange
import datetime
import csv
from ..mongotimecurve import parseLocalTime

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
        def extract(line):
            items = line.split(';')
            return {
                'datetime': parseLocalTime(items[0]+':00', items[1]=='S'),
                'ae': items[2]
                } 

        with open(self.res, 'rb') as csvfile:
            content = csvfile.readlines()
            return [[
                measure
                for date in daterange(start, end + datetime.timedelta(days=1)) 
                for measure in (
                    extract(line)
                    for line in content[1:]
                    )
                if measure['datetime'].date() == date.date()
                ]]

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

register("csv", CSVProvider)
