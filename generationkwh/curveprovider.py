# -*- coding: utf-8 -*-
import datetime
import numpy


class CurveProvider(object):
    """ Provides hourly curves required to track
        generationkwh member usage.
    """

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


class UnconfiguredDataProvider(Exception):
    pass

class ActiveSharesCurve(object):
    """ Provides the shares that are active at a give
        day, or either daily or hourly in a date span.
        You need to feed this object with an investment
        provider.
    """
    def __init__(self, investments=None):
        self._investmentProvider = investments

    def atDay(self, member, day):
        if self._investmentProvider is None:
            raise UnconfiguredDataProvider("InvestmentProvider")

        return sum(
            investment.shares
            for investment in self._investmentProvider.shareContracts()
            if (member is None or investment.member == member)
            and investment.activationEnd >= day
            and investment.activationStart <= day
        )

    def hourly(self, member, start, end):

        if end<start:
            return numpy.array([], dtype=int)

        hoursADay=25
        nDays=(end-start).days+1
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)
        for i in xrange(nDays):
            day=start+datetime.timedelta(days=i)
            result[i*hoursADay:(i+1)*hoursADay] = self.atDay(member, day)
        return result

import unittest
from yamlns import namespace as ns

def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()

class InvestmentProvider_MockUp(object):
    def __init__(self, shareContracts):
        self._contracts = [
            ns(
                member=member,
                activationStart=isodate(start),
                activationEnd=isodate(end),
                shares=shares,
                )
            for member, start, end, shares in shareContracts
            ]

    def shareContracts(self):
        return self._contracts

class ActiveSharesCurve_Test(unittest.TestCase):

    def test_atDay(self):
        curve = ActiveSharesCurve()
        with self.assertRaises(UnconfiguredDataProvider) as assertion:
            curve.atDay('member', isodate('2015-02-21'))
        self.assertEqual(assertion.exception.args[0], "InvestmentProvider")

    def assert_atDay_equal(self, member, day, investments, expectation):
        investmentsProvider = InvestmentProvider_MockUp(investments)
        curve = ActiveSharesCurve(investments = investmentsProvider)
        self.assertEqual(expectation, curve.atDay(member, isodate(day)))

    def test_atDay_noShares(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [],
            0
        )

    def test_atDay_singleShare(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
            ],
            3
        )

    def test_atDay_multipleShares_getAdded(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-21', '2015-02-21', 5),
            ],
            8
            )

    def test_atDay_otherMembersIgnored(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            3
            )

    def test_atDay_allMembersCountedIfNoneSelected(self):
        self.assert_atDay_equal(
            None, '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            8
            )
 
    def test_atDay_expiredActionsNotCounted(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2014-02-21', '2015-02-20', 5),
            ],
            3
            )
 
    def test_atDay_unactivatedActions(self):
        self.assert_atDay_equal(
            'member', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-22', '2016-02-20', 5),
            ],
            3
            )

    def test_hourly_whenNoShareProvider(self):
        curve = ActiveSharesCurve()
        with self.assertRaises(UnconfiguredDataProvider) as assertion:
            curve.hourly('member', isodate('2015-02-21'), isodate('2015-02-21'))
        self.assertEqual(assertion.exception.args[0], "InvestmentProvider")

    def assertActiveSharesEqual(self, member, start, end, investments, expectation):
        provider = InvestmentProvider_MockUp(investments)
        curve = ActiveSharesCurve(investments = provider)
        result = curve.hourly(member, isodate(start), isodate(end))
        self.assertEqual(list(result), expectation)

    def test_hourly_singleDay_noShares(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [],
            +25*[0]
        )

    def test_hourly_singleDay_singleShare(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
            ],
            +25*[3]
        )

    def test_hourly_singleDay_multipleShare(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[8]
            )

    def test_hourly_otherMembersIgnored(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[3]
            )

    def test_hourly_allMembersCountedIfNoneSelected(self):
        self.assertActiveSharesEqual(
            None, '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('other', '2015-02-21', '2015-02-21', 5),
            ],
            +25*[8]
            )
 
    def test_hourly_expiredActionsNotCounted(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2014-02-21', '2015-02-20', 5),
            ],
            +25*[3]
            )
 
    def test_hourly_unactivatedActions(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-22', '2016-02-20', 5),
            ],
            +25*[3]
            )

    def test_hourly_twoDays(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-21', '2015-02-22', 3),
            ],
            +25*[3]
            +25*[3]
            )

    def test_hourly_lastDaysNotActive(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
            ],
            +25*[3]
            +25*[0]
            )

    def test_hourly_firstDaysNotActive(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-22',
            [
                ('member', '2015-02-22', '2015-02-26', 3),
            ],
            +25*[0]
            +25*[3]
            )

    def test_hourly_swappedDatesReturnsEmpty(self):
        self.assertActiveSharesEqual(
            'member', '2016-02-21', '2015-02-22',
            [
            ],
            []
            )

    def test_hourly_fullCase(self):
        self.assertActiveSharesEqual(
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
