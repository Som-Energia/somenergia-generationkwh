# -*- coding: utf-8 -*-
import os
import unittest
import datetime
dbconfig = None
try:
    import dbconfig
    import erppeek
    import pymongo
    from generationkwh.rightspershare import RightsPerShare
    from plantmeter.mongotimecurve import toLocal
except ImportError:
    pass

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d")

def datespan(startDate, endDate, delta=datetime.timedelta(hours=1)):
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta

def localisodate(string):
    return toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

@unittest.skipIf(not dbconfig, "depends on ERP")
class ProductionLoader_Test(unittest.TestCase):
    def setUpAggregator(self):
        self.clearAggregator()

    def clearAggregator(self):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        plant_obj = self.erp.model('generationkwh.production.plant')
        meter_obj = self.erp.model('generationkwh.production.meter')
        meter_obj.unlink(meter_obj.search([]))
        plant_obj.unlink(plant_obj.search([]))
        aggr_obj.unlink(aggr_obj.search([]))

    def setUpMeasurements(self):
        self.database = dbconfig.pymongo['database']
        self.collection = 'generationkwh.production.measurement'
        self.m = pymongo.Connection()
        self.mdb = self.m[self.database]
        self.mdc = self.mdb[self.collection]
        self.clearMeasurements()

    def clearMeasurements(self):
        self.mdc.delete_many({})

    def setUpTemp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()

    def clearTemp(self):
        for filename in os.listdir(self.tempdir):
            os.remove(os.path.join(self.tempdir, filename))
        os.removedirs(self.tempdir)

    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)

        self.setUpAggregator()
        self.setUpMeasurements()
        self.setUpTemp()
        self.productionLoader = self.erp.GenerationkwhProductionLoader

    def tearDown(self):
        self.clearAggregator()
        self.clearMeasurements()
        self.clearTemp()

    def setupPlant(self, aggr_id, plant):
        plant_obj = self.erp.model('generationkwh.production.plant')
        return plant_obj.create(dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True,
            nshares=1000*(plant+1)))

    def setupMeter(self, plant_id, plant, meter):
        meter_obj = self.erp.model('generationkwh.production.meter')
        return meter_obj.create(dict(
            plant_id=plant_id,
            name='mymeter%d%d' % (plant, meter),
            description='mymeter%d%d' % (plant, meter),
            uri='csv://%s/mymeter%d%d' % (self.tempdir, plant, meter),
            enabled=True))

    def setupAggregator(self, nplants, nmeters):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        aggr = aggr_obj.create(dict(
            name='myaggr',
            description='myaggr',
            enabled=True))

        for plant in range(nplants):
            plant_id = self.setupPlant(aggr, plant)
            for meter in range(nmeters):
                self.setupMeter(plant_id, plant, meter)
        return aggr

    def setupLocalMeter(self, filename, points):
        import csv
        def toStr(date):
            return date.strftime('%Y-%m-%d %H:%M')

        with open(filename, 'w') as tmpfile:
            writer = csv.writer(tmpfile, delimiter=';')
            writer.writerows([[toStr(date),summer,value,0,0]
                for start, end, summer, values in points
                for date,value in zip(datespan(isodatetime(start),
                    isodatetime(end)+datetime.timedelta(days=1)), values)])

    def getProduction(self, aggr_id, start, end):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        return aggr_obj.getWh(aggr_id, '2015-08-16', '2015-08-16')

    def _test_retrieveMeasuresFromPlants_withNoPoints(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ])
        self.productionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 25*[0])

    def _test_retrieveMeasuresFromPlants_onePlant(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.productionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+[1000]+14*[0])

    def _test_retrieveMeasuresFromPlants_twoPlant(self):
        aggr_id = self.setupAggregator(
                nplants=2,
                nmeters=1).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter10'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.productionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+[2000]+14*[0])

 
    def getRightsPerShare(self, aggr_id, start, end):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        return aggr_obj.getWh(aggr_id, '2015-08-16', '2015-08-16')

    def test_computeAvailableRights_singleDay(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.productionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        self.productionLoader.computeAvailableRights(aggr_id)

        rights = RightsPerShare(self.mdb)
        result = rights.rightsPerShare(1,
                localisodate('2015-08-16'),
                localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-17'), 0),
            ])


if __name__ == '__main__':
    unittest.main()

