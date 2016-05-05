# -*- coding: utf-8 -*-

import datetime

class UsageTracker(object):
    """UsageTracker manages the available use rights for a given partner.
    """

    def __init__(self, rights, usage, periodMask):
        self._rights = rights
        self._usage = usage
        self._periodMask = periodMask

    def available_kwh(self, member, start, end, fare, period):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)
        return int(sum(
            p-u if m else 0
            for p,u,m
            in zip(rights, usage, periodMask)
            ))

    def use_kwh(self, member, start, end, fare, period, kwh):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)

        allocated = 0
        for i, (p, u, m) in enumerate(zip(rights, usage, periodMask)):
            if not m: continue # not in period
            used = min(kwh-allocated, p-u)
            usage[i] += used
            allocated += used

        self._usage.updateUsage(member, start, usage)
        return allocated

    def refund_kwh(self, member, start, end, fare, period, kwh):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        rights = self._rights.rights_kwh(member, start, end)
        periodMask = self._periodMask.periodMask(fare, period, start, end)
        usage = self._usage.usage(member, start, end)

        deallocated = 0
        for i, (u, m) in reversed(list(enumerate(zip(usage, periodMask)))):
            if not m: continue # not in period
            unused = min(kwh-deallocated, u)
            usage[i] -= unused
            deallocated += unused

        self._usage.updateUsage(member, start, usage)
        return deallocated

    def usage(self, member, start, end):
        assert type(start) == datetime.date
        assert type(end) == datetime.date
        return self._usage.usage(member, start, end)

# vim: ts=4 sw=4 et
