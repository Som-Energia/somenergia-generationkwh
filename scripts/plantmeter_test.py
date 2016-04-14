#!/usr/bin/env python

import datetime
import pytz
from plantmeter.mongotimecurve import MongoTimeCurve,parseLocalTime
from yamlns import namespace as ns

import unittest

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

def localTime(string):
    isSummer = string.endswith("S")
    if isSummer: string=string[:-1]
    return parseLocalTime(string, isSummer)

class GenerationkwhProductionAggregator_Test(unittest.TestCase):
    def setUp(self):
        import erppeek
        import dbconfig
        import pymongo

        self.database = dbconfig.pymongo['database']
        self.collection = 'generationkwh.production.measurement'

        self.c = erppeek.Client(**dbconfig.erppeek)
        self.m = pymongo.Connection()
        self.mdb = self.m[self.database]
        self.mdc = self.mdb[self.collection]
        self.curveProvider = MongoTimeCurve(self.mdb, self.collection)
        self.clearAggregator()
        self.clearMeasurements()
        
    def tearDown(self):
        self.clearAggregator()
        self.clearMeasurements()

    def clearAggregator(self):
        aggr_obj = self.c.model('generationkwh.production.aggregator')
        plant_obj = self.c.model('generationkwh.production.plant')
        meter_obj = self.c.model('generationkwh.production.meter')
        meter_obj.unlink(meter_obj.search([]))
        plant_obj.unlink(plant_obj.search([]))
        aggr_obj.unlink(aggr_obj.search([]))

    def clearMeasurements(self):
        self.mdc.delete_many({})

    def setupPlant(self, aggr_id, plant):
        plant_obj = self.c.model('generationkwh.production.plant')
        return plant_obj.create(dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True))

    def setupMeter(self, plant_id, meter):
        meter_obj = self.c.model('generationkwh.production.meter')
        return meter_obj.create(dict(
            plant_id=plant_id,
            name='mymeter%d' % meter,
            description='mymeter%d' % meter,
            uri='uri/mymeter%d' % meter,
            enabled=True))

    def setupAggregator(self, nplants, nmeters):
        aggr_obj = self.c.model('generationkwh.production.aggregator')
        aggr = aggr_obj.create(dict(
            name='myaggr',
            description='myaggr',
            enabled=True))

        for plant in range(nplants):
            plant_id = self.setupPlant(aggr, plant)
            for meter in range(nmeters):
                self.setupMeter(plant_id, meter)
        return aggr

    def setupPointsByDay(self, points):
        def datespan(startDate, endDate, delta=datetime.timedelta(hours=1)):
            currentDate = startDate
            while currentDate < endDate:
                yield currentDate
                currentDate += delta

        for meter, start, end, values in points:
            daterange = datespan(isodatetime(start), isodatetime(end)+datetime.timedelta(days=1))
            for date, value in zip(daterange, values):
                self.curveProvider.fillPoint(
                    datetime=localTime(str(date)),
                    name=meter,
                    ae=value)

    def setupPointsByHour(self, points):
        for meter, date, value in points:
            self.curveProvider.fillPoint(
                datetime=localTime(date),
                name=meter,
                ae=value)

    def test_GenerationkwhProductionAggregator_getwh_onePlant_withNoPoints(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter0', '2015-08-16', '2015-08-16', 24*[10])
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id, '2015-08-17', '2015-08-17')
        self.assertEqual(production, 25*[0])

    def test_GenerationkwhProductionAggregator_getwh_onePlant_winter(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter0', '2015-03-16', '2015-03-16', 24*[10])
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id, '2015-03-16', '2015-03-16')
        self.assertEqual(production, [0]+24*[10])

    def test_GenerationkwhProductionAggregator_getwh_onePlant_winterToSummer(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter0', '2015-03-29 00:00:00', 1),
            ('mymeter0', '2015-03-29 01:00:00', 2),
            ('mymeter0', '2015-03-29 03:00:00', 3),
            ('mymeter0', '2015-03-29 23:00:00', 4)
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id, '2015-03-29', '2015-03-29')
        self.assertEqual(production, [0,1,2,3]+19*[0]+[4,0])

    def test_GenerationkwhProductionAggregator_getwh_onePlant_summer(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

        self.setupPointsByDay([
            ('mymeter0', '2015-08-16', '2015-08-16', 24*[10])
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 24*[10]+[0])

    def test_GenerationkwhProductionAggregator_getwh_onePlant_summerToWinter(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

        self.setupPointsByHour([
            ('mymeter0','2015-10-25 00:00:00', 1),
            ('mymeter0','2015-10-25 02:00:00S', 2),
            ('mymeter0','2015-10-25 02:00:00', 3),
            ('mymeter0','2015-10-25 23:00:00', 4)
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id, '2015-10-25', '2015-10-25')
        self.assertEqual(production, [1,0,2,3]+20*[0]+[4])


# vim: et ts=4 sw=4
