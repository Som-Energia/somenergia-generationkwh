# -*- coding: utf-8 -*-

import unittest
from .dealer import Dealer
from yamlns import namespace as ns
from .isodates import isodate

class AssignmentsMockup(object):
    def __init__(self, assignments):
        self._assignments = assignments

    def seek(self, contract_id):
        return self._assignments


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
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])
        self.assertEqual(result, [])
        
    def test_usekwh_singleAssignment_prioritariesDoNotInterfere(self):
        t = UsageTrackerMockup([20])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, [
            dict(member_id='member1', kwh=20),
            ])
        
        
    def test_usekwh_singleAssignment_prioritariesDoInterfere(self):
        t = UsageTrackerMockup([10])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2014-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01',
                '2014-10-01',
                '2.0A', 'P1', 100),
            ])
        self.assertEqual(result, [
            dict(member_id='member1', kwh=10),
            ])
        
    def test_usekwh_singleAssignment_prioritariesHaveOldInvoicing(self):
        t = UsageTrackerMockup([20])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2013-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])
        
        self.assertEqual(result, [
            ])
        
        

    def test_usekwh_manyAssignments_prioritariesDontInterfere(self):
        t = UsageTrackerMockup([20,30])
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
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ('use_kwh', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100-20),
            ])
        
        self.assertEqual(result, [
            dict(member_id='member1', kwh=20),
            dict(member_id='member2', kwh=30),
            ])
        
        
    def test_usekwh_manyAssignments_firstHaveOldInvoicing(self):
        t = UsageTrackerMockup([30])
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
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member2',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, [
            dict(member_id='member2', kwh=30),
            ])
 
    def test_refundkwh(self):
        t = UsageTrackerMockup([20])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=isodate('2015-10-01'),
            ),
            ])

        s = Dealer(usageTracker=t, assignmentProvider=a)
        result = s.refund_kwh(
            contract_id = 1,
            start_date = isodate('2015-08-01'),
            end_date = isodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            member_id='member1',
            )

        self.assertEqual(t.calls(),[
            ('refund_kwh', 'member1',
                '2014-08-01',
                '2015-09-01',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, 20)
        
        
        



# vim: ts=4 sw=4 et
