# -*- coding: utf-8 -*-
#!/usr/bin/env python
from  genkwh_curver import usage_getter
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.isodates import isodate
import erppeek
import dbconfig

class CurverGetter_Test(unittest.TestCase):
    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')
    
    def test_curverGetter_withNoUsage(self):
        usage_getter('1','2015-08-16','2015-08-16')
        lines=open('test.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,[0]*25))],
            map(str.rstrip,lines)
        )
    def test_curverGetter_withUsage(self):        
        p=self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            "1",
            '2015-08-15',
            range(1,25)+[0]
            )
        usage_getter('1','2015-08-15','2015-08-15')
        lines=open('test.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

if __name__ == '__main__':
    unittest.main()
    


