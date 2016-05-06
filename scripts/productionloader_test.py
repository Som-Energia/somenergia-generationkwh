# -*- coding: utf-8 -*-
import os
import unittest
import datetime
dbconfig = None
try:
    import dbconfig
    import erppeek
    from plantmeter.mongotimecurve import addDays
except ImportError:
    pass

from generationkwh.isodates import localisodate

def datespan(startDate, endDate, delta=datetime.timedelta(hours=1)):
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta

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
        self.collection = 'generationkwh.production.measurement'
        self.clearMeasurements()

    def clearMeasurements(self):
        self.TestHelper.clear_mongo_collections([self.collection])

    def setUpTemp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()

    def clearTemp(self):
        for filename in os.listdir(self.tempdir):
            os.remove(os.path.join(self.tempdir, filename))
        os.removedirs(self.tempdir)

    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)
        self.ProductionLoader = self.erp.GenerationkwhProductionLoader
        self.TestHelper = self.erp.GenerationkwhTesthelper
        self.setUpAggregator()
        self.setUpMeasurements()
        self.setUpTemp()

    def tearDown(self):
        self.clearAggregator()
        self.clearMeasurements()
        self.clearRemainders()
        self.clearTemp()

    def setupPlant(self, aggr_id, plant, nshares):
        plant_obj = self.erp.model('generationkwh.production.plant')
        return plant_obj.create(dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True,
            nshares=nshares))

    def setupMeter(self, plant_id, plant, meter):
        meter_obj = self.erp.model('generationkwh.production.meter')
        return meter_obj.create(dict(
            plant_id=plant_id,
            name='mymeter%d%d' % (plant, meter),
            description='mymeter%d%d' % (plant, meter),
            uri='csv://%s/mymeter%d%d' % (self.tempdir, plant, meter),
            enabled=True))

    def setupAggregator(self, nplants, nmeters, nshares):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        aggr = aggr_obj.create(dict(
            name='myaggr',
            description='myaggr',
            enabled=True))

        for plant in range(nplants):
            plant_id = self.setupPlant(aggr, plant, nshares[plant])
            for meter in range(nmeters):
                self.setupMeter(plant_id, plant, meter)
        return aggr

    def setupRemainders(self, remainders):
        remainder = self.erp.model('generationkwh.remainder.testhelper')
        remainder.updateRemainders(remainders)
        return remainder

    def clearRemainders(self):
        remainder = self.erp.model('generationkwh.remainder')
        remainder.clean()

    def setupLocalMeter(self, filename, points):
        import csv
        def toStr(date):
            return date.strftime('%Y-%m-%d %H:%M')

        with open(filename, 'w') as tmpfile:
            writer = csv.writer(tmpfile, delimiter=';')
            writer.writerows([[toStr(date),summer,value,0,0]
                for start, end, summer, values in points
                for date,value in zip(datespan(localisodate(start),
                    addDays(localisodate(end),1)),
                    values)])

    def getProduction(self, aggr_id, start, end):
        aggr_obj = self.erp.model('generationkwh.production.aggregator.testhelper')
        return aggr_obj.getWh(aggr_id, start, end)

    def test_retrieveMeasuresFromPlants_withNoPoints(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[1]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 25*[0])

    def test_retrieveMeasuresFromPlants_onePlant(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[1]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+[1000]+14*[0])

    def test_retrieveMeasuresFromPlants_twoPlant(self):
        aggr_id = self.setupAggregator(
                nplants=2,
                nmeters=1,
                nshares=[1,1]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter10'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')

        production = self.getProduction(aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+[2000]+14*[0])

 
    def getRightsPerShare(self, aggr_id, start, end):
        aggr_obj = self.erp.model('generationkwh.production.aggregator')
        return aggr_obj.getWh(aggr_id, start, end)

    def test_computeAvailableRights_singleDay(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[1]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[1000]+13*[0])
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.ProductionLoader.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1, '2015-08-16', '2015-08-16')
        self.assertEqual(result, +10*[0]+[1]+14*[0])
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-17', 0],
            ])

    def test_computeAvailableRights_withManyPlantShares_divides(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[4]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-16', 'S', 10*[0]+[20000]+13*[0])
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-16')
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.ProductionLoader.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-16')
        self.assertEqual(result, +10*[0]+[5]+14*[0])
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-17', 0],
            ])

    def test_computeAvailableRights_withManyPlantShares_twoDays(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[4]).read(['id'])['id']
        self.setupLocalMeter(os.path.join(self.tempdir,'mymeter00'),[
            ('2015-08-16', '2015-08-17', 'S', 2*(10*[0]+[20000]+13*[0]))
            ])
        self.ProductionLoader.retrieveMeasuresFromPlants(aggr_id,
                '2015-08-16', '2015-08-17')
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.ProductionLoader.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-17')
        self.assertEqual(result, 2*(10*[0]+[5]+14*[0]))
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-18', 0],
            ])

if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
