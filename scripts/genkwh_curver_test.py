# -*- coding: utf-8 -*-
#!/usr/bin/env python
from  genkwh_curver import curver_getter
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.isodates import isodate

class CurverGetter_Test(unittest.TestCase):
    def setUp(self):
        self.databasename = 'generationkwh_test'
        c = pymongo.Connection()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')
    
    def test_curverGetter_withNoUsage(self):
        curver_getter(self.databasename,'1','2015-08-15','2015-08-15')
        lines=open('test.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,[0]*25))],
            map(str.rstrip,lines)
        )
    def test_curverGetter_withUsage(self):        
        p=MemberRightsUsage(self.db)
        usage = p.updateUsage(
            member="1",
            start=isodate('2015-08-15'),
            data=range(1,25)+[0]
            )
        curver_getter(self.databasename,'1','2015-08-15','2015-08-15')
        lines=open('test.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

if __name__ == '__main__':
    unittest.main()
    


