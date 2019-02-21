#!/usr/bin/env python

from .mongotimecurve import MongoTimeCurve, tz
from .isodates import localisodatetime,naiveisodatetime
import os
import pymongo
from datetime import datetime, date
from . import testutils
from .resource import (
    ProductionMeter,
    ProductionPlant,
    ProductionAggregator,
    )

import unittest

def local_file(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

class Meter_Test(unittest.TestCase):
    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'production'

        self.connection = pymongo.MongoClient()
        self.connection.drop_database(self.databasename)
        self.db = self.connection[self.databasename]
        self.curveProvider = MongoTimeCurve(self.db, self.collection)
        self.uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        self.row1 = [0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,]
        self.row2 = [0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,]

    def tearDown(self):
        self.connection.drop_database('generationkwh_test')

    def setupMeter(self, **kwd):
        return ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider,
            **kwd
            )

    def test_get_empty(self):
        m = self.setupMeter()
        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            2*25*[0]
            )

    def test_get_filled(self):
        m = self.setupMeter()
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            self.row1 + self.row2)

    def test_get_filled__whenFiltered(self):
        m = self.setupMeter(working_since=date(2015,9,5))
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [0]*25 + self.row2)

    def test_get_filled__whenFiltered_onStart(self):
        m = self.setupMeter(working_since=date(2015,9,4))
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            self.row1 + self.row2)

    def test_get_filled__whenFiltered_onEnd(self):
        m = self.setupMeter(working_since=date(2015,9,6))
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [0]*50)

    def test_lastDate_empty(self):
        m = self.setupMeter()
        self.assertEqual(m.lastMeasurementDate(), None)

    def test_lastDate_filled(self):
        m = self.setupMeter()
        m.update_kwh(date(2015,9,4), date(2015,9,5))
        self.assertEqual(m.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_empty(self):
        m = self.setupMeter()
        self.assertEqual(m.firstMeasurementDate(), None)

    def test_firstDate_filled(self):
        m = self.setupMeter()
        m.update_kwh(date(2015,9,4), date(2015,9,5))
        self.assertEqual(m.firstMeasurementDate(), date(2015,9,4))

    # TODO: Test update_kwh setting lastcommit
    # TODO: the result of update_kwh is uses anywhere? if so, test it thoroughly if not drop it

class Resource_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'production'

        self.connection = pymongo.MongoClient()
        self.connection.drop_database(self.databasename)
        self.db = self.connection[self.databasename]
        self.curveProvider = MongoTimeCurve(self.db, self.collection)

    def tearDown(self):
        self.connection.drop_database('generationkwh_test')

    def setupMeter(self, n, uri, lastcommit=None):
        uri = 'csv:/' + local_file('data/manlleu_{}.csv'.format(uri))
        return ProductionMeter(
            id=n,
            name = 'meterName{}'.format(n),
            description = 'meterDescription{}'.format(n),
            enabled = True,
            uri = uri,
            curveProvider = self.curveProvider,
            lastcommit = lastcommit,
            )


    def test_getEmpty(self):
        m = self.setupMeter(1, '20150904')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','eggrDescription',True, plants=[p])

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
                2*25*[0] 
                )
      
    def test_update_onePlantOneMeter(self):
        m = self.setupMeter(1, '20150904')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True, plants=[p])
        m.update_kwh(
            date(2015,9,4),
            date(2015,9,5))

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_update_onePlantTwoMeters(self):
        m1 = self.setupMeter(1,'20150904')
        m2 = self.setupMeter(2,'20150904')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m1,m2])
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True, plants=[p])
        m1.update_kwh(date(2015,9,4),date(2015,9,5))
        m2.update_kwh(date(2015,9,4),date(2015,9,5))

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,6,12,10, 8,16,34,68,24,24,10,6,2,0,0,0,0,0,
                0,0,0,0,0,0,0,0,8,14,12,10,18,36,70,26,26,12,8,4,0,0,0,0,0,
            ])

    def test_update_twoPlantsOneMeter(self):
        m1 = self.setupMeter(1, '20150904')
        p1 = ProductionPlant(1,'plantName1','plantDescription1',True, meters=[m1])
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True)

        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True,plants=[p1,p2])
        m1.update_kwh(date(2015,9,4),date(2015,9,5))

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_update_twoPlantsTwoMeters(self):
        m1 = self.setupMeter(1, '20150904')
        p1 = ProductionPlant(1,'plantName1','plantDescription1',True, meters=[m1])

        m2 = self.setupMeter(2, '20150904')
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True, meters=[m2])

        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True,
            plants=[p1, p2])
        m1.update_kwh(date(2015,9,4),date(2015,9,5))
        m2.update_kwh(date(2015,9,4),date(2015,9,5))

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,6,12,10, 8,16,34,68,24,24,10,6,2,0,0,0,0,0,
                0,0,0,0,0,0,0,0,8,14,12,10,18,36,70,26,26,12,8,4,0,0,0,0,0,
            ])

    def test_update_startMissing(self):
        m = self.setupMeter(1, '20150904', lastcommit='2015-09-04')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True,
            plants=[p])
        updated = aggr.update_kwh()
        # Check single aggregator, with single plant and meter
        self.assertEqual(updated[0][1][0][1], localisodatetime('2015-09-05 23:00:00'))

    def test_update_outofdate(self):
        m = self.setupMeter(1, '20150804', lastcommit='2015-09-04')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True,
            plants=[p])
        updated = aggr.update_kwh()
        # Check single aggregator, with single plant and meter
        self.assertEqual(updated[0][1][0][1], None)

    def test_lastDate_empty(self):
        m = self.setupMeter(1, '20150904')
        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True,
            plants=[p])

        self.assertEqual(aggr.lastMeasurementDate(), None)
    
    def test_firstDate_empty(self):
        m = self.setupMeter(1, '20150904')
        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p])

        self.assertEqual(aggr.firstMeasurementDate(), None)

    def test_lastDate_onePlantOneMeter(self):
        m = self.setupMeter(1, '20150904')
        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p])
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_onePlantOneMeter(self):
        m = self.setupMeter(1, '20150904')
        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p])
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,9,4))

    def test_lastDate_onePlantTwoMeters(self):
        m1 = self.setupMeter(1, '20150904')
        m2 = self.setupMeter(2, '20150804')

        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m1,m2])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p])
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,8,5))

    def test_firstDate_onePlantTwoMeters(self):
        m1 = self.setupMeter(1, '20150904')
        m2 = self.setupMeter(2, '20150804')
        p = ProductionPlant(1,'plantName','plantDescription',True, meters=[m1,m2])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p])
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,8,4))

    def test_lastDate_twoPlantsTwoMeters(self):
        m1 = self.setupMeter(1, '20150904')
        m2 = self.setupMeter(2, '20150804')

        p1 = ProductionPlant(1,'plantName1','plantDescription1',True, meters=[m1])
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True, meters=[m2])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p1,p2])
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,8,5))

    def test_firstDate_twoPlantsTwoMeters(self):
        m1 = self.setupMeter(1, '20150904')
        m2 = self.setupMeter(2, '20150804')

        p1 = ProductionPlant(1,'plantName1','plantDescription1',True, meters=[m1])
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True, meters=[m2])
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True, plants=[p1,p2])
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,8,4))



# vim: et ts=4 sw=4
