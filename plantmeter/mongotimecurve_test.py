#!/usr/bin/env python

from .mongotimecurve import MongoTimeCurve
import pymongo
import datetime

import unittest

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'generation'

        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')
    
    def setupPoints(self, points):
        mtc = MongoTimeCurve(self.db, self.collection)
        for datetime, plant, value in points:
            mtc.fillPoint(
                datetime=isodatetime(datetime),
                name=plant,
                ae=value,
            )
        return mtc


    def test_get_whenEmpty(self):
        mtc = self.setupPoints([
            ])
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
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-01 22:00:00', 'miplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-02 23:00:00', 'miplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ('2015-01-01 01:00:00', 'miplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'otraplanta', 10),
            ])

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
        mtc = self.setupPoints([
            ('2015-01-01 23:00:00', 'miplanta', 10),
            ('2015-01-01 23:00:00', 'miplanta', 30),
            ])

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
        mtc = self.setupPoints([
            ('2015-08-01 23:00:00', 'miplanta', 10),
            ])

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
        mtc = MongoTimeCurve(self.db, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                name='miplanta',
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'datetime'")

    def test_fillPoint_complaintsMissingName(self):
        mtc = MongoTimeCurve(self.db, self.collection)
        with self.assertRaises(Exception) as ass:
            mtc.fillPoint(
                datetime=isodatetime('2015-08-01 23:00:00'),
                ae=10,
                )
        self.assertEqual(ass.exception.args[0],
            "Missing 'name'")

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

    def setupDatePoints(self, date, name, values):
        return self.setupPoints([
            (date+" {:02}:00:00".format(i), name, value)
            for i, value in enumerate(values)
            ])

    def test_setupDatePoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', range(1,25))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            list(range(1,25))+[0])

    def test_lastFullDate_withNoPoints(self):
        mtc = self.setupDatePoints('2015-01-01', 'miplanta', [1]*24)

        lastdate = mtc.lastFullDate('miplanta')
        self.assertEqual(lastdate,isodate('2015-01-01'))
 




# vim: et ts=4 sw=4
