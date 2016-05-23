#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
import erppeek
import dbconfig
import os
from subprocess import call
import sys
import genkwh_curver 

class CurveExporter_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.erp = erppeek.Client(**dbconfig.erppeek)
        self.Investment = self.erp.GenerationkwhInvestment
        self.clear()
        self.member = 1
        self.shares = 26
        self.summerUp = range(1,25)+[0]
        self.summerDown = range(24,0,-1)+[0]

        self.Investment.create_from_accounting(
            self.member, None, '2015-11-19', 0, None)

    def tearDown(self):
        self.clear()

    def clear(self):
        self.Investment.dropAll()
        self.erp.GenerationkwhTesthelper.clear_mongo_collections([
            'rightspershare',
            'memberrightusage',
            ])

    def assertCsvByColumnEqual(self, csv, columns):
        self.assertMultiLineEqual(
            csv,
            '\n'.join(
                '\t'.join( str(v) for v in row)
                for row in zip(*columns)
                )
            )

    def setupRights(self, shares, firstDate, data):
        self.erp.GenerationkwhTesthelper.setup_rights_per_share(
            shares, firstDate, data)

    def setupUsage(self, member, firstDate, data):
        self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            member, firstDate, data)

    def test_dump(self):

        usage = self.summerUp + self.summerDown
        rights = self.summerDown + self.summerUp

        self.setupRights(self.shares, '2015-08-15', rights)
        self.setupUsage(self.member, '2015-08-15', usage)

        csv = genkwh_curver.dump(
            member=self.member,
            first=genkwh_curver.isodate('2015-08-15'),
            last =genkwh_curver.isodate('2015-08-17'),
            returnCsv=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['rights']+ rights+25*[0],
                ['usage'] + usage+25*[0],
            ])

    def test_dump_withMemberShares(self):

        usage = range(24,0,-1)+[0]
        rights = range(1,25)+[0]

        self.setupRights(self.shares, '2015-08-15', rights)
        self.setupUsage(self.member, '2015-08-15', usage)

        csv = genkwh_curver.dump(
            member=self.member,
            first=genkwh_curver.isodate('2015-08-15'),
            last =genkwh_curver.isodate('2015-08-15'),
            returnCsv=True,
            dumpMemberShares=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['memberShares']+ 25*[self.shares],
                ['rights']+ rights,
                ['usage'] + usage,
            ])


    def test_dump_withMemberShares_changing(self):

        usage = self.summerUp + self.summerDown
        rights = self.summerDown + self.summerUp
        zeroday = 25*[0]

        self.setupRights(self.shares, '2015-07-28', rights)
        self.setupUsage(self.member, '2015-07-28', usage)

        csv = genkwh_curver.dump(
            member=self.member,
            first=genkwh_curver.isodate('2015-07-27'),
            last =genkwh_curver.isodate('2015-07-30'),
            returnCsv=True,
            dumpMemberShares=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['memberShares']+ 2*25*[self.shares-1]+2*25*[self.shares],
                ['rights']+ 2*zeroday + rights[25:] + zeroday,
                ['usage'] + zeroday + usage + zeroday,
            ])

    def test_dump_withMemberShares_changingAndRights(self):

        usage = self.summerUp + self.summerDown
        rights = self.summerDown + self.summerUp
        zeroday = 25*[0]

        self.setupRights(self.shares, '2015-07-28', rights)
        self.setupRights(self.shares-1, '2015-07-28', 25*[4])
        self.setupUsage(self.member, '2015-07-28', usage)

        csv = genkwh_curver.dump(
            member=self.member,
            first=genkwh_curver.isodate('2015-07-27'),
            last =genkwh_curver.isodate('2015-07-30'),
            returnCsv=True,
            dumpMemberShares=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['memberShares']+ 2*25*[self.shares-1]+2*25*[self.shares],
                ['rights']+ zeroday + 24*[4]+[0]+ rights[25:] + zeroday,
                ['usage'] + zeroday + usage + zeroday,
            ])



if __name__ == '__main__':
    unittest.main()



