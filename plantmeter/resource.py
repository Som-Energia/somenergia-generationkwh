import numpy as np
from urlparse import urlparse

from plantmeter.backends import get_backend
from plantmeter.schemes import get_scheme
from plantmeter.models.plant import * 


class Resource(object):
    name = None
    description = None
    enabled = None

    def __init__(self, name, description, enabled):
        self.name = name
        self.description = description
        self.enabled = enabled


class VirtualPlant(Resource):
    def __init__(self, *args, **kwargs):
        self.plants = kwargs.pop('plants') if 'plants' in kwargs else []
        super(VirtualPlant, self).__init__(*args, **kwargs)

    def get_kwh(self, start, end, context=None):
        return np.sum([plant.get_kwh(start, end, context)
                          for plant in self.plants if plant.enabled], axis=0)


class Plant(Resource):
    def __init__(self, *args, **kwargs):
        self.meters = kwargs.pop('meters') if 'meters' in kwargs else []
        super(Plant, self).__init__(*args, **kwargs)

    def get_kwh(self, start, end, context=None):
        return np.sum([meter.get_kwh(start, end, context)
                          for meter in self.meters if meter.enabled], axis=0)


class Meter(Resource):
    def __init__(self, *args, **kwargs):
        self.uri = kwargs.pop('uri') if 'uri' in kwargs else None 
        super(Meter, self).__init__(*args, **kwargs)

    def get_kwh(self, start, end, context=None):
        backend = get_backend(context['backend'])
        with backend(context['backend']) as bnd:
            return [MeasurementSchema().load(measurement).data.ae
                       for measurement in bnd.get(self.name, start, end)]

    def update_kwh(self, start, end=None, context=None):
        scheme = get_scheme(self.uri)
        backend = get_backend(context['backend'])
        with backend(context['backend']) as bnd:
            with scheme(self.uri) as sch:
                for day in sch.get(start, end):
                    for measurement in day:
                        document = MeasurementSchema().dump(Measurement(
                            self.name,
                            measurement['datetime'],
                            measurement['ae'])).data
                        document.update({'datetime': measurement['datetime']}) # TO BE FIXED
                        bnd.insert(document)

class Measurement(object):
    def __init__(self, name, datetime, ae):
        self.name = name
        self.datetime = datetime
        self.ae = ae
