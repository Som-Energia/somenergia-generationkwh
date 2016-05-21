#!/usr/bin/env python
# -*- coding: utf-8 -*-
from  genkwh_curver import curver_getter
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
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
    
    def test_usageGetter_withNoUsage(self):
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "usage",
            "-s","2016-08-17",
            "-e","2016-08-17", 
            "-f","prueba.csv",
            "1"])
        lines=open('prueba.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,[0]*25))],
            map(str.rstrip,lines)
        )

    def test_usageGetter_withUsage(self):        
        p=self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            1,
            '2015-08-15',
            range(1,25)+[0]
            )
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "usage",
            "-s","2015-08-15",
            "-e","2015-08-15", 
            "-f","prueba2.csv",
            "1"])
        lines=open('prueba2.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

    def test_usageGetter_withUsage_partnerId(self):        
        p=self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            1,
            '2015-08-15',
            range(1,25)+[0]
            )
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "usage",
            "-s","2015-08-15",
            "-e","2015-08-15", 
            "-f","prueba3.csv",
            "--partner",
            "2"])
        lines=open('prueba3.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

    def test_usageGetter_withUsage_code(self):        
        p=self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            1,
            '2015-08-15',
            range(1,25)+[0]
            )
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "usage",
            "-s","2015-08-15",
            "-e","2015-08-15", 
            "-f","prueba4.csv",
            "--number",
            "1"])
        lines=open('prueba4.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,range(1,25)+[0]))],
            map(str.rstrip,lines)
        )

    def test_availableGetter_method_withNoUsage(self):
        call([os.path.dirname(os.path.abspath(__file__))+"/genkwh_curver.py",
            "curver",
            "-s","2014-08-15",
            "-e","2014-08-15", 
            "-f","prueba5.csv",
            "1"])
        lines=open('prueba5.csv', 'rb').readlines()
        self.assertEqual(
            [" ".join(map(str,range(1,26)))," ".join(map(str,[0]*25))],
            map(str.rstrip,lines)
        )

if __name__ == '__main__':
    unittest.main()



