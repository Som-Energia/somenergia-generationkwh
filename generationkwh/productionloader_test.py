# -*- coding: utf-8 -*-

from productionloader import ProductionLoader
import unittest
import datetime
import pymongo
from .rightspershare import RightsPerShare
import numpy

from .isodates import localisodate, isodate

class ProductionAggregatorMockUp(object):

    def __init__(self,first=None,last=None,data=None):
        self.data = data
        self.firstDate = first
        self.lastDate = last
        self.updateStart = None
        self.updateEnd = None

    def getWh(self, *args):
        return self.data

    def getFirstMeasurementDate(self):
        return self.firstDate

    def getLastMeasurementDate(self):
        return self.lastDate

    def retrieveMeasuresFromPlants(self, start, end):
        self.updateStart = start
        self.updateEnd = end

class RemainderProviderMockup(object):
    
    def __init__(self,remainders=[]):
        self.remainders = dict((remainder[0], remainder) for remainder in remainders)

    def lastRemainders(self):
        return [self.remainders[nshares] for nshares in self.remainders]
    
    def updateRemainders(self, remainders):
        for nshares, date, remainder in remainders:
            self.remainders[nshares] = (nshares, date, remainder)

class PlantShareCurverMockup(object):

    def __init__(self, data):
        self.data = data

    def hourly(self, start, end):
        return self.data

class userRightsProviderMockup(object):
    def __init__(self, userRights, newRemainder):
        self.userRights=userRights
        self.newRemainder=newRemainder

    def computeRights(*args):
        return userRights, newRemainder

class rightsPerShareProviderMockup(object):
    def updateRightsPerShare(self, n, start, stop):
        self.data.append([n,start,stop])

    def getRightsPerShare():
        return self.data

class ProductionLoaderTest(unittest.TestCase):

    def assertStartPointEqual(self, firstProductionDate, remainders, expected):
        l = ProductionLoader()
        date = l.startPoint(localisodate(firstProductionDate),[
            (shares, isodate(date), remainderwh)
            for shares, date, remainderwh in remainders
            ])
        self.assertEqual(str(date.date()), expected)
    
    def test_startPoint_withNoremainders(self):
        self.assertStartPointEqual('2000-01-01',[
            ], '2000-01-01')

    def test_startPoint_withSingleRemainder(self):
        self.assertStartPointEqual('2000-01-01',[
            (1, '2001-01-01', 45),
            ], '2001-01-01')

    def test_startPoint_withManyRemainders(self):
        self.assertStartPointEqual('2000-01-01',[
            (1, '2002-01-01', 45),
            (2, '2001-01-01', 45),
            ], '2001-01-01')


    def test_endPoint_withNoProduction(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), [])
        self.assertEqual('2000-01-01', str(date))

    def test_endPoint_withOneDay(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), 25*[0])
        self.assertEqual('2000-01-02', str(date))

    def test_endPoint_withHalfADay_justReturnsTheWholeOnes(self):
        l = ProductionLoader()
        date = l.endPoint(isodate('2000-01-01'), 27*[0])
        self.assertEqual('2000-01-02', str(date))


    def assertDatePairEqual(self, expected, result):
        e1,e2 = expected
        self.assertEqual((localisodate(e1),localisodate(e2)), result)

    def test_getRecomputationInterval_withNoremainders_takesFirstMeassure(self):
        p = ProductionAggregatorMockUp(
                first=localisodate('2000-01-01'),
                last=localisodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([])
        self.assertDatePairEqual( ('2000-01-01','2006-01-01'), interval)
    
    def test_getRecomputationInterval_withSingleRemainders_takesIt(self):
        p = ProductionAggregatorMockUp(
                first=localisodate('2000-01-01'),
                last=localisodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    def test_getRecomputationInterval_withManyRemainders_takesEarlier(self):
        p = ProductionAggregatorMockUp(
                first=localisodate('2000-01-01'),
                last=localisodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2002-01-01'), 45),
            (2,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    @unittest.skip("Failing case!!")
    def test_getRecomputationInterval_withRemaindersSameTarget_takesLater(self):
        p = ProductionAggregatorMockUp(
                first=localisodate('2000-01-01'),
                last=localisodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2002-01-01'), 45),
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual(
            ('2002-01-01','2006-01-01'),
            interval)

    def setUp(self):
        self.maxDiff = None
        self.databasename = 'generationkwh_test'
        
        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        
    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')


    def test_appendRightsPerShare_singleDay(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=localisodate('2015-08-16'),
            lastDateToCompute=localisodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            )
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_appendRightsPerShare_withManyPlantShares_divides(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=localisodate('2015-08-16'),
            lastDateToCompute=localisodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[20000]+14*[0]),
            plantshares=numpy.array(25*[4]), # here
            )
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[5]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_appendRightsPerShare_withNShares_multiplies(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=2, # here
            firstDateToCompute=localisodate('2015-08-16'),
            lastDateToCompute=localisodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            )
        result = rights.rightsPerShare(2,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[2]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (2, isodate('2015-08-17'), 0),
            ])

    def test_appendRightsPerShare_withAdvancedRemainder(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            firstDateToCompute=localisodate('2015-08-16'),
            lastDateToCompute=localisodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(100*[0]+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(100*[0]+25*[1]),
            )
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_appendRightsPerShare_firstDateToCompute_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16').date(),
                lastDateToCompute=localisodate('2015-08-16'),
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "firstDateToCompute should be a datetime")

    def test_appendRightsPerShare_lastDateToCompute_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16'),
                lastDateToCompute=localisodate('2015-08-16').date(), # here
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "lastDateToCompute should be a datetime")

    def test_appendRightsPerShare_tooSmallProductionArray(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16'),
                lastDateToCompute=localisodate('2015-08-17'),
                lastRemainder=0,
                production=numpy.array(49*[1]),
                plantshares=numpy.array(50*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Not enough production data to compute such date interval")

    def test_appendRightsPerShare_tooSmallShareArray(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16'),
                lastDateToCompute=localisodate('2015-08-17'),
                lastRemainder=0,
                production=numpy.array(50*[1]),
                plantshares=numpy.array(49*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Not enough plant share data to compute such date interval")

    def test_appendRightsPerShare_crossedDates(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                firstDateToCompute=localisodate('2015-08-16'),
                lastDateToCompute=localisodate('2015-08-15'),
                lastRemainder=0,
                production=numpy.array(50*[1]),
                plantshares=numpy.array(50*[1]),
                )
        self.assertEqual(ctx.exception.args[0],
            "Empty interval")

    def test_computeAvailableRights_singleDay(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=localisodate('2015-08-16'),
                last=localisodate('2015-08-16'),
                data=numpy.array(+10*[0]+[1000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withManyPlantShares_divides(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=localisodate('2015-08-16'),
                last=localisodate('2015-08-16'),
                data=numpy.array(+10*[0]+[20000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[4]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[5]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withNShares_multiplies(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            (2, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=localisodate('2015-08-16'),
                last=localisodate('2015-08-16'),
                data=numpy.array(+10*[0]+[1000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(2,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[2]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            (2, isodate('2015-08-17'), 0),
            ])

    def test_computeAvailableRights_withAdvancedRemainder(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([
            (1, isodate('2015-08-16'), 0),
            ])
        production = ProductionAggregatorMockUp(
                first=localisodate('2015-08-16'),
                last=localisodate('2015-08-16'),
                data=numpy.array(100*[0]+10*[0]+[1000]+14*[0]))
        plantShare = PlantShareCurverMockup(
                data=numpy.array(100*[0]+25*[1]))
        l = ProductionLoader(productionAggregator=production,
                plantShareCurver=plantShare,
                rightsPerShare=rights,
                remainders=remainders)
        l.computeAvailableRights()
        result = rights.rightsPerShare(1,
            isodate('2015-08-16'),
            isodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.lastRemainders(), [
            (1, isodate('2015-08-17'), 0),
            ])

    def test_retrieveMeasuresFromPlants(self):
        production = ProductionAggregatorMockUp()
        now = datetime.datetime.now()
        start = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        end = (now - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        production.retrieveMeasuresFromPlants(start, end)
        self.assertEqual(production.updateStart, start)
        self.assertEqual(production.updateEnd, end)

# vim: ts=4 sw=4 et
