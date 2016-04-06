# -*- coding: utf-8 -*-

from productionloader import ProductionLoader
import unittest
import datetime

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

class ProductionAggregatorMockUp(object):

    def __init__(self, data, startDate, endDate):
        self.data = data
        self.start_date = startDate
        self.end_date = endDate
    def getWh(self, *args):
        return self.data

    def getFirstMeasurement(self):
        return self.startDate

    def getLastMeasurementDate(self):
        return self.endDate

class RemainderProviderMockup(object):
    
    def get(self):
        return self.remainders
    def set(self, nshares, date, rem):
        self.remaniders=[(nshares, date, rem) if x[0]==nshares else x for x in self.remainders]
        
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

    def test_startPoint_withSingleRemainder(self):
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
    
    def test_doit(self):
        pass






# vim: ts=4 sw=4 et
