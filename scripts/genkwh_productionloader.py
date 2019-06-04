#!/usr/bin/env python
description = """
Calculate rights per share
"""

import erppeek
import dbconfig
from yamlns import namespace as ns

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    computerights = subparsers.add_parser('computerights',
        help="compute rights",
        )
    for sub in computerights,:
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
    step("Next day to compute (nshares, date):")
    for nshares, day, remainderWh in sorted(Remainder.lastRemainders()):
        print nshares, day
    step("Computing production rights for each number of shares...")
    productionloader_obj = c.GenerationkwhProductionLoader
    productionloader_obj.computeAvailableRights(id)
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
