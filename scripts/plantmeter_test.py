#!/usr/bin/env python

import datetime
import pytz
from plantmeter.mongotimecurve import MongoTimeCurve,toLocal,tz
from yamlns import namespace as ns

import unittest

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

def localisodate(string):
        return toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

class GenerationkwhProductionAggregator_Test(unittest.TestCase):
    def setUp(self):
        import erppeek
        import dbconfig
        import pymongo

        self.database = dbconfig.pymongo['database']
        self.collection = 'generationkwh.production.plant'

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
            name='mymerter%d' % meter,
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

    def setupPoints(self, points):
        def datespan(startDate, endDate, delta=datetime.timedelta(hours=1)):
            currentDate = startDate
            while currentDate < endDate:
                yield currentDate
                currentDate += delta

        for meter, start, end, values in points:
            daterange = datespan(isodatetime(start), isodatetime(end))
            for date, value in zip(daterange, values):
                self.curveProvider.fillPoint(
                    datetime=tz.localize(date),
                    name=meter,
                    ae=value)

    def test_GenerationkwhProductionAggregator_getwhOnePlant(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']

    	self.setupPoints([
	    	('mymeter0', '2015-08-16', '2015-08-17', 24*[10])
            ])
        production = self.c.GenerationkwhProductionAggregator.getWh(
                aggr_id,localisodate('2015-08-16'), localisodate('2015-08-17'))
        self.assertEqual(production, 24*[10])

# vim: et ts=4 sw=4
