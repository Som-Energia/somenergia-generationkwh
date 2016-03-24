#!/usr/bin/env python

from .mongotimecurve import MongoTimeCurve, tz
from plantmeter.resource import *

import pymongo
from datetime import datetime

import unittest

def localDate(y,m,d):
    return tz.localize(datetime(y,m,d))

class Resource_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'production'

        self.connection = pymongo.Connection()
        self.connection.drop_database(self.databasename)
        self.db = self.connection[self.databasename]
        self.curveProvider = MongoTimeCurve(self.db, self.collection)

    def tearDown(self):
        self.connection.drop_database('generationkwh_test')

    def test_getEmpty(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m = Meter(
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = Plant('plantName','plantDescription',True)
        p.meters.append(m)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)

        self.assertEqual(
            list(vp.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
                2*25*[0] 
                )
      
    def test_update_onePlantOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m = Meter(
                'meterName',
                'meterDescription',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = Plant('plantName','plantDescription',True)
        p.meters.append(m)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)
        m.updateWh(
            localDate(2015,9,4),
            localDate(2015,9,5))

        self.assertEqual(
            list(vp.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_update_onePlantTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = Meter(
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        m2 = Meter(
                'meterName2',
                'meterDescription2',
                True,
                uri=uri,
                curveProvider = self.curveProvider)

        p = Plant('plantName','plantDescription',True)
        p.meters.append(m1)
        p.meters.append(m2)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)
        m1.updateWh(localDate(2015,9,4),localDate(2015,9,5))
        m2.updateWh(localDate(2015,9,4),localDate(2015,9,5))

        self.assertEqual(
            list(vp.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,6,12,10, 8,16,34,68,24,24,10,6,2,0,0,0,0,0,
                0,0,0,0,0,0,0,0,8,14,12,10,18,36,70,26,26,12,8,4,0,0,0,0,0,
            ])

    def test_update_twoPlantsOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = Meter(
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p1 = Plant('plantName1','plantDescription1',True)
        p1.meters.append(m1)
        p2 = Plant('plantName2','plantDescription2',True)

        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p1)
        vp.plants.append(p2)
        m1.updateWh(localDate(2015,9,4),localDate(2015,9,5))

        self.assertEqual(
            list(vp.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_update_twoPlantsTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        curveProvider = self.curveProvider 
        m1 = Meter(
                'meterName1',
                'meterDescription1',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p1 = Plant('plantName1','plantDescription1',True)
        p1.meters.append(m1)

        m2 = Meter(
                'meterName2',
                'meterDescription2',
                True,
                uri=uri,
                curveProvider = self.curveProvider)
        p2 = Plant('plantName2','plantDescription2',True)
        p2.meters.append(m2)

        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p1)
        vp.plants.append(p2)
        m1.updateWh(localDate(2015,9,4),localDate(2015,9,5))
        m2.updateWh(localDate(2015,9,4),localDate(2015,9,5))

        self.assertEqual(
            list(vp.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,6,12,10, 8,16,34,68,24,24,10,6,2,0,0,0,0,0,
                0,0,0,0,0,0,0,0,8,14,12,10,18,36,70,26,26,12,8,4,0,0,0,0,0,
            ])


    def test_lastDate_empty(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = Plant('plantName','plantDescription',True)
        p.meters.append(m)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)

        self.assertEqual(vp.lastMeasurementDate(), None)

    def test_lastDate_onePlantOneMeter(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        p = Plant('plantName','plantDescription',True)
        p.meters.append(m)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)
        m.updateWh(localDate(2015,9,4), localDate(2015,9,5))

        self.assertEqual(vp.lastMeasurementDate(), localDate(2015,9,5))

    def test_lastDate_onePlantTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = Meter(
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = Meter(
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p = Plant('plantName','plantDescription',True)
        p.meters.append(m1)
        p.meters.append(m2)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p)
        m1.updateWh(localDate(2015,9,4), localDate(2015,9,5))
        m2.updateWh(localDate(2015,8,4), localDate(2015,8,5))

        self.assertEqual(vp.lastMeasurementDate(), localDate(2015,8,5))


    def test_lastDate_twoPlantsTwoMeters(self):
        uri = 'csv:/' + local_file('data/manlleu_20150904.csv')
        m1 = Meter(
            'meterName1',
            'meterDescription1',
            True,
            uri = uri,
            curveProvider = self.curveProvider)
        uri = 'csv:/' + local_file('data/manlleu_20150804.csv')
        m2 = Meter(
            'meterName2',
            'meterDescription2',
            True,
            uri = uri,
            curveProvider = self.curveProvider)

        p1 = Plant('plantName1','plantDescription1',True)
        p2 = Plant('plantName2','plantDescription2',True)
        p1.meters.append(m1)
        p2.meters.append(m2)
        vp = VirtualPlant('vplantName','vplantDescription',True)
        vp.plants.append(p1)
        vp.plants.append(p2)
        m1.updateWh(localDate(2015,9,4), localDate(2015,9,5))
        m2.updateWh(localDate(2015,8,4), localDate(2015,8,5))

        self.assertEqual(vp.lastMeasurementDate(), localDate(2015,8,5))


class Meter_Test(unittest.TestCase):
    def setUp(self):
        self.databasename = 'generationkwh_test'
        self.collection = 'production'

        self.connection = pymongo.Connection()
        self.connection.drop_database(self.databasename)
        self.db = self.connection[self.databasename]
        self.curveProvider = MongoTimeCurve(self.db, self.collection)
        self.uri = 'csv:/' + local_file('data/manlleu_20150904.csv')

    def tearDown(self):
        self.connection.drop_database('generationkwh_test')

    def test_get_whenEmpty(self):
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)

        self.assertEqual(
            list(m.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            2*25*[0]
            )

    def test_get_afterUpdate(self):
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        m.updateWh(localDate(2015,9,4), localDate(2015,9,5))

        self.assertEqual(
            list(m.getWh(
                localDate(2015,9,4),
                localDate(2015,9,5))),
            [
                0,0,0,0,0,0,0,0,3,6,5,4,8,17,34,12,12,5,3,1,0,0,0,0,0,
                0,0,0,0,0,0,0,0,4,7,6,5,9,18,35,13,13,6,4,2,0,0,0,0,0,
            ])

    def test_lastDate_empty(self):
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        self.assertEqual(m.lastMeasurementDate(), None)

    def test_lastDate_filled(self):
        m = Meter(
            'meterName',
            'meterDescription',
            True,
            uri = self.uri,
            curveProvider = self.curveProvider)
        m.updateWh(localDate(2015,9,4), localDate(2015,9,5))

        self.assertEqual(m.lastMeasurementDate(), localDate(2015,9,5))


unittest.TestCase.__str__ = unittest.TestCase.id

# vim: et ts=4 sw=4
