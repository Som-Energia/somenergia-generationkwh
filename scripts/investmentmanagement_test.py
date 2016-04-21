#!/usr/bin/env python

from genkwh_investments_from_accounting import *

import unittest

dbconfig = None
try:
    import dbconfig
    import erppeek
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentManagement_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"

    def test_clean(self):
        clear()
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_fromPaymentLines_toEarly(self):
        clear()
        create_fromPaymentLines(stop="2015-06-17")
        data = listactive(csv=True)
        self.assertMultiLineEqual(data,"")

    @unittest.skip("TODO: Check why it stopped to work")
    def test_create_fromPaymentLines_firstDay(self):
        clear()
        data = listactive(csv=True)
        create_fromPaymentLines(stop="2015-06-18")
        self.assertMultiLineEqual(data,
            "550\tFalse\tFalse\t3\n"
            "42\tFalse\tFalse\t3\n"
            )

    def test_create_fromPaymentLines_more(self):
        clear()
        create_fromPaymentLines(stop="2015-06-19")
        data = listactive(csv=True)
        self.assertMultiLineEqual(data,
            "550\tFalse\tFalse\t3\n"
            "42\tFalse\tFalse\t3\n"
            "1377\tFalse\tFalse\t20\n"
            "7238\tFalse\tFalse\t15\n"
            "4063\tFalse\tFalse\t70\n"
            "2\tFalse\tFalse\t15\n"
            "2609\tFalse\tFalse\t12\n"
            )
    def test_create_fromPaymentLines_justSecondDay(self):
        clear()
        create_fromPaymentLines(start='2015-06-19', stop="2015-06-19")
        data = listactive(csv=True)
        self.assertMultiLineEqual(data,
            "1377\tFalse\tFalse\t20\n"
            "7238\tFalse\tFalse\t15\n"
            "4063\tFalse\tFalse\t70\n"
            "2\tFalse\tFalse\t15\n"
            "2609\tFalse\tFalse\t12\n"
            )

    def test_create_fromPaymentLines_waitTwoDays(self):
        clear()
        create_fromPaymentLines(stop="2015-06-19", waitingDays=2)
        data = listactive(csv=True)
        self.assertMultiLineEqual(data,
            "550\t20150620T00:00:00\tFalse\t3\n"
            "42\t20150620T00:00:00\tFalse\t3\n"
            "1377\t20150621T00:00:00\tFalse\t20\n"
            "7238\t20150621T00:00:00\tFalse\t15\n"
            "4063\t20150621T00:00:00\tFalse\t70\n"
            "2\t20150621T00:00:00\tFalse\t15\n"
            "2609\t20150621T00:00:00\tFalse\t12\n"
            )

    def test_create_fromPaymentLines_expireOneYear(self):
        clear()
        create_fromPaymentLines(stop="2015-06-19", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertMultiLineEqual(data,
            "550\t20150620T00:00:00\t20160620T00:00:00\t3\n"
            "42\t20150620T00:00:00\t20160620T00:00:00\t3\n"
            "1377\t20150621T00:00:00\t20160621T00:00:00\t20\n"
            "7238\t20150621T00:00:00\t20160621T00:00:00\t15\n"
            "4063\t20150621T00:00:00\t20160621T00:00:00\t70\n"
            "2\t20150621T00:00:00\t20160621T00:00:00\t15\n"
            "2609\t20150621T00:00:00\t20160621T00:00:00\t12\n"
            )

    def test_create_toEarly(self):
        clear()
        create(stop="2015-06-29")
        data = listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_onlyFirstBatch(self):
        clear()
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    @unittest.skip("My current test [DAVID]")
    def test_create_firstBatch_twice(self):
        clear()
        create(stop="2015-06-30")
        create(stop="2015-06-30")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstAndSecondBatch(self):
        clear()
        create(stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        clear()
        create(start='2015-07-02', stop="2015-07-03")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        clear()
        create(stop="2015-06-30", waitingDays=2)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        clear()
        create(stop="2015-06-30", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_inTwoBatches(self):
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(stop="2015-07-03")
        data = listactive(csv=True)

    def test_listactive_withMember(self):
        clear()
        create(stop="2015-06-30")
        data = listactive(csv=True, member=550)
        self.assertMultiLineEqual(data,
            '550\tFalse\tFalse\t3\n'
            '550\tFalse\tFalse\t2\n'
        )

    def test_listactive_withStop_shouldBeFirstBatch(self):
        clear()
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, stop="2015-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStopAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Second batch is not activated, and is not shown even if we extend stop
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        create(start="2015-07-03", stop="2015-07-03")
        data = listactive(csv=True, stop="2020-07-03")
        self.assertB2BEqual(data)

    def test_listactive_withStart_excludeExpired_shouldBeSecondBatch(self):
        # Expired contracts do not show if start is specified and it is earlier
        clear()
        create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = listactive(csv=True, start="2016-07-01")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Unactivated contracts are not listed if start is specified
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # listed
        create(start="2015-07-03", stop="2015-07-03") # unlisted
        data = listactive(csv=True, start="2016-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoExpirationRunForEver_shouldBeSecondBatch(self):
        # Active with no deactivation keeps being active for ever
        clear()
        create(stop="2015-06-30", waitingDays=0, expirationYears=1) # unlisted
        create(start="2015-07-03", stop="2015-07-03", waitingDays=0) # listed
        data = listactive(csv=True, start="2036-06-30")
        self.assertB2BEqual(data)




