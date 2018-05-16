#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime
import pytz
from plantmeter.mongotimecurve import MongoTimeCurve
from plantmeter.isodates import naiveisodate, localisodate, parseLocalTime, asUtc
from yamlns import namespace as ns

import unittest

def localTime(string):
    isSummer = string.endswith("S")
    if isSummer: string=string[:-1]
    return parseLocalTime(string, isSummer)

def datespan(startDate, endDate):
    delta=datetime.timedelta(hours=1)
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta

class PlantMeterApiTestBase(unittest.TestCase):

    def setUp(self):
        import erppeek_wst
        import dbconfig
        import pymongo
        import tempfile

        self.maxDiff = None
        self.database = 'dummytest'
        self.collection = 'generationkwh.production.measurement'

        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()
        self.helper = self.c.GenerationkwhProductionAggregatorTesthelper
        self.m = pymongo.MongoClient()
        self.mdb = self.m[self.database]
        self.mdc = self.mdb[self.collection]
        self.curveProvider = MongoTimeCurve(self.mdb, self.collection)
        self.tempdir = tempfile.mkdtemp()
        self.clearAggregator()
        self.clearMeasurements()
        self.clearTempContent()
        
    def tearDown(self):
        self.clear()
        self.c.rollback()
        self.c.close()

    def clear(self):
        self.clearAggregator()
        self.clearMeasurements()
        self.clearTemp()

    

    def clearAggregator(self):
        aggr_obj = self.c.model('generationkwh.production.aggregator')
        plant_obj = self.c.model('generationkwh.production.plant')
        meter_obj = self.c.model('generationkwh.production.meter')
        not_obj = self.c.model('generationkwh.production.notifier')
        meter_obj.unlink(meter_obj.search([]))
        plant_obj.unlink(plant_obj.search([]))
        aggr_obj.unlink(aggr_obj.search([]))
        not_obj.unlink(not_obj.search([]))

    def clearMeasurements(self):
        self.helper.clear_mongo_collections([
            self.collection,
            ])

    def clearTemp(self):
        self.clearTempContent()
        os.removedirs(self.tempdir)

    def clearTempContent(self):
        for filename in os.listdir(self.tempdir):
            os.remove(os.path.join(self.tempdir, filename))

    def setupPlant(self, aggr_id, plant):
        plant_obj = self.c.model('generationkwh.production.plant')
        return plant_obj.create(dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True,
            nshares=1000*(plant+1)))

    def setupMeter(self, plant_id, plant, meter, lastcommit=None):
        meter_obj = self.c.model('generationkwh.production.meter')
        if lastcommit:
            lastcommit=lastcommit.strftime('%Y-%m-%d')
        return meter_obj.create(dict(
            plant_id=plant_id,
            name='mymeter%d%d' % (plant, meter),
            description='mymeter%d%d' % (plant, meter),
            uri='csv://%s/mymeter%d%d' % (self.tempdir, plant, meter),
            lastcommit=lastcommit,
            enabled=True))

    def setupAggregator(self, nplants, nmeters, lastcommit=None):
        aggr_obj = self.c.model('generationkwh.production.aggregator')
        aggr = aggr_obj.create(dict(
            name='myaggr',
            description='myaggr',
            enabled=True))

        meters = []
        for plant in range(nplants):
            plant_id = self.setupPlant(aggr, plant)
            for meter in range(nmeters):
                meters.append(self.setupMeter(plant_id, plant, meter, lastcommit))
        return aggr, meters

    def setupPointsByDay(self, points):

        for meter, start, end, values in points:
            daterange = datespan(
                localisodate(start),
                localisodate(end)+datetime.timedelta(days=1)
                )
            for date, value in zip(daterange, values):
                self.helper.fillMeasurementPoint(str(asUtc(date))[:-6],meter,value)

    def setupPointsByHour(self, points):
        for meter, date, value in points:
            self.helper.fillMeasurementPoint(str(asUtc(localTime(date)))[:-6],meter,value)

    def setupLocalMeter(self, filename, points):
        filename = os.path.join(self.tempdir,filename)
        import csv
        def toStr(date):
            return date.strftime('%Y-%m-%d %H:%M')

        with open(filename, 'w') as tmpfile:
            writer = csv.writer(tmpfile, delimiter=';')
            writer.writerows([
                (toStr(date),summer,value,0,0)
                for start, end, summer, values in points
                for date,value in zip(
                    datespan(
                        naiveisodate(start),
                        naiveisodate(end)+datetime.timedelta(days=1)
                    ), values)
                ])

    def getLastcommit(self, meter_id):
        return self.c.GenerationkwhProductionMeter.read(meter_id, ['lastcommit'])['lastcommit']

class GenerationkwhProductionAggregator_Test(PlantMeterApiTestBase):

    def test_get_kwh_onePlant_withNoPoints(self):
        aggr, meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-08-17', '2015-08-17')
        self.assertEqual(production, 25*[0])

    def test_get_kwh_onePlant_winter(self):
        aggr,meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-16', 24*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-03-16', '2015-03-16')
        self.assertEqual(production, 24*[10]+[0])

    def test_get_kwh_onePlant_winterToSummer(self):
        aggr,meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-03-29 00:00:00', 1),
            ('mymeter00', '2015-03-29 01:00:00', 2),
            ('mymeter00', '2015-03-29 03:00:00', 3),
            ('mymeter00', '2015-03-29 23:00:00', 4)
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-03-29', '2015-03-29')
        self.assertEqual(production, [1,2,3]+19*[0]+[4,0,0])

    def test_get_kwh_onePlant_summer(self):
        aggr,meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 24*[10]+[0])

    def test_get_kwh_onePlant_summerToWinter(self):
        aggr,meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter00','2015-10-25 00:00:00', 1),
            ('mymeter00','2015-10-25 02:00:00S', 2),
            ('mymeter00','2015-10-25 02:00:00', 3),
            ('mymeter00','2015-10-25 23:00:00', 4)
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-10-25', '2015-10-25')
        self.assertEqual(production, [1,0,2,3]+20*[0]+[4])

    def test_get_kwh_twoPlant_withNoPoints(self):
        aggr,meters = self.setupAggregator(
                nplants=2,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        production = self.helper.get_kwh(
                aggr_id, '2015-08-17', '2015-08-17')
        self.assertEqual(production, 25*[0])

    def test_get_kwh_twoPlant_winter(self):
        aggr,meters = self.setupAggregator(
                nplants=2,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-16', 24*[10]),
            ('mymeter10', '2015-03-16', '2015-03-16', 24*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-03-16', '2015-03-16')
        self.assertEqual(production, 24*[20] + [0])

    def test_get_kwh_twoPlant_winterToSummer(self):
        aggr, meters = self.setupAggregator(
                nplants=2,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-03-29 00:00:00', 1),
            ('mymeter00', '2015-03-29 01:00:00', 2),
            ('mymeter00', '2015-03-29 03:00:00', 3),
            ('mymeter00', '2015-03-29 23:00:00', 4),
            ('mymeter10', '2015-03-29 00:00:00', 1),
            ('mymeter10', '2015-03-29 01:00:00', 2),
            ('mymeter10', '2015-03-29 03:00:00', 3),
            ('mymeter10', '2015-03-29 23:00:00', 4)
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-03-29', '2015-03-29')
        self.assertEqual(production, [2,4,6]+19*[0]+[8,0,0])

    def test_get_kwh_twoPlant_summer(self):
        aggr,meters = self.setupAggregator(
                nplants=2,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10]),
            ('mymeter10', '2015-08-16', '2015-08-16', 24*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 24*[20]+[0])

    def test_get_kwh_twoPlant_summerToWinter(self):
        aggr,meters = self.setupAggregator(
                nplants=2,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter00','2015-10-25 00:00:00', 1),
            ('mymeter00','2015-10-25 02:00:00S', 2),
            ('mymeter00','2015-10-25 02:00:00', 3),
            ('mymeter00','2015-10-25 23:00:00', 4),
            ('mymeter10','2015-10-25 00:00:00', 1),
            ('mymeter10','2015-10-25 02:00:00S', 2),
            ('mymeter10','2015-10-25 02:00:00', 3),
            ('mymeter10','2015-10-25 23:00:00', 4)
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-10-25', '2015-10-25')
        self.assertEqual(production, [2,0,4,6]+20*[0]+[8])

    def test_get_kwh_twoDays(self):
        aggr,meters = self.setupAggregator(
                nplants=1,
                nmeters=1)
        aggr_id = aggr.read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-17', 48*[10])
            ])
        production = self.helper.get_kwh(
                aggr_id, '2015-03-16', '2015-03-17')
        self.assertEqual(production, 24*[10]+[0]+24*[10]+[0])

    def test_update_kwh_withNoPoints(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ])

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            production = self.helper.get_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            self.assertEqual(production, 25*[0])

    def test_update_kwh_onePlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            production = self.helper.get_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            self.assertEqual(production, 10*[0]+14*[10]+[0])

    def test_update_kwh_twoPlant_sameDay(self):
            aggr,meters = self.setupAggregator(
                    nplants=2,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])
            self.setupLocalMeter('mymeter10',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[20])
                ])

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            production = self.helper.get_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            self.assertEqual(production, 10*[0]+14*[30]+[0])

    def test_update_kwh_twoPlant_differentDays(self):
            aggr,meters = self.setupAggregator(
                    nplants=2,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])
            self.setupLocalMeter('mymeter10',[
                ('2015-08-17', '2015-08-17', 'S', 10*[0]+14*[20])
                ])

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')
            production = self.helper.get_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')
            self.assertEqual(production, 10*[0]+14*[10]+[0]+10*[0]+14*[20]+[0])

    @unittest.skip('working on')
    def test_update_kwh_missing(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1,
                    lastcommit=naiveisodate('2015-08-15'))
            aggr_id = aggr.read(['id'])['id']
            meter_id = meters[0].read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])

            self.helper.update_kwh(
                    aggr_id, None, None)
            production = self.helper.get_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')
            self.assertEqual(production, 10*[0]+14*[10]+[0])
            self.assertEqual(self.getLastcommit(meter_id), '2015-08-16')

    def test_firstMeasurementDate_noPoint(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ])

            date = self.helper.firstMeasurementDate(aggr_id)
            self.assertEqual(date, False)

    def test_firstMeasurementDate_onePlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-17', 'S', 10*[0]+14*[10]+10*[0]+14*[10])
                ])
            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')

            date = self.helper.firstMeasurementDate(aggr_id)
            self.assertEqual(date, '2015-08-16')

    def test_firstMeasurementDate_twoPlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=2,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])
            self.setupLocalMeter('mymeter10',[
                ('2015-08-17', '2015-08-17', 'S', 10*[0]+14*[20])
                ])
            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')

            date = self.helper.firstMeasurementDate(aggr_id)
            self.assertEqual(date, '2015-08-16')

    def test_lastMeasurementDate_onePlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-17', 'S', 10*[0]+14*[10]+10*[0]+14*[10])
                ])
            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')

            date = self.helper.lastMeasurementDate(aggr_id)
            self.assertEqual(date, '2015-08-17')

    def test_lastMeasurementDate_twoPlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=2,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])
            self.setupLocalMeter('mymeter10',[
                ('2015-08-17', '2015-08-17', 'S', 10*[0]+14*[20])
                ])
            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-17')

            date = self.helper.lastMeasurementDate(aggr_id)
            self.assertEqual(date, '2015-08-17')

    def test_getNshares_onePlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            shares = self.helper.getNshares(aggr_id)
            self.assertEqual(shares, 1000)

    def test_getNshares_twoPlant(self):
            aggr,meters = self.setupAggregator(
                    nplants=2,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            shares = self.helper.getNshares(aggr_id)
            self.assertEqual(shares, 3000)

class GenerationkwhProductionNotifier_Test(PlantMeterApiTestBase):

    def searchNotifications(self, search):
        return self.c.GenerationkwhProductionNotifier.search(search)

    def test_add_done(self):
            aggr, meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            meter_id = meters[0].read(['id'])['id']
            notification_id = self.c.GenerationkwhProductionNotifierTesthelper.push(
                    meter_id,
                    'done',
                    'xxxx')

            search_params = [
                    ('meter_id', '=', meter_id),
                    ('status', '=', 'done'),
                    ('message', '=', 'xxxx')
                    ]

            self.assertEqual(
                    self.searchNotifications(search_params)[0],
                    notification_id)

    def test_update_kwh_done(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            meter_id = meters[0].read(['id'])['id']
            self.setupLocalMeter('mymeter00',[
                ('2015-08-16', '2015-08-16', 'S', 10*[0]+14*[10])
                ])

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')

            search_params = [
                    ('meter_id', '=', meter_id),
                    ('status', '=', 'done')
                    ]
            self.assertNotEqual(
                    self.searchNotifications(search_params)[0], [])

    def test_update_kwh_failed(self):
            aggr,meters = self.setupAggregator(
                    nplants=1,
                    nmeters=1)
            aggr_id = aggr.read(['id'])['id']
            meter_id = meters[0].read(['id'])['id']

            self.helper.update_kwh(
                    aggr_id, '2015-08-16', '2015-08-16')

            search_params = [
                    ('meter_id', '=', meter_id),
                    ('status', '=', 'failed')
                    ]
            self.assertNotEqual(
                    self.searchNotifications(search_params)[0], [])

# vim: et ts=4 sw=4
