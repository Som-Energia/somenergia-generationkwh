#!/usr/bin/env python

import unittest

from pymongo import Connection
from yamlns import namespace as ns
import json
import numpy
import datetime

class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, uri, collection):
        ""
        self.data=numpy.array([0]*25)

    def get(self, start, stop, filter, field):
        return self.data

    def fillPoint(self, data):
        self.data[-2]=10
        

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

class MongoTimeCurve_Test(unittest.TestCase):

    def setUp(self):
        c = Connection()
        self.databasename = 'generationkwh_test'
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        self.collection = self.db['generation']
        self.dburi = 'mongodb://localhost/{}'.format(self.databasename)


    def tearDown(self):
        c = Connection()
        c.drop_database('generationkwh_test')


    def test_get_whenEmpty(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*25)

    def test_get_withSingleData(self):
        mtc = MongoTimeCurve(self.dburi, self.collection)
        mtc.fillPoint(ns(
            datetime=isodatetime('2015-01-01 23:00:00'),
            name='miplanta',
            ae=10,
            ))

        curve = mtc.get(
            start=isodate('2015-01-01'),
            stop=isodate('2015-01-01'),
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*23+[10,0])


            

        
        




# vim: ts ts=4 sw=4
