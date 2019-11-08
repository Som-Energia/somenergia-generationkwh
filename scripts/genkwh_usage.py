#!/usr/bin/env python
description = """
Manage rights usage data
"""

import datetime
import erppeek
import dbconfig
from yamlns import namespace as ns
from somutils.sequence import sequence

from generationkwh.isodates import isodate
import numpy as np

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest='subcommand',
        )
    clear = subparsers.add_parser('clear',
        help="clear usage",
        )
    return parser.parse_args(namespace=ns())

def clear():
    genkwh_obj = c.model('generationkwh.testhelper')
    genkwh_obj.clear_mongo_collections([
            'memberrightusage',
            ])
 
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
