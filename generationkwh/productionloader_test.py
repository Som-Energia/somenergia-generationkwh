# -*- coding: utf-8 -*-

from productionloader import ProductionLoader
import unittest
import datetime

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

class ProductionAggregatorMockUp(object):

    def __init__(self, data):
        self.data = data

    def getWh(self, firstDate):
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







# vim: ts=4 sw=4 et
