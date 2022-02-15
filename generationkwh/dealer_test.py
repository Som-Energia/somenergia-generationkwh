# -*- coding: utf-8 -*-

import unittest
from .dealer import Dealer
from yamlns import namespace as ns
from .isodates import isodate

class AssignmentsMockup(object):
    def __init__(self, assignments):
        self._assignments = assignments

    def contractSources(self, contract_id):
        return self._assignments

    def anyForContract(self, contract_id):
        return not not self._assignments


class UsageTrackerMockup(object):

    def __init__(self, results):
        self._results = results
        self._calls = []

    def calls(self):
        return self._calls

    def use_kwh(self, member, start, end, fare, period, kwh):
        self._calls.append(
            ('use_kwh', member, str(start), str(end), fare, period, kwh)
            )
        return self._results.pop(0)

    def refund_kwh(self, member, start, end, fare, period, kwh):
        self._calls.append(
            ('refund_kwh', member, str(start), str(end),
                fare, period, kwh)
            )
        return self._results.pop(0)

    def use_kwh_with_dates_dict(self, member, start, end, fare, period, kwh):
        self._calls.append(
            ('use_kwh_with_dates_dict', member, str(start), str(end), fare, period, kwh)
            )
        return self._results.pop(0)

    def refund_kwh_with_dates_dict(self, member, start, end, fare, period, kwh):
        self._calls.append(
            ('refund_kwh_with_dates_dict', member, str(start), str(end),
                fare, period, kwh)
            )
        return self._results.pop(0)

class InvestmentMockup(object):
    def __init__(self, members):
        self._activeMembers = members

    def effectiveForMember(self, member_id, first_date, last_date):
        return member_id in self._activeMembers


class Dealer_Test(unittest.TestCase):

    def test_trackerMockup_withNoCalls(self):

        t = UsageTrackerMockup([])

        self.assertEqual(t.calls(), [
        ])

    def test_trackerMockup(self):

        t = UsageTrackerMockup([2])
        result = t.use_kwh(member='member',
            start=isodate('2015-09-01'),
            end=isodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 2)
        self.assertEqual(t.calls(), [
            ('use_kwh', 'member',
                '2015-09-01',
                '2015-09-01',
                'myfare', 'myperiod', 100),
        ])

    def test_trackerMockup_severalCalls(self):

        t = UsageTrackerMockup([3,1])
        result = t.use_kwh(member='member1',
            start=isodate('2015-09-01'),
            end=isodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 3)

        result = t.use_kwh(member='member2',
            start=isodate('2015-09-01'),
            end=isodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 1)

        self.assertEqual(t.calls(), [
            ('use_kwh', 'member1',
                '2015-09-01',
                '2015-09-01',
                'myfare', 'myperiod', 100),
            ('use_kwh', 'member2',
                '2015-09-01',
                '2015-09-01',
                'myfare', 'myperiod', 100),
        ])


    def test_usekwh_withoutAssignns(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([])
        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])
        self.assertEqual(result, [])

    def test_usekwh_singleAssignment_prioritariesDoNotInterfere(self):

        t = UsageTrackerMockup([(20, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])

        self.assertEqual(result, [
            dict(member_id='member1', kwh=20, usage={}),
            ])


    def test_usekwh_singleAssignment_prioritariesDoInterfere(self):
        t = UsageTrackerMockup([(10, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2014-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2014-10-01',
                '2.0A', 'P1', 100),
            ])
        self.assertEqual(result, [
            dict(member_id='member1', kwh=10, usage={}),
            ])

    def test_usekwh_singleAssignment_prioritariesHaveOldInvoicing(self):
        t = UsageTrackerMockup([(20, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2013-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])

        self.assertEqual(result, [
            ])



    def test_usekwh_manyAssignments_prioritariesDontInterfere(self):
        t = UsageTrackerMockup([(20, {}),(30, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ('use_kwh_with_dates_dict', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100-20),
            ])

        self.assertEqual(result, [
            dict(member_id='member1', kwh=20, usage={}),
            dict(member_id='member2', kwh=30, usage={}),
            ])

    def test_usekwh_manyAssignments_zeroUseIncluded(self):
        t = UsageTrackerMockup([(0, {}),(10, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 20,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 20),
            ('use_kwh_with_dates_dict', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 20),
            ])

        self.assertEqual(result, [
            dict(member_id='member1', kwh=0, usage={}),
            dict(member_id='member2', kwh=10, usage={}),
            ])

    def test_usekwh_manyAssignments_zeroUseBecauseNoMoreRequired(self):
        t = UsageTrackerMockup([(20, {}),(0, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 20,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 20),
            ('use_kwh_with_dates_dict', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 0),
            ])

        self.assertEqual(result, [
            dict(member_id='member1', kwh=20, usage={}),
            dict(member_id='member2', kwh=0, usage={}),
            ])

    def test_usekwh_manyAssignments_firstHaveOldInvoicing(self):
        t = UsageTrackerMockup([(30, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2013-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh_with_dates_dict', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])

        self.assertEqual(result, [
            dict(member_id='member2', kwh=30, usage={}),
            ])

    def test_refundkwh(self):
        t = UsageTrackerMockup([(20, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.refund_kwh(
            contract_id = 1,
            first_date = isodate('2015-08-01'),
            last_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            member_id='member1',
            )

        self.assertEqual(t.calls(),[
            ('refund_kwh_with_dates_dict', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])

        self.assertEqual(result, {'kwh': 20, 'member_id': 'member1', 'unusage': {}})


    def test_isactive_withAssignments_andInvesments(self):
        t = UsageTrackerMockup([(20, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])
        i = InvestmentMockup([
            'member1'
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a, investments=i)
        self.assertTrue(s.is_active(
            contract_id=1,
            first_date=isodate('2015-10-01'),
            last_date=isodate('2015-10-01'),
            ))

    def test_isactive_withAssignments_noEffectiveInvestment(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])
        i = InvestmentMockup([])

        s = Dealer(usageTracker=t, assignmentProvider=a, investments=i)
        self.assertFalse(s.is_active(
            contract_id=1,
            first_date=isodate('2015-10-01'),
            last_date=isodate('2015-10-01'),
            ))


    def test_isactive_manyAssigments_oneWithoutInvestment(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])
        i = InvestmentMockup(['member1'])

        s = Dealer(usageTracker=t, assignmentProvider=a, investments=i)
        self.assertTrue(s.is_active(
            contract_id=1,
            first_date=isodate('2015-10-01'),
            last_date=isodate('2015-10-01'),
            ))

    def test_isactive_withoutAssignments(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        self.assertFalse(s.is_active(
            contract_id=1,
            first_date=isodate('2015-10-01'),
            last_date=isodate('2015-10-01'),
            ))

    def test_usekwh_assertsPositiveRequiredUse(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        with self.assertRaises(AssertionError) as ctx:
            result = s.use_kwh(
                contract_id = 1,
                first_date = isodate('2015-08-01'),
                last_date = isodate('2015-09-01'),
                fare = '2.0A',
                period = 'P1',
                kwh = -20,
                )
        self.assertEqual(ctx.exception.args[0],
            "Negative use not allowed")

    def test_usekwh_asserts_ifTrackerReturnsNegative(self):
        t = UsageTrackerMockup([(-1, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        with self.assertRaises(AssertionError) as ctx:
            result = s.use_kwh(
                contract_id = 1,
                first_date = isodate('2015-08-01'),
                last_date = isodate('2015-09-01'),
                fare = '2.0A',
                period = 'P1',
                kwh = 20,
                )
        self.assertEqual(ctx.exception.args[0],
            "Genkwh Usage traker returned negative use (-1) for member member1")

    def test_usekwh_asserts_ifTrackerReturnsNegative(self):
        t = UsageTrackerMockup([(11, {})])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        with self.assertRaises(AssertionError) as ctx:
            result = s.use_kwh(
                contract_id = 1,
                first_date = isodate('2015-08-01'),
                last_date = isodate('2015-09-01'),
                fare = '2.0A',
                period = 'P1',
                kwh = 10,
                )
        self.assertEqual(ctx.exception.args[0],
            "Genkwh Usage traker returned more (11) than required (10) "
            "for member member1")

# vim: ts=4 sw=4 et
