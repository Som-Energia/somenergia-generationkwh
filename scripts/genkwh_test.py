#!/usr/bin/env python
description = """
Generates investments from the accounting logs.
"""

import erppeek
import dbconfig
import b2btest

import glob
import os
from yamlns import namespace as ns

from remainder_test import *
from holidaysprovider_test import *
#from investmentmanagement_test import *
from usagetracker_test import *
from assignment_test import *
from productionloader_test import *

def parseArgumments():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--accept',
        action='store_true',
        help="accept changed b2b data",
        )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help="verbose messages",
        )
    return parser.parse_args(namespace=ns())

import unittest
import sys

def runtest(accept=False, verbose=False):
    unittest.TestCase.acceptMode=accept
    if accept: sys.argv.remove("--accept")
    unittest.TestCase.__str__ = unittest.TestCase.id
    unittest.main()

def main():
    # Calls the function homonymous to the subcommand
    # with the options as paramteres
    args = parseArgumments()
    print args.dump()
    runtest(**args)

if __name__ == '__main__':
    main()



