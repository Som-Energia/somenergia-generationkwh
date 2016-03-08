#!/usr/bin/env python

import unittest

from pymongo import Connection
from yamlns import namespace as ns
import json

class MongoTimeCurve(object):
    """Consolidates curve data in a mongo database"""

    def __init__(self, uri, collection):
        ""

    def get(self, start, stop, filter, field):
        return [0]*25

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
            start='2015-01-01',
            stop='2015-01-01',
            filter='miplanta',
            field='ae',
            )
        self.assertEqual(
            list(curve),
            [0]*25)


            

        
        




# vim: ts ts=4 sw=4
