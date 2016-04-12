import os
import numpy as np

from plantmeter.providers import get_provider

"""
TODOs
- Ordre
- Duplicats
- Gaps
- Padding
"""

def local_file(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

class Resource(object):
    name = None
    description = None
    enabled = None

    def __init__(self, name, description, enabled):
        self.name = name
        self.description = description
        self.enabled = enabled


class ProductionAggregator(Resource):
    def __init__(self, *args, **kwargs):
        self.plants = kwargs.pop('plants') if 'plants' in kwargs else []
        super(ProductionAggregator, self).__init__(*args, **kwargs)

    def getWh(self, start, end):
        return np.sum([
            plant.getWh(start, end)
            for plant in self.plants
            if plant.enabled
            ], axis=0)
    
    def firstMeasurementDate(self):
        return min([
            plant.firstMeasurementDate()
            for plant in self.plants
            if plant.enabled
            ])

    def lastMeasurementDate(self):
        return min([
            plant.lastMeasurementDate()
            for plant in self.plants
            if plant.enabled
            ])

class ProductionPlant(Resource):
    def __init__(self, *args, **kwargs):
        self.meters = kwargs.pop('meters') if 'meters' in kwargs else []
        super(ProductionPlant, self).__init__(*args, **kwargs)

    def getWh(self, start, end):
        return np.sum([
            meter.getWh(start, end)
            for meter in self.meters
            if meter.enabled
            ], axis=0)

    def lastMeasurementDate(self):
        return min([
            meter.lastMeasurementDate()
            for meter in self.meters
            if meter.enabled
            ])

    def firstMeasurementDate(self):
        return min([
            meter.firstMeasurementDate()
            for meter in self.meters
            if meter.enabled
            ])

class ProductionMeter(Resource):
    def __init__(self, *args, **kwargs):
        self.uri = kwargs.pop('uri') if 'uri' in kwargs else None 
        self.curveProvider = kwargs.pop('curveProvider') if 'curveProvider' in kwargs else None
        super(ProductionMeter, self).__init__(*args, **kwargs)

    def getWh(self, start, end):
        return self.curveProvider.get(start, end, self.name, 'ae')

    def updateWh(self, start, end=None):
        provider = get_provider(self.uri)
        with provider(self.uri) as remote:
            for day in remote.get(start, end):
                for measurement in day:
                    self.curveProvider.fillPoint(
                            name = self.name,
                            datetime = measurement['datetime'],
                            ae = measurement['ae']
                            )
    def lastMeasurementDate(self):
        return self.curveProvider.lastFullDate(self.name)
    
    def firstMeasurementDate(self):
        return self.curveProvider.firstFullDate(self.name)

# vim: et ts=4 sw=4
