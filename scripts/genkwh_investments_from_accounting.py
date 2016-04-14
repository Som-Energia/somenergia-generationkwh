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
    return datetime.datetime.strptime(string, "%Y-%m-%d")

def isodate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def clear(**args):
    allinvestments = c.search('generationkwh.investment')
    c.unlink('generationkwh.investment', allinvestments)

def listactive(member=None, start=None, stop=None, csv=False):
    """
        List active investments between start and stop, both included,
        for the member of for any member if member is None.
        If start is not specified, it lists activated before stop.
        If stop is not specified, it list activated and not deactivated
        before start.
        If neither start or stop are specified all investments are listed
        active or not.
    """
    def buildcsv(data):
        return u''.join((
            u"\t".join((
                unicode(c) for c in line
                ))+'\n'
            for line in data))

    csvdata = buildcsv(c.GenerationkwhInvestment.active_investments(
            member, start and str(start), stop and str(stop)))
    if csv: return csvdata
    print csvdata

def create(start=None, stop=None,
        waitingDays=None,
        expirationYears=None,
        force=False,
        **_):
    if force: clear()

    c.GenerationkwhInvestment.create_investments_from_accounting(
        start, stop, waitingDays, expirationYears)

def create_fromPaymentLines(start=None, stop=None,
        waitingDays=None,
        expirationYears=None,
        force=False,
        **_):
    if force: clear()

    c.GenerationkwhInvestment.create_investments_from_paymentlines(
        start, stop, waitingDays, expirationYears)

# TODO: Tests
# TODO: Move implementation to the ERP side
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

    investments = c.read( 'generationkwh.investment', criteria)

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
        c.write('generationkwh.investment', investment.id, updateDict)

c = erppeek.Client(**dbconfig.erppeek)

def main():
    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    args = parseArgumments()
    print args.dump()
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



