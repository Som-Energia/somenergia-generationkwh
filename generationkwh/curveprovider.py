# -*- coding: utf-8 -*-
import datetime
import numpy

class UnconfiguredDataProvider(Exception):
    pass

class CurveProvider(object):
    """ Provides hourly curves required to track
        generationkwh member usage.
    """

    def __init__(self, shares=None):
        self._shareProvider = shares

    def activeShares(self, member, start, end):
        if self._shareProvider is None:
            raise UnconfiguredDataProvider("MemberSharesProvider")

        def activeSharesADay(day, member):
            return sum(
                share.shares
                for share in self._shareProvider.shareContracts()
                if (member is None or share.member == member)
                and share.end >= day
                and share.start <= day
            )
        hoursADay=25
        nDays=(end-start).days+1
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)
        for i in xrange(nDays):
            day=start+datetime.timedelta(days=i)
            result[i*hoursADay:(i+1)*hoursADay] = activeSharesADay(day,member)
        return result

    def production(self, member, start, end):
        """ Returns acquainted productions rights for
            the member
            within start and end dates, included.
        """

    def usage(self, member, start, end):
        """ Return used production rights for the member
            within start and end dates, included.
        """

    def periodMask(self, fare, period, start, end):
        """ Returns an array for the set of hours
            the period is active por a given fare
            within start and end days, included.
        """

import unittest
from yamlns import namespace as ns

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

class SharesProvider_Mockup(object):
    def __init__(self, shareContracts):
        self._contracts = [
            ns(member=member, start=isodate(start), end=isodate(end), shares=shares)
            for member, start, end, shares in shareContracts
            ]

    def shareContracts(self):
        return self._contracts

class CurveProvider_Test(unittest.TestCase):

    def test_shares_whenNoShareProvider(self):
        curves = CurveProvider()
        with self.assertRaises(UnconfiguredDataProvider) as assertion:
            curves.activeShares('member', isodate('2015-02-21'), isodate('2015-02-21'))
        self.assertEqual(assertion.exception.args[0], "MemberSharesProvider")

    def assertShareCurveEquals(self, member, start, end, shares, expectation):
        sharesprovider = SharesProvider_Mockup(shares)
        curves = CurveProvider(shares = sharesprovider)
        result = curves.activeShares(member, isodate(start), isodate(end))
        self.assertEqual(list(result), expectation)

    def test_shares_singleDay_noShares(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [],
            +25*[0]
        )

    def test_shares_singleDay_singleShare(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
            ],
            +25*[3]
        )

    def test_shares_singleDay_multipleShare(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[8]
            )

    def test_shares_otherMembersIgnored(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[3]
            )

    def test_shares_allMembersCountedIfNoneSelected(self):
        self.assertShareCurveEquals(
            None, '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[8]
            )
 
    def test_shares_expiredActionsNotCounted(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2014-02-21', '2015-02-20', 5),
            ],
            +25*[3]
            )
 
    def test_shares_unactivatedActions(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-22', '2016-02-20', 5),
            ],
            +25*[3]
            )

    def test_shares_twoDays(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-21', '2015-02-22', 3),
            ],
            +25*[3]
            +25*[3]
            )

    def test_shares_lastDaysNotActive(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
            ],
            +25*[3]
            +25*[0]
            )

    def test_shares_firstDaysNotActive(self):
        self.assertShareCurveEquals(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-22', '2015-02-26', 3),
            ],
            +25*[0]
            +25*[3]
            )

    def test_shares_fullCase(self):
        self.assertShareCurveEquals(
            'member', '2015-02-11', '2016-03-11',
            [
                ('member', '2015-02-10', '2015-02-22', 3),
                ('member', '2015-01-11', '2015-02-11', 5),
                ('member', '2015-02-13', '2015-02-14', 7),
                ('member', '2015-02-16', '2015-02-24', 11),
                # ignored
                ('member', '2014-02-12', '2014-02-22', 13), # early
                ('member', '2017-02-12', '2017-02-22', 17), # late
                ('other',  '2015-02-12', '2015-02-22', 21), # other
            ],
            +25*[8] # 11
            +25*[3] # 12
            +25*[10] # 13
            +25*[10] # 14
            +25*[3] # 15
            +25*[14] # 16
            +25*[14] # 17
            +25*[14] # 18
            +25*[14] # 19
            +25*[14] # 20
            +25*[14] # 21
            +25*[14] # 22
            +25*[11] # 23
            +25*[11] # 24
            +25*381*[0] # 25 and so
            )



# vim: ts=4 sw=4 et
