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
    list = subparsers.add_parser('list',
        help="list investments objects",
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
    """
    for sub in activate,create: 
        sub.add_argument(
            '--force',
            action='store_true',
            help="do it even if they where already computed",
            )
"""
    for sub in list,: 
        sub.add_argument(
            '--member',
            type=int,
            metavar='MEMBERID',
            help="filter by member",
            )
    for sub in activate,create,clear,list: 
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
            dest='waitingMonths',
            type=int,
            metavar='DAYS',
            help="number of days from the purchase date until they provide usufruct"
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

def list(member=None, start=None, stop=None):
    print u'\n'.join(( u"\t".join([unicode(c) for c in line])
        for line in c.GenerationkwhInvestments.get_list(
            member=member, start=start, end=stop)
        ))

def create(start=None, stop=None, waitingMonths=None, expirationYears=None, **_):
    clear()
    criteria = [('name','like','GKWH')]
    if stop: criteria.append(('create_date', '<=', str(stop)))
    if start: criteria.append(('create_date', '>=', str(start)))

    paymentlines = c.read( 'payment.line', criteria)

    for payment in paymentlines:
        payment = ns(payment)
        c.create('generationkwh.investments', dict(
            member_id=payment.partner_id[0],
            nshares=-payment.amount_currency//100,
            purchase_date=payment.create_date,
            activation_date=(
                None if waitingMonths is None else
                str(isodatetime(payment.create_date)
                    +relativedelta(months=waitingMonths))
                ),
            deactivation_date=(
                None if waitingMonths is None else
                None if expirationYears is None else
                str(isodatetime(payment.create_date)
                    +relativedelta(
                        years=expirationYears,
                        months=waitingMonths,
                        )
                    )
                ),
            ))

c = erppeek.Client(**dbconfig.erppeek)

def main():
    args = parseArgumments()
    print args.dump()
    subcommand = args.subcommand
    del args.subcommand
    globals()[subcommand](**args)

if __name__ == '__main__':
    main()



