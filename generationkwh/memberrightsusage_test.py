# -*- coding: utf-8 -*-

from .memberrightsusage import MemberRightsUsage
import unittest
import pymongo
from .isodates import isodate

class MemberRightsUsage_Test(unittest.TestCase):

    def setUp(self):
        self.databasename = 'generationkwh_test'
        
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]
        
    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database('generationkwh_test')


    def test_usage_withNoUsage(self):
        provider = MemberRightsUsage(self.db)
        usage = provider.usage(
            member='1',
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            )
        self.assertEqual(
            +25*[0],
            list(usage)
            )

    def test_usage_withUsage(self):
        provider = MemberRightsUsage(self.db)
        usage = provider.updateUsage(
            member='1',
            start=isodate('2015-08-15'),
            data=list(range(1,25))+[0],
            )
        usage = provider.usage(
            member='1',
            start=isodate('2015-08-15'),
            stop=isodate('2015-08-15'),
            )
        self.assertEqual(
            list(range(1,25))+[0],
            list(usage),
            )



# vim: ts=4 sw=4 et
