# -*- coding: utf-8 -*-

class CurveProvider(object):
    """ Provides hourly curves required to track
        generationkwh member usage.
    """

    def __init__(self, shares=None):
        self._shareProvider = shares

    def activeShares(self, member, start, end):
        return +25*((end-start).days+1)*[
            sum(
                share.shares
                for share in self._shareProvider.shareContracts()
                if (member is None or share.member == member)
                and share.end >= start
                and share.start <= start # TODO: wrong on purpose
            )]

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
    import datetime
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

    def assertShareCurveEquals(self, member, start, end, shares, expectation):
        sharesprovider = SharesProvider_Mockup(shares)
        curves = CurveProvider(shares = sharesprovider)
        result = curves.activeShares(member, isodate(start), isodate(end))
        self.assertEqual(result, expectation)

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



# vim: ts=4 sw=4 et
