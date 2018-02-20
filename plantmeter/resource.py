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

class ParentResource(Resource):

    def __init__(self, id, name, description, enabled, children=[]):
        super(ParentResource, self).__init__(id, name, description, enabled)
        self.children = children

    def get_kwh(self, start, end):

        assertDate('start', start)
        assertDate('end', end)

        return np.sum([
            child.get_kwh(start, end)
            for child in self.children
            if child.enabled
            ], axis=0)

    def update_kwh(self, start=None, end=None, notifier=None):

        assertDateOrNone('start', start)
        assertDateOrNone('end', end)

        return [
            # TODO: Untested you can mess up with ID
            (meter.id, meter.update_kwh(start, end, notifier))
            for meter in self.children
            ]

    def firstMeasurementDate(self):
        return min([
            child.firstMeasurementDate()
            for child in self.children
            if child.enabled
            ])

    def lastMeasurementDate(self):
        return max([
            child.lastMeasurementDate()
            for child in self.children
            if child.enabled
            ])

class ProductionAggregator(ParentResource):
    def __init__(self, id, name, description, enabled, plants=[]):
        super(ProductionAggregator, self).__init__(
            id, name, description, enabled, children=plants)

class ProductionPlant(ParentResource):
    def __init__(self, id, name, description, enabled, meters=[]):
        super(ProductionPlant, self).__init__(
            id, name, description, enabled, children=meters)

class ProductionMeter(Resource):
    def __init__(self, *args, **kwargs):
        self.uri = kwargs.pop('uri', None)
        self.lastcommit = kwargs.pop('lastcommit', None)
        if self.lastcommit:
            self.lastcommit = localisodate(self.lastcommit).date() + datetime.timedelta(days=1)
        self.curveProvider = kwargs.pop('curveProvider', None)
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
