# -*- coding: utf-8 -*-

import unittest
from .assignmentseeker import AssignmentSeeker
from yamlns import namespace as ns
from .isodates import localisodate

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



class AssignmentSeeker_Test(unittest.TestCase):

    def test_trackerMockup_withNoCalls(self):

        t = UsageTrackerMockup([])

        self.assertEqual(t.calls(), [
        ])
        
    def test_trackerMockup(self):

        t = UsageTrackerMockup([2])
        result = t.use_kwh(member='member',
            start=localisodate('2015-09-01'),
            end=localisodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 2)
        self.assertEqual(t.calls(), [
            ('use_kwh', 'member',
                '2015-09-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                'myfare', 'myperiod', 100),
        ])
        
    def test_trackerMockup_severalCalls(self):

        t = UsageTrackerMockup([3,1])
        result = t.use_kwh(member='member1',
            start=localisodate('2015-09-01'),
            end=localisodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 3)

        result = t.use_kwh(member='member2',
            start=localisodate('2015-09-01'),
            end=localisodate('2015-09-01'),
            fare='myfare', period='myperiod',
            kwh=100)

        self.assertEqual(result, 1)
        
        self.assertEqual(t.calls(), [
            ('use_kwh', 'member1',
                '2015-09-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                'myfare', 'myperiod', 100),
            ('use_kwh', 'member2',
                '2015-09-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                'myfare', 'myperiod', 100),
        ])


    def test_assign_withoutAssignns(self):
        t = UsageTrackerMockup([])
        a = AssignmentsMockup([])
        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])
        self.assertEqual(result, 0)
        
    def test_assign_singleAssignment_prioritariesDoNotInterfere(self):
        t = UsageTrackerMockup([20])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=localisodate('2015-10-01'),
            ),
            ])

        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, 20)
        
        
    def test_assign_singleAssignment_prioritariesDoInterfere(self):
        t = UsageTrackerMockup([10])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=localisodate('2014-10-01'),
            ),
            ])

        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01 00:00:00+02:00',
                '2014-10-01 00:00:00+02:00',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, 10)
        
    def test_assign_singleAssignment_prioritariesHaveOldInvoicing(self):
        t = UsageTrackerMockup([20])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=localisodate('2013-10-01'),
            ),
            ])

        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ])
        
        self.assertEqual(result, 0)
        
        

    def test_assign_manyAssignments_prioritariesDontInterfere(self):
        t = UsageTrackerMockup([20,30])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=localisodate('2015-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=localisodate('2015-10-01'),
            ),
            ])

        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member1',
                '2014-08-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                '2.0A', 'P1', 100),
            ('use_kwh', 'member2',
                '2014-08-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                '2.0A', 'P1', 100-20),
            ])
        
        self.assertEqual(result, 20+30)
        
        
    def test_assign_manyAssignments_firstHaveOldInvoicing(self):
        t = UsageTrackerMockup([30])
        a = AssignmentsMockup([
            ns(
                member_id='member1',
                last_usable_date=localisodate('2013-10-01'),
            ),
            ns(
                member_id='member2',
                last_usable_date=localisodate('2015-10-01'),
            ),
            ])

        s = AssignmentSeeker(usagetracker=t, assignmentProvider=a)
        result = s.use_kwh(
            contract_id = 1,
            start_date = localisodate('2015-08-01'),
            end_date = localisodate('2015-09-01'),
            fare = '2.0A',
            period = 'P1',
            kwh = 100,
            )

        self.assertEqual(t.calls(),[
            ('use_kwh', 'member2',
                '2014-08-01 00:00:00+02:00',
                '2015-09-01 00:00:00+02:00',
                '2.0A', 'P1', 100),
            ])
        
        self.assertEqual(result, 30)
        
        
        
        




# vim: ts=4 sw=4 et