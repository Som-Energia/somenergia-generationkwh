# -*- coding: utf-8 -*-

from .rightspershare import RightsPerShare
import unittest
import pymongo
import datetime
from .isodates import localisodate

class RightsPerShare_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        
        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        
    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')


    def test_usage_withNoUsage(self):
        provider = RightsPerShare(self.db)
        rightsPerShare = provider.rightsPerShare(
            nshares='1',
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
            )
        self.assertEqual(
            +25*[0],
            list(rightsPerShare)
            )

    def test_usage_withUsage(self):
        provider = RightsPerShare(self.db)
        provider.updateRightsPerShare(
            nshares='1',
            start=localisodate('2015-08-15'),
            data=range(1,25)+[0],
            )
        rightsPerShare = provider.rightsPerShare(
            nshares='1',
            start=localisodate('2015-08-15'),
            stop=localisodate('2015-08-15'),
            )
        self.assertEqual(
            range(1,25)+[0],
            list(rightsPerShare),
            )



# vim: ts=4 sw=4 et
