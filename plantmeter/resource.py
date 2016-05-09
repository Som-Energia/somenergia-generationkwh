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

class Resource(object):
    id = None 
    name = None
    description = None
    enabled = None

    def __init__(self, id, name, description, enabled):
        self.id = id 
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
    
    def updateWh(self, start, end, notifier):
        return [plant.updateWh(start, end, notifier) for plant in self.plants]

    def firstMeasurementDate(self):
        return min([
            plant.firstMeasurementDate()
            for plant in self.plants
            if plant.enabled
            ])

    def lastMeasurementDate(self):
        return max([
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

    def updateWh(self, start, end, notifier):
        return [meter.updateWh(start, end, notifier) for meter in self.meters]

    def lastMeasurementDate(self):
        return max([
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

    def updateWh(self, start, end=None , notifier=None):
        import datetime

        now = datetime.datetime.now()
        provider = get_provider(self.uri)
        with provider(self.uri) as remote:
            status = 'done'
            message = None
            try:
                for day in remote.get(start, end):
                    for measurement in day:
                        self.curveProvider.fillPoint(
                                name = self.name,
                                datetime = measurement['datetime'],
                                ae = measurement['ae']
                                )
            except Exception as e:
                status = 'failed'
                message = str(e)
            finally:
                if notifier:
                    notifier.push(self.id, now, status, message)
        return True

    def lastMeasurementDate(self):
        return self.curveProvider.lastFullDate(self.name)
    
    def firstMeasurementDate(self):
        return self.curveProvider.firstFullDate(self.name)

# vim: et ts=4 sw=4
