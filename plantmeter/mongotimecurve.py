#!/usr/bin/env python

import pymongo
from yamlns import namespace as ns
import json
import numpy
import datetime
from .backends import urlparse

"""
+ More than one meassure
+ Different name ignored
+ Priority for newer meassuers the same hour
+ Summer daylight
+ Check mandatory fields
+ last meassure
+ first meassure
- Properly detect summer daylight change
- disconnect, context handlers...
- notice gaps
- remove urlparse dependency on backends

"""

class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, uri, collection):
        ""
        self.connection = pymongo.Connection()
        self.config = urlparse(uri)
        self.collectionName = collection
        self.databasename = self.config['db'] 
        self.db = self.connection[self.databasename]
        self.collection = self.db[collection]

    def get(self, start, stop, filter, field):
        ndays = (stop-start).days+1
        data = numpy.zeros(ndays*25, numpy.int)
        filters = dict(
            name = filter,
            datetime = {
                '$gte': start,
                '$lte': stop+datetime.timedelta(days=1)
            }
        )

        for x in self.collection.find(filters, [field,'datetime']).sort(
                'create_at',pymongo.ASCENDING):
            point = ns(x)
            monthAndDay = point.datetime.month, point.datetime.day
            summerOffset = 1 if (3,26) < monthAndDay < (10,26) else 0
            timeindex = (
                +summerOffset
                +25*(point.datetime.date()-start.date()).days
                +point.datetime.hour
                )
            data[timeindex]=point.get(field)
        return data

    def fillPoint(self, **data):
        for requiredField in ('name', 'datetime'):
            if requiredField not in data:
                raise Exception("Missing '{}'".format(requiredField))

        counter = self.db['counters'].find_and_modify(
            {'_id': self.collectionName},
            {'$inc': {'counter': 1}}
        )
        data.update(
            create_at = datetime.datetime.now()
            )
        return self.collection.insert(data)

    def _firstLastDate(self, name, first=False):
        """returns the date of the first or last item of a given name"""
        order = pymongo.ASCENDING if first else pymongo.DESCENDING
        for point in (self.collection
                .find(dict(name=name))
                .sort('datetime', order)
                .limit(1)
                ):
            return datetime.datetime.combine(
                ns(point).datetime.date(),
                datetime.time(0,0,0))

        return None

    def firstDate(self, name):
        """returns the date of the first item of a given name"""
        return self._firstLastDate(name, first=True)

    def lastDate(self, name):
        """returns the date of the last item of a given name"""
        return self._firstLastDate(name)


def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

import unittest

class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'generation'
        self.dburi = 'mongodb://localhost/{}'.format(self.databasename)

        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        counters = self.db['counters']


    def tearDown(self):
        c = pymongo.Connection()
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
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            )

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
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            )

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
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 22:00:00'),
            name='miplanta',
            ae=10,
            )

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
        mtc.fillPoint(
            datetime=isodatetime('2015-01-02 23:00:00'),
            name='miplanta',
            ae=10,
            )

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
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            )
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 1:00:00'),
            name='miplanta',
            ae=10,
            )

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0,10]+21*[0]+[10,0])

    def test_get_differentNameIgnored(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='otraplanta',
            ae=10,
            )

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +25*[0])


    def test_get_prioritizesNewest(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            )

        mtc.fillPoint(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=30,
            )

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +23*[0]+[30,0])

    def test_get_summerPointsPadsLeft(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(
            datetime=isodatetime('2015-08-01 23:00:00'),
            name='miplanta',
            ae=10,
            )

        curve = mtc.get(
            start=isodate('2015-08-01'),
            stop=isodate('2015-08-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            +24*[0]+[10])

    def test_fillPoint_complaintsMissingDatetime(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                name='miplanta',
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'datetime'")

    def test_fillPoint_complaintsMissingName(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                datetime=isodatetime('2015-08-01 23:00:00'),
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'name'")

    def setupPoints(self, points):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        for datetime, plant, value in points:
            mtc.fillPoint(
                datetime=isodatetime(datetime),
                name=plant,
                ae=value,
            )
        return mtc

    def test_lastDate_whenNoPoint_returnsNone(self):
        mtc = self.setupPoints([
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,None)

    def test_lastDate_withOnePoint_takesIt(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))

    def test_lastDate_withForeignPoint_ignored(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 30)
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,None)
      
    def test_lastDate_withSeveralPoints_takesLast(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ('2015-01-02 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.lastDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-02'))

    def test_firstDate_withSeveralPoints_takesFirst(self):
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ('2015-01-02 23:00:00', 'miplanta', 30),
            ])

        lastdate = mtc.firstDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))
 




# vim: ts ts=4 sw=4
