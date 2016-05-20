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
def _getter(method,member,start,stop,file):
    curve=method(member,start,stop)
    with open(file, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(range(1,26)*((isodate(stop)-isodate(start)).days+1))
        spamwriter.writerow(curve)

def usage_getter(member,start,stop,file):
    erp=erppeek.Client(**dbconfig.erppeek)
    method=erp.GenerationkwhTesthelper.usage
    _getter(method,member,start,stop,file)

def curver_getter(member,start,stop,file):
    erp=erppeek.Client(**dbconfig.erppeek)
    method=erp.GenerationkwhTesthelper.rights_kwh
    _getter(method,member,start,stop,file)

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest="subcommand",
        )
    curver = subparsers.add_parser('curver')
    usage = subparsers.add_parser('usage')
    for sub in curver,usage:
        sub.add_argument(
            '-s','--start',
            type=str,
            help="Start date",
            )
        sub.add_argument(
            '-e','--end',
            type=str,
            help="End date",
            )
        sub.add_argument(
            '-f','--file',
            type=str,
            help="Output file",
            )
        sub.add_argument(
            'member',
            type=str,
            help="investor of Generation-kWh (see --partner and --number)",
            )

    return parser.parse_args(namespace=ns())

def main():
    args = parseArguments()
    if args.subcommand == "usage":
        usage_getter(args.member,args.start,args.end,args.file)
    else:
        curver_getter(args.member,args.start,args.end,args.file)

if __name__ == '__main__':
    main()
