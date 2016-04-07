# -*- coding: utf-8 -*-

from .productionloader import ProductionLoader
import unittest
import datetime
import pymongo
from .rightspershare import RightsPerShare
from plantmeter.mongotimecurve import toLocal

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def localisodate(string):
    return toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

class ProductionAggregatorMockUp(object):

    def __init__(self, data=None, startDate=None, endDate=None):
        self.data = data
        self.start_date = startDate
        self.end_date = endDate
    def getWh(self, *args):
        return self.data

    def getFirstMeasurementDate(self):
        return self.start_date

    def getLastMeasurementDate(self):
        return self.end_date

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
    
    def test_getRecomputeStart_withNoremainders(self):
        p = ProductionAggregatorMockUp(startDate=isodate('2000-01-01'))
        r = RemainderProviderMockup()
        l = ProductionLoader(productionAggregator=p, remainderProvider=r)
        recomputeStart, remainders = l.getRecomputeStart()
        self.assertEqual(('2000-01-01',[]), (str(recomputeStart),remainders))
    
    def test_getRecomputeStart_withSingleRemainders(self):
        p = ProductionAggregatorMockUp(startDate=isodate('2000-01-01'))
        r = RemainderProviderMockup([(1,'2001-01-01', 45)])
        l = ProductionLoader(productionAggregator=p, remainderProvider=r)
        recomputeStart, remainders = l.getRecomputeStart()
        self.assertEqual(('2001-01-01',[(1,'2001-01-01', 45)]), (str(recomputeStart),remainders))

    def test_getRecomputeStart_withManyRemainders(self):
        p = ProductionAggregatorMockUp(startDate=isodate('2000-01-01'))
        r = RemainderProviderMockup([(1,'2002-01-01', 45),(2,'2001-01-01',45)])
        l = ProductionLoader(productionAggregator=p, remainderProvider=r)
        recomputeStart, remainders = l.getRecomputeStart()
        self.assertEqual(('2001-01-01',[(1,'2002-01-01', 45),(2,'2001-01-01',45)]), (str(recomputeStart),remainders))

    def setUp(self):
        self.databasename = 'generationkwh_test'
        
        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        
    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')


    def test_appendRightsPerShare(self):
        import numpy
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShareProvider=rights, remainderProvider=remainders)
        l.appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(25*[1]),
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(1, localisodate('2015-08-16'), localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-16'), 0),
            ])

    def test_appendRightsPerShare_withAdvancedRemainder(self):
        import numpy
        rights = RightsPerShare(self.db)
        remainders = RemainderProviderMockup([])
        l = ProductionLoader(rightsPerShareProvider=rights, remainderProvider=remainders)
        l.appendRightsPerShare(
            nshares=1,
            lastComputedDate=localisodate('2015-08-15'),
            lastRemainder=0,
            production=numpy.array(100*[0]+10*[0]+[1000]+14*[0]),
            plantshares=numpy.array(100*[0]+25*[1]),
            lastProductionDate=localisodate('2015-08-16'),
            )
        result = rights.rightsPerShare(1, localisodate('2015-08-16'), localisodate('2015-08-16'))
        self.assertEqual(list(result),
            +10*[0]+[1]+14*[0])
        self.assertEqual(remainders.get(), [
            (1, localisodate('2015-08-16'), 0),
            ])

# vim: ts=4 sw=4 et
