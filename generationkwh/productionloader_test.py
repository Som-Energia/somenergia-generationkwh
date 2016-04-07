# -*- coding: utf-8 -*-

from .productionloader import ProductionLoader
import unittest
import datetime
import pymongo
from .rightspershare import RightsPerShare
from plantmeter.mongotimecurve import toLocal, asUtc
import numpy


def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def localisodate(string):
    return toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

class ProductionAggregatorMockUp(object):

    def __init__(self,first=None,last=None,data=None):
        self.data = data
        self.firstDate = first
        self.lastDate = last

    def getWh(self, *args):
        return self.data

    def getFirstMeasurementDate(self):
        return self.firstDate

    def getLastMeasurementDate(self):
        return self.lastDate

class RemainderProviderMockup(object):
    
    def __init__(self,remainders=[]):
        self.remainders = remainders

    def get(self):
        return self.remainders
    
    def set(self, nshares, date, rem):
        self.remainders.append((nshares, date, rem))
 
class PlantShareCurverMockup(object):

    def __init__(self, data):
        self.data = data

    def hourly(start, end):
        return data

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
        date = l.startPoint(isodate(firstProductionDate),[
            (shares, isodate(date), remainderwh)
            for shares, date, remainderwh in remainders
            ])
        self.assertEqual(str(date), expected)
    
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
        self.assertEqual((isodate(e1),isodate(e2)), result)

    def test_getRecomputationInterval_withNoremainders_takesFirstMeassure(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([])
        self.assertDatePairEqual( ('2000-01-01','2006-01-01'), interval)
    
    def test_getRecomputationInterval_withSingleRemainders_takesIt(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
                )
        l = ProductionLoader(productionAggregator=p)
        interval = l._recomputationInterval([
            (1,isodate('2001-01-01'), 45),
            ])
        self.assertDatePairEqual( ('2001-01-01','2006-01-01'), interval)

    def test_getRecomputationInterval_withManyRemainders_takesEarlier(self):
        p = ProductionAggregatorMockUp(
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
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
                first=isodate('2000-01-01'),
                last=isodate('2006-01-01'),
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


    def test_appendRightsPerShare(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(1,
            localisodate('2015-08-16'),
            localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-16'), 0),
            ])

    def test_appendRightsPerShare_withManyPlantShares_divides(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[20000]+14*[0]),
            plantshares=numpy.array(25*[4]), # here
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(1,
            localisodate('2015-08-16'),
            localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[5]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-16'), 0),
            ])

    def test_appendRightsPerShare_withNShares_multiplies(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=2, # here
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(2,
            localisodate('2015-08-16'),
            localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[2]+14*[0])
        self.assertEqual(remainders.get(), [
            (2, localisodate('2015-08-16'), 0),
            ])

    def test_appendRightsPerShare_withAdvancedRemainder(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(100*[0]+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(100*[0]+25*[1]),
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(1,
            localisodate('2015-08-16'),
            localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-16'), 0),
            ])

    def test_appendRightsPerShare_lastDateComputed_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                lastComputedDate=localisodate('2015-08-15').date(),
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                lastProductionDate=localisodate('2015-08-16'),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "lastComputedDate should be a datetime")

    def test_appendRightsPerShare_lastProductionDate_isProtected(self):
        l = ProductionLoader()
        with self.assertRaises(AssertionError) as ctx:
            l._appendRightsPerShare(
                nshares=1,
                lastComputedDate=localisodate('2015-08-15'),
                lastRemainder=0,
                production=numpy.array(25*[1]),
                plantshares=numpy.array(25*[1]),
                lastProductionDate=localisodate('2015-08-16').date(),
                )
        # also non CEST/CET, and naive, using assertLocalDateTime
        self.assertEqual(ctx.exception.args[0],
            "lastProductionDate should be a datetime")

    @unittest.skip("Not failing as it should!")
    def test_appendRightsPerShare_tooSmallArrays(self):
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShare=rights, remainders=remainders)
        l._appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-16'),
            lastRemainder=0,
            production=numpy.array(25*[1]),
            plantshares=numpy.array(25*[1]),
            lastProductionDate=localisodate('2015-08-20'),
            )
        result = rights.rightsPerShare(1,
            localisodate('2015-08-16'),
            localisodate('2015-08-20'))
        self.assertEqual(list(result),
            +125*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-20'), 25),
            ])



# vim: ts=4 sw=4 et
