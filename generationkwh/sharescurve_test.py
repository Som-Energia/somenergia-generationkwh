# -*- coding: utf-8 -*-

from sharescurve import UnconfiguredDataProvider, MemberSharesCurve, PlantSharesCurve

import unittest
from yamlns import namespace as ns
import datetime

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

class MemberSharesCurve_Test(unittest.TestCase):

    def assert_atDay_equal(self, member, day, investments, expectation):
        investmentsProvider = InvestmentProvider_MockUp(investments)
        curve = MemberSharesCurve(investments = investmentsProvider)
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


    def assertActiveSharesEqual(self, member, start, end, investments, expected):
        provider = InvestmentProvider_MockUp(investments)
        curve = MemberSharesCurve(investments = provider)
        result = curve.hourly(member, isodate(start), isodate(end))
        self.assertEqual(list(result), expected)

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
class PlantProvider_MockUp(object):
    def __init__(self, sharePlants):
        self._plants = [
            ns(
                plant=plant,
                activationStart=isodate(start),
                activationEnd=isodate(end),
                shares=shares,
                )
            for plant, start, end, shares in sharePlants
            ]

    def sharePlants(self):
        return self._plants
class PlantSharesCurve_Test(unittest.TestCase):
    def test_atDay(self):
        curve = PlantSharesCurve()
        with self.assertRaises(UnconfiguredDataProvider) as assertion:
            curve.atDay('member', isodate('2015-02-21'))
        self.assertEqual(assertion.exception.args[0], "PlantProvider")

# vim: ts=4 sw=4 et
