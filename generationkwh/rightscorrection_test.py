# -*- coding: utf-8 -*-

from .rightscorrection import RightsCorrection
import unittest
import pymongo
import datetime
from .isodates import isodate

class RightsCorrection_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        
    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database('generationkwh_test')


    def test_usage_withNoUsage(self):
        provider = RightsCorrection(self.db)
        rightsCorrection = provider.rightsCorrection(
            nshares='1',
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            )
        self.assertEqual(
            +25*[0],
            list(rightsCorrection)
            )

    def test_usage_withUsage(self):
        provider = RightsCorrection(self.db)
        provider.updateRightsCorrection(
            nshares='1',
            start=isodate('2015-08-15'),
            data=list(range(1,25))+[0],
            )
        rightsCorrection = provider.rightsCorrection(
            nshares='1',
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            )
        self.assertEqual(
            list(range(1,25))+[0],
            list(rightsCorrection),
            )



# vim: ts=4 sw=4 et
