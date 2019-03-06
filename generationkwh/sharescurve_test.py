# -*- coding: utf-8 -*-

from .sharescurve import (
    MemberSharesCurve,
    PlantSharesCurve,
    MixTotalSharesCurve,
    LayeredShareCurve,
    )

import unittest
from yamlns import namespace as ns
from .isodates import isodate

class ItemProvider_MockUp(object):
    def __init__(self, items):
        self._items = [
            ns(
                myattribute=itemattribute,
                firstEffectiveDate=isodate(start),
                lastEffectiveDate=isodate(end),
                shares=shares,
                )
            for itemattribute, start, end, shares in items
            ]

    def items(self):
        return self._items

class InvestmentProvider_MockUp(object):
    def __init__(self, items):
        self._contracts = [
            ns(
                member=member,
                firstEffectiveDate=isodate(start),
                lastEffectiveDate=isodate(end),
                shares=shares,
                )
            for member, start, end, shares in items
            ]

    def items(self):
        return self._contracts

class PlantProvider_MockUp(object):
    def __init__(self, items):
        self._plants = [
            ns(
                mix=mix,
                firstEffectiveDate=isodate(start),
                lastEffectiveDate=isodate(end),
                shares=shares,
                )
            for mix, start, end, shares in items
            ]

    def items(self):
        return self._plants

class LayeredShareCurve_Test(unittest.TestCase):

    def assert_atDay_equal(self, filterValue, day, items, expectation):
        provider = ItemProvider_MockUp(items)
        curve = LayeredShareCurve(
            items = provider,
            filterAttribute = 'myattribute',
            )
        self.assertEqual(expectation, curve.atDay(isodate(day),filterValue))

    def assertActiveSharesEqual(self, filterValue, start, end, items, expected):
        provider = ItemProvider_MockUp(items)
        curve = LayeredShareCurve(
            items = provider,
            filterAttribute = 'myattribute',
            )
        result = curve.hourly(isodate(start), isodate(end),filterValue)
        self.assertEqual(list(result), expected)


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
 
    def test_hourly_notYetActivatedActions(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', '2015-02-21', 3),
                ('member', '2015-02-22', '2016-02-20', 5),
            ],
            +25*[3]
            )

    def test_hourly_unactivatedActions(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', False, False, 3),
                ('member', '2015-02-21', '2016-02-20', 5),
            ],
            +25*[5]
            )

    def test_hourly_undeactivatedActions(self):
        self.assertActiveSharesEqual(
            'member', '2015-02-21', '2015-02-21',
            [
                ('member', '2015-02-21', False, 3),
                ('member', '2015-02-21', '2016-02-20', 5),
            ],
            +25*[8]
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


class MemberSharesCurve_Test(LayeredShareCurve_Test):

    def assert_atDay_equal(self, member, day, investments, expectation):
        provider = InvestmentProvider_MockUp(investments)
        curve = MemberSharesCurve(investments = provider)
        self.assertEqual(expectation, curve.atDay(isodate(day),member))

    def assertActiveSharesEqual(self, member, start, end, investments, expected):
        provider = InvestmentProvider_MockUp(investments)
        curve = MemberSharesCurve(investments = provider)
        result = curve.hourly(isodate(start), isodate(end),member)
        self.assertEqual(list(result), expected)


class TotalMixShareCurve_Test(LayeredShareCurve_Test):

    def assert_atDay_equal(self, member, day, plants, expectation):
        provider = PlantProvider_MockUp(plants)
        curve = MixTotalSharesCurve(plants = provider)
        self.assertEqual(expectation, curve.atDay(isodate(day),member))

    def assertActiveSharesEqual(self, mix, start, end, plants, expected):
        provider = PlantProvider_MockUp(plants)
        curve = MixTotalSharesCurve(plants = provider)
        result = curve.hourly(isodate(start), isodate(end),mix)
        self.assertEqual(list(result), expected)



class PlantSharesCurve_Test(unittest.TestCase):

    def test_atDay(self):
        curve = PlantSharesCurve(5000)
        self.assertEqual(5000, curve.atDay(isodate('2016-05-01')))
    
    def test_hourly(self):
        curve = PlantSharesCurve(5000)
        self.assertEqual(25*[5000], list(curve.hourly(isodate('2016-05-01'), isodate('2016-05-01'))))

# vim: ts=4 sw=4 et
