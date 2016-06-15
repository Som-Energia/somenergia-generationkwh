import os
import numpy as np

from plantmeter.providers import get_provider
from plantmeter.isodates import localisodate, assertDateOrNone, assertDate, dateToLocal
import datetime

"""
TODOs
+ Ordre
- Duplicats
- Gaps
+ Padding
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

    def get_kwh(self, start, end):

        assertDate('start', start)
        assertDate('end', end)

        return np.sum([
            plant.get_kwh(start, end)
            for plant in self.plants
            if plant.enabled
            ], axis=0)
    
    def update_kwh(self, start=None, end=None, notifier=None):

        assertDateOrNone('start', start)
        assertDateOrNone('end', end)

        return [(plant.id, plant.update_kwh(start, end, notifier)) for plant in self.plants]

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

    def get_kwh(self, start, end):
        assertDate('start', start)
        assertDate('end', end)

        return np.sum([
            meter.get_kwh(start, end)
            for meter in self.meters
            if meter.enabled
            ], axis=0)

    def update_kwh(self, start=None, end=None, notifier=None):

        assertDateOrNone('start', start)
        assertDateOrNone('end', end)

        return [(meter.id, meter.update_kwh(start, end, notifier)) for meter in self.meters]

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
        self.lastcommit = kwargs.pop('lastcommit') if 'lastcommit' in kwargs else None
        if self.lastcommit:
            self.lastcommit = localisodate(self.lastcommit).date() + datetime.timedelta(days=1)
        self.curveProvider = kwargs.pop('curveProvider') if 'curveProvider' in kwargs else None
        super(ProductionMeter, self).__init__(*args, **kwargs)

    def get_kwh(self, start, end):

        assertDate('start', start)
        assertDate('end', end)

        return self.curveProvider.get(
            dateToLocal(start),
            dateToLocal(end),
            self.name,
            'ae'
            )

    def update_kwh(self, start=None, end=None , notifier=None):
        import datetime

        assertDateOrNone('start', start)
        assertDateOrNone('end', end)

        if start is None:
            start = self.lastcommit

        provider = get_provider(self.uri)
        updated = None
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
                        updated = measurement['datetime']
            except Exception as e:
                status = 'failed'
                message = str(e)
            finally:
                if notifier:
                    notifier.push(self.id, status, message)
        return updated

    def lastMeasurementDate(self):
        result = self.curveProvider.lastFullDate(self.name)
        return result and result.date()
    
    def firstMeasurementDate(self):
        result = self.curveProvider.firstFullDate(self.name)
        return result and result.date()

# vim: et ts=4 sw=4
