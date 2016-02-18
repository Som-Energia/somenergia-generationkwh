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
            items = line.split(';')
            return {'datetime': datetime.datetime.strptime(items[0], '%Y-%m-%d %H:%M'), 'ae': items[1]} 

        with open(self.res, 'rb') as csvfile:
            content = csvfile.readlines()
            return [[measure
		   for date in daterange(start, end) 
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

register("csv", CSVScheme)
