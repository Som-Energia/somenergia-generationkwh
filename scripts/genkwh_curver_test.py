#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from  genkwh_curver import usage_getter
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.isodates import isodate
import erppeek
import dbconfig
import os
from subprocess import call
import sys
class CurverGetter_Test(unittest.TestCase):
    def setUp(self):
        self.erp = erppeek.Client(**dbconfig.erppeek)

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database('generationkwh_test')
    
    def test_curverGetter_withNoUsage(self):
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "-s","2015-08-16",
            "-e","2015-08-16", 
            "1"])
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
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "-s","2015-08-15",
            "-e","2015-08-15", 
            "1"])
        lines=open('test.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

if __name__ == '__main__':
    unittest.main()
    


