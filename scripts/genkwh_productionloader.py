#!/usr/bin/env python
description = """
Calculate rights per share
"""

import erppeek
import dbconfig
from yamlns import namespace as ns
from consolemsg import step, success
from dateutil.relativedelta import relativedelta
from generationkwh.isodates import isodate

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    computerights = subparsers.add_parser('computerights',
        help="Generates new rights available",
        )
    recompute = subparsers.add_parser('recompute',
        help="Recompute rights granting existing ones (and compensating)",
        )
    for sub in computerights, recompute:
        sub.add_argument(
            '--id',
            dest='id',
            type=int,
            metavar='ID',
            help="aggregator id"
            )
    return parser.parse_args(namespace=ns())

def computerights(id=None):
    Remainder = c.GenerationkwhRemainderTesthelper
    RightsGranter = c.GenerationkwhRightsGranter
    step("Next day to compute (nshares, date):")
    for nshares, day, remainderWh in sorted(Remainder.lastRemainders()):
        print nshares, day
    step("Computing production rights for each number of shares...")
    log = RightsGranter.computeAvailableRights(id)
    success(log)
    step("Next day to compute after update...")
    for nshares, day, remainderWh in sorted(Remainder.lastRemainders()):
        print nshares, day

def recompute(id=None):
    Mix = c.GenerationkwhProductionAggregatorTesthelper
    Remainder = c.GenerationkwhRemainderTesthelper
    RightsGranter = c.GenerationkwhRightsGranter
    firstDate=Mix.firstActiveDate(id)
    lastRemainderDate = max(
        day
        for nshares, day, remainderWh
        in Remainder.lastRemainders()
    )
    lastDate = str(isodate(lastRemainderDate)-relativedelta(days=1))
    step("Recomputing rights from {} to {}:", firstDate, lastDate)
    log = RightsGranter.recomputeRights(id, firstDate, lastDate)
    success(log)
    step("Next day to compute after update...")
    for nshares, day, remainderWh in sorted(Remainder.lastRemainders()):
        print nshares, day

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
