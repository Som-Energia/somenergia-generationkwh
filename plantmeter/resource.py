import os
import numpy as np
from urlparse import urlparse

from plantmeter.backends import get_backend
from plantmeter.schemes import get_scheme
from plantmeter.models.plant import * 


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


import unittest
from datetime import datetime
from plantmeter.resource import *
#@unittest.skip("be patient!!")
class Resource_Test(unittest.TestCase):
    def test_get(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = Meter('meter1','meter1 description',True,uri=uri)
        p1 = Plant('plant1','plant1 description',True)
        p1.meters.append(m1)
        vp1 = VirtualPlant('vplant1','vplant1 description',True)
        vp1.plants.append(p1)
        context = {'backend': 'mongodb://localhost/somenergia'}
        ##m1.update_kwh(date(2015,9,4),date(2015,9,5), context)
        #m1.update_kwh(datetime(2015,9,4,0,0,0),datetime(2015,9,5,0,0,0), context)
        self.assertEqual(
            list(vp1.get_kwh(
                datetime(2015,9,4,0,0,0),
                datetime(2015,9,5,0,0,0),
                context)),
                [ 6,  3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  3,  5, 
                12, 12, 34, 17,  8,  4,  5,  6,  3,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  3,  6,  5,  4,  8, 17, 34, 12, 12,
                5,  3,  1,  0,  0,  0,  0,  5,  4,  8, 17, 34, 12, 12,  5,  3,  1, 
                0,  0,  0,  0]
                )

      
    def _test_update(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = Meter('meter1','meter1 description',True,uri=uri)
        p1 = Plant('plant1','plant1 description',True)
        p1.meters.append(m1)
        vp1 = VirtualPlant('vplant1','vplant1 description',True)
        vp1.plants.append(p1)
        context = {'backend': 'mongodb://localhost/somenergia'}
        m1.update_kwh(date(2015,9,4),date(2015,9,5), context)
        #m1.update_kwh(datetime(2015,9,4,0,0,0),datetime(2015,9,5,0,0,0), context)
        self.assertEqual(
            list(vp1.get_kwh(
                datetime(2015,9,4,0,0,0),
                datetime(2015,9,5,0,0,0),
                context)),
                [ 6,  3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  3,  5, 
                12, 12, 34, 17,  8,  4,  5,  6,  3,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  3,  6,  5,  4,  8, 17, 34, 12, 12,
                5,  3,  1,  0,  0,  0,  0,  5,  4,  8, 17, 34, 12, 12,  5,  3,  1, 
                0,  0,  0,  0]
                )

from pymongo import Connection
class Meter_Test(unittest.TestCase):
    def setUp(self):
        c = Connection()
        c.drop_database('generationkwh_test')
        self.db = c['generationkwh_test']
        self.collection = self.db['generation']
        self.context = {'backend': 'mongodb://localhost/generationkwh_test'}
        self.uri = 'csv:/' + local_file('data/manlleu_20150904.csv')

    def tearDown(self):
        c = Connection()
        c.drop_database('generationkwh_test')

    def _test_get_whenEmpty(self):
        m = Meter('meter1','meter1 description',True,uri=self.uri)
        self.assertEqual(
            list(m.get_kwh(
                datetime(2015,9,4,0,0,0),
                datetime(2015,9,5,0,0,0),
                self.context)),
            25*[0]
                )

    def test_get_afterUpdate(self):
        m = Meter('meter1','meter1 description',True,uri=self.uri)
        m.update_kwh(datetime(2015,9,4,0,0,0),datetime(2015,9,5,0,0,0), self.context)
        self.assertEqual(
            list(m.get_kwh(
                datetime(2015,9,4,0,0,0),
                datetime(2015,9,5,0,0,0),
                self.context)),
            [0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 5, 4, 8, 17, 34, 12, 12, 5, 3, 1, 0, 0, 0, 0]
            )
    def _test_get(self):
        m = Meter('meter1','meter1 description',True,uri=self.uri)
        self.assertEqual(
            list(m.get_kwh(
                datetime(2015,9,4,0,0,0),
                datetime(2015,9,5,0,0,0),
                self.context)),
                [ 6,  3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  3,  5, 
                12, 12, 34, 17,  8,  4,  5,  6,  3,  0,  0,  0,  0,  0,  0,  0,  0,
                0,  0,  0,  0,  0,  0,  0,  0,  3,  6,  5,  4,  8, 17, 34, 12, 12,
                5,  3,  1,  0,  0,  0,  0,  5,  4,  8, 17, 34, 12, 12,  5,  3,  1, 
                0,  0,  0,  0]
                )
