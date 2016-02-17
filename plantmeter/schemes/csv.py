from plantmeter.schemes import BaseScheme, register, urlparse
from plantmeter.utils import daterange
import datetime
import csv

class CSVScheme(BaseScheme):
    """CSV Scheme
    """
 
    def __init__(self, uri=None):
        if uri is None:
            uri = "csv://path"
        super(CSVScheme, self).__init__(uri)
        self.uri = uri
        self.res = self.uri.split(':')[1]

    def get(self, start, end=None):
        def extract(line):
            items = line.split(':')
            return {'datetime': items[0], 'ae': items[1]} 

        with open(self.res, 'rb') as csvfile:
            content = csvfile.readlines()
            return [extract(line) for date in daterange(start, end) 
                   for line in content 
                       if extract(line)['datetime'].startswith(date.strftime('%Y-%m-%d'))]

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

register("csv", CSVScheme)
