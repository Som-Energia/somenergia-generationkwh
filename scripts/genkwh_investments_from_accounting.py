#!/usr/bin/env python
description = """
Generates investments from the accounting logs.
"""

import erppeek
import datetime
from dateutil.relativedelta import relativedelta
import dbconfig
from yamlns import namespace as ns

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    runtest = subparsers.add_parser('runtest',
        help="runs tests",
        )
    listactive = subparsers.add_parser('listactive',
        help="list active investments objects",
        )
    create = subparsers.add_parser('create',
        help="create investments objects from accounting information",
        )
    activate = subparsers.add_parser('activate',
        help="activate the investments",
        )
    clear = subparsers.add_parser('clear',
        help="clear investments objects",
        )
    extend = subparsers.add_parser('extend',
        help="extend the expiration date of a set of investments",
        )
    for sub in runtest,: 
        sub.add_argument(
            '--accept',
            action='store_true',
            help="accept changed b2b data",
            )
    for sub in activate,create: 
        sub.add_argument(
            '--force',
            action='store_true',
            help="do it even if they where already computed",
            )
    for sub in listactive,: 
        sub.add_argument(
            '--member',
            type=int,
            metavar='MEMBERID',
            help="filter by member",
            )
    for sub in activate,create,clear,listactive: 
        sub.add_argument(
            '--start',
            type=isodate,
            metavar='ISODATE',
            help="first purchase date to be considered",
            )
        sub.add_argument(
            '--stop',
            type=isodate,
            metavar='ISODATE',
            help="last purchase date to be considered",
            )
    for sub in activate,create: 
        sub.add_argument(
            '--wait',
            '-w',
            dest='waitingDays',
            type=int,
            metavar='DAYS',
            help="number of days from the purchase date until "
                "they provide usufruct",
            )
        sub.add_argument(
            '--expires',
            '-x',
            dest='expirationYears',
            type=int,
            metavar='YEARS',
            help="number of years the shares will provide usufruct"
            )
    return parser.parse_args(namespace=ns())

def isodatetime(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def clear(**args):
    allinvestments = c.search('generationkwh.investments')
    c.unlink('generationkwh.investments', allinvestments)

def listactive(member=None, start=None, stop=None, csv=False):
    def buildcsv(data):
        return u''.join((
            u"\t".join((
                unicode(c) for c in line
                ))+'\n'
            for line in data))

    csvdata = buildcsv(c.GenerationkwhInvestments.active_investments(
            member, start and str(start), stop and str(stop)))
    if csv: return csvdata
    print csvdata

def create(start=None, stop=None,
        waitingDays=None,
        expirationYears=None,
        force=False,
        **_):
    if force: clear()

    c.GenerationkwhInvestments.create_investments_from_accounting(
        start, stop, waitingDays, expirationYears)

def create_fromPaymentLines(start=None, stop=None,
        waitingDays=None,
        expirationYears=None,
        force=False,
        **_):
    if force: clear()

    c.GenerationkwhInvestments.create_investments_from_paymentlines(
        start, stop, waitingDays, expirationYears)

def activate(
        waitingDays,
        start=None, stop=None,
        expirationYears=None,
        force=False,
        **_):
    criteria = []
    if not force: criteria.append(('activation_date', '=', False))
    if stop: criteria.append(('purchase_date', '<=', str(stop)))
    if start: criteria.append(('purchase_date', '>=', str(start)))

    investments = c.read( 'generationkwh.investments', criteria)

    for investment in investments:
        investment = ns(investment)
        updateDict = dict(
            activation_date=(
                str(isodate(investment.purchase_date)
                    +relativedelta(days=waitingDays))
                ),
            )
        if expirationYears:
            updateDict.update(
                deactivation_date=(
                    str(isodate(investment.purchase_date)
                        +relativedelta(
                            years=expirationYears,
                            days=waitingDays,
                            )
                        )
                    ),
                )
        c.write('generationkwh.investments', investment.id, updateDict)

import unittest
import b2btest
import sys
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

    def test_create_firstAndSecondBatch(self):
        clear()
        create(stop="2015-07-31")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        clear()
        create(start='2015-06-30', stop="2015-07-31")
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        clear()
        create(stop="2015-06-19", waitingDays=2)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        clear()
        create(stop="2015-06-19", waitingDays=2, expirationYears=1)
        data = listactive(csv=True)
        self.assertB2BEqual(data)

def runtest(accept=False):
    unittest.TestCase.acceptMode=accept
    sys.argv.remove("runtest")
    if accept: sys.argv.remove("--accept")
    unittest.main()

c = erppeek.Client(**dbconfig.erppeek)

def main():
    args = parseArgumments()
    print args.dump()
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



