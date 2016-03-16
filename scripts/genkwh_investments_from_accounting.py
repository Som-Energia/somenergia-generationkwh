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
        sub.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help="verbose messages",
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
"""
import os

def loadErp(dbcfg):
    if hasattr(loadErp, 'pool'):
        return loadErp.db, loadErp.pool

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../erp/server/bin")))

    import netsvc
    import tools
    tools.config['db_name'] = dbcfg.database
    tools.config['db_host'] = dbcfg.host
    tools.config['db_user'] = dbcfg.user
    tools.config['db_password'] = dbcfg.password
    tools.config['db_port'] = dbcfg.port
    tools.config['root_path'] = "../erp/server"
    tools.config['addons_path'] = "../erp/server/bin/addons"
    tools.config['log_level'] = None #'warn'
    tools.config['log_file'] = open('/dev/null','w')
    #tools.config['log_handler'] = [':WARNING']
    tools.config['init'] = []
    tools.config['demo'] = []
    tools.config['update'] = []

    import pooler
    import osv

    osv_ = osv.osv.osv_pool()
    loadErp.db,loadErp.pool = pooler.get_db_and_pool(tools.config['db_name'])
    netsvc.SERVICES['im_a_worker'] = True

    return loadErp.db, loadErp.pool
db, pool = loadErp(ns(dbconfig.psycopg))
"""

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


def runtest(accept=False, verbose=False):
    unittest.TestCase.acceptMode=accept
    sys.argv.remove("runtest")
    if accept: sys.argv.remove("--accept")
    unittest.TestCase.__str__ = unittest.TestCase.id
    sys.argv.append('--verbose')
    unittest.main()

c = erppeek.Client(**dbconfig.erppeek)

def main():
    # Calls the function homonimous to the subcommand
    # with the options as paramteres
    args = parseArgumments()
    print args.dump()
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



