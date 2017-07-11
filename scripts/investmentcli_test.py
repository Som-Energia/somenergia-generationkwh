#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genkwh_investments import *

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentCommand_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        clear()

    def tearDown(self):
        clear()

    def test_clean(self):
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_toEarly(self):
        create(stop="2015-06-29")
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_onlyFirstBatch(self):
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstBatch_twice(self):
        create(stop="2015-06-30")
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstAndSecondBatch(self):
        create(stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        create(start='2015-07-02', stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        create(stop="2015-06-30", waitingDays=2)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        create(stop="2015-06-30", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_inTwoBatches(self):
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(stop="2015-07-03")
        data = listactive(csv=True)

    def test_listactive_withMember(self):
        create(stop="2015-06-30")
        data = listactive(csv=True, member=469)
        self.assertMultiLineEqual(data,
            '469\tFalse\tFalse\t3\n'
            '469\tFalse\tFalse\t2\n'
        )

    def test_listactive_withStop_shouldBeFirstBatch(self):
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, stop="2015-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStopAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Second batch is not activated, and is not shown even if we extend stop
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(start="2015-07-03", stop="2015-07-03")
        data = listactive(csv=True, stop="2020-07-03")
        self.assertB2BEqual(data)

    def test_listactive_withStart_excludeExpired_shouldBeSecondBatch(self):
        # Expired contracts do not show if start is specified and it is earlier
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, start="2016-07-01")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Unactivated contracts are not listed if start is specified
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # listed
        create(start="2015-07-03", stop="2015-07-03") # unlisted
        data = listactive(csv=True, start="2016-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoExpirationRunForEver_shouldBeSecondBatch(self):
        # Active with no deactivation keeps being active for ever
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # unlisted
        create(start="2015-07-03", stop="2015-07-03", waitingDays=0) # listed
        data = listactive(csv=True, start="2036-06-30")
        self.assertB2BEqual(data)


    def test_activate_withStop(self):
        create(stop="2015-07-03")
        effective(stop="2015-06-30", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withStart(self):
        create(stop="2015-07-03")
        effective(start="2015-07-02", waitingDays=0)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_activate_withExpiration(self):
        create(stop="2015-07-03")
        effective(stop="2015-06-30", waitingDays=0, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)







