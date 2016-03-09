#!/usr/bin/env python

import unittest

from pymongo import Connection
from yamlns import namespace as ns
import json
import numpy
import datetime
from .backends import urlparse

"""
- More than one meassure
- Summer daylight
- Different name ignored
- Priority for newer meassuers the same hour
- Check mandatory fields
- remove urlparse dependency on backends
- disconnect, context handlers...
- notice gaps
- last meassure
- first meassure
"""

class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, uri, collection):
        ""
        self.connection = Connection()
        self.config = urlparse(uri)
        self.collectionName = collection
        self.databasename = self.config['db'] 
        self.db = self.connection[self.databasename]
        self.collection = self.db[collection]

    def get(self, start, stop, filter, field):
        ndays = (stop-start).days+1
        data = numpy.zeros(ndays*25, numpy.int)
        filters = dict(
#            name = filter,
            datetime = {
                '$gte': start,
                '$lte': stop+datetime.timedelta(days=1)
            }
        )

        for x in self.collection.find(filters, [field,'datetime']):
            point = ns(x)
            timeindex = (
                +25*(point.datetime.date()-start.date()).days
                +point.datetime.hour
                )
            data[timeindex]=point.get(field)
        return data

    def fillPoint(self, data):
        counter = self.db['counters'].find_and_modify(
            {'_id': self.collectionName},
            {'$inc': {'counter': 1}}
        )
        data.update({'create_at': datetime.datetime.now()})
        return self.collection.insert(data)
        

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'generation'
        self.dburi = 'mongodb://localhost/{}'.format(self.databasename)

        c = Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        counters = self.db['counters']


    def tearDown(self):
        c = Connection()
        c.drop_database('generationkwh_test')

    

    def test_get_whenEmpty(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*25)

    def test_get_withSingleData(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*23+[10,0])

    def test_get_twoDays(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2014-12-31'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0]
            +23*[0]+[10,0]
            )

    def test_get_differentTime(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 22:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            str(list(curve)),
            str(+22*[0]+[10,0,0])
            )

    def test_get_withOutsideData(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-02 23:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0])

    def test_get_withTwoPoints(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            ))
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 1:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0,10]+21*[0]+[10,0])





# vim: ts ts=4 sw=4
