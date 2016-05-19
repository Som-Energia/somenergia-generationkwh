#! /usr/bin/env python
# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve
from generationkwh.isodates import isodate
from generationkwh.memberrightsusage import MemberRightsUsage
import pymongo
import csv
from yamlns import namespace as ns
import erppeek
import dbconfig

dbname='generationkwh_test'
def _getter(method,member,start,stop):
    curve=method(member,start,stop)
    with open('test.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(range(1,26)*((isodate(stop)-isodate(start)).days+1))
        spamwriter.writerow(curve)

def usage_getter(member,start,stop):
    erp=erppeek.Client(**dbconfig.erppeek)
    method=erp.GenerationkwhTesthelper.usage
    _getter(method,member,start,stop)

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '-s','--start',
        type=str,
        help="Start date",
        )
    parser.add_argument(
        '-e','--end',
        type=str,
        help="End date",
        )
    parser.add_argument(
        'member',
        type=str,
        help="investor of Generation-kWh (see --partner and --number)",
        )

    return parser.parse_args(namespace=ns())

def main():
    args = parseArguments()
    usage_getter(args.member,args.start,args.end)

if __name__ == '__main__':
    main()
