#! /usr/bin/env python
# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve
from generationkwh.isodates import isodate
from generationkwh.memberrightsusage import MemberRightsUsage
import pymongo
import csv
from yamlns import namespace as ns
dbname='generationkwh_test'
def curver_getter(dbname,member,start,stop):
    c = pymongo.Connection()                                                                                       
    db = c[dbname]
    p=MemberRightsUsage(db)
    curve=p.usage(member=member,start=isodate(start),stop=isodate(stop))
    with open('test.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(range(1,26)*((isodate(stop)-isodate(start)).days+1))
        spamwriter.writerow(curve)

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
    curver_getter(dbname,args.member,args.start,args.end)

if __name__ == '__main__':
    main()
