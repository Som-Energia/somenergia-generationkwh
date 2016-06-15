#!/usr/bin/env python

from .mongotimecurve import MongoTimeCurve, tz
from plantmeter.resource import *
from plantmeter.isodates import localisodatetime,naiveisodatetime

import pymongo
from datetime import datetime, date

import unittest

def local_file(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

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

    def test_getEmpty(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m = ProductionMeter(
                1,
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','eggrDescription',True)
        aggr.plants.append(p)

        self.assertEqual(
            list(aggr.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
                2*25*[0] 
                )
      
    def test_update_onePlantOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m = ProductionMeter(
                1,
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True)
        aggr.plants.append(p)
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
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = ProductionMeter(
                1,
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        m2 = ProductionMeter(
                2,
                'meterName2',
                'meterDescription2',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m1)
        p.meters.append(m2)
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True)
        aggr.plants.append(p)
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
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = ProductionMeter(
                1,
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p1 = ProductionPlant(1,'plantName1','plantDescription1',True)
        p1.meters.append(m1)
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True)

        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True)
        aggr.plants.append(p1)
        aggr.plants.append(p2)
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
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = ProductionMeter(
                1,
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p1 = ProductionPlant(1,'plantName1','plantDescription1',True)
        p1.meters.append(m1)

        m2 = ProductionMeter(
                1,
                'meterName2',
                'meterDescription2',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True)
        p2.meters.append(m2)

        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p1)
        aggr.plants.append(p2)
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
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider
        m = ProductionMeter(
                1,
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                lastcommit='2015-09-04',
                curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True)
        aggr.plants.append(p)
        updated = aggr.update_kwh()
        # Check single aggregator, with single plant and meter
        self.assertEqual(updated[0][1][0][1], localisodatetime('2015-09-05 23:00:00'))

    def test_update_outofdate(self):
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        curveProvider = self.curveProvider
        m = ProductionMeter(
                1,
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                lastcommit='2015-09-04',
                curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggrDescription',True)
        aggr.plants.append(p)
        updated = aggr.update_kwh()
        # Check single aggregator, with single plant and meter
        self.assertEqual(updated[0][1][0][1], None)

    def test_lastDate_empty(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)

        self.assertEqual(aggr.lastMeasurementDate(), None)
    
    def test_firstDate_empty(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)

        self.assertEqual(aggr.firstMeasurementDate(), None)

    def test_lastDate_onePlantOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_onePlantOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,9,4))

    def test_lastDate_onePlantTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = ProductionMeter(
            1,
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = ProductionMeter(
            1,
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m1)
        p.meters.append(m2)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_onePlantTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = ProductionMeter(
            1,
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = ProductionMeter(
            2,
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p = ProductionPlant(1,'plantName','plantDescription',True)
        p.meters.append(m1)
        p.meters.append(m2)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p)
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,8,4))

    def test_lastDate_twoPlantsTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = ProductionMeter(
            1,
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = ProductionMeter(
            2,
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p1 = ProductionPlant(1,'plantName1','plantDescription1',True)
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True)
        p1.meters.append(m1)
        p2.meters.append(m2)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p1)
        aggr.plants.append(p2)
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_twoPlantsTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = ProductionMeter(
            1,
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = ProductionMeter(
            2,
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p1 = ProductionPlant(1,'plantName1','plantDescription1',True)
        p2 = ProductionPlant(2,'plantName2','plantDescription2',True)
        p1.meters.append(m1)
        p2.meters.append(m2)
        aggr = ProductionAggregator(1,'aggrName','aggreDescription',True)
        aggr.plants.append(p1)
        aggr.plants.append(p2)
        m1.update_kwh(date(2015,9,4), date(2015,9,5))
        m2.update_kwh(date(2015,8,4), date(2015,8,5))

        self.assertEqual(aggr.firstMeasurementDate(), date(2015,8,4))

class Meter_Test(unittest.TestCase):
    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'production'

        self.connection = pymongo.MongoClient()
        self.connection.drop_database(self.databasename)
        self.db = self.connection[self.databasename]
        self.curveProvider = MongoTimeCurve(self.db, self.collection)
        self.uri = 'csv:/' + local_file('data/manlleu_20150904.csv')

    def tearDown(self):
        self.connection.drop_database('generationkwh_test')

    def test_get_whenEmpty(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            2*25*[0]
            )

    def test_get_afterUpdate(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(
            list(m.get_kwh(
                date(2015,9,4),
                date(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_lastDate_empty(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        self.assertEqual(m.lastMeasurementDate(), None)

    def test_lastDate_filled(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        m.update_kwh(date(2015,9,4), date(2015,9,5))

        self.assertEqual(m.lastMeasurementDate(), date(2015,9,5))

    def test_firstDate_empty(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        self.assertEqual(m.firstMeasurementDate(), None)

    def test_firstDate_filled(self):
        m = ProductionMeter(
            1,
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        m.update_kwh(date(2015,9,4), date(2015,9,5))
        self.assertEqual(m.firstMeasurementDate(), date(2015,9,4))


unittest.TestCase.__str__ = unittest.TestCase.id

# vim: et ts=4 sw=4
