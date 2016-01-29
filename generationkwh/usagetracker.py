# -*- coding: utf-8 -*-

class UsageTracker(object):
    """UsageTracker manages the available use rights for a given partner.
    """

    def __init__(self, curveProvider):
        self._curves = curveProvider

    def available_kwh(self, member, start, end, fare, period):
        production = self._curves.production(start, end) # member?
        periodMask = self._curves.periodMask(fare, period, start, end)
        usage = self._curves.usage(member, start, end)
        return sum(
            p-u if m else 0
            for p,u,m
            in zip(production, usage, periodMask)
            )

    def use_kwh(self, member, start, end, fare, period, kwh):
        production = self._curves.production(start, end) # member?
        periodMask = self._curves.periodMask(fare, period, start, end)
        usage = self._curves.usage(member, start, end)

        allocated = 0
        for i, (p, u, m) in enumerate(zip(production, usage, periodMask)):
            if not m: continue # not in period
            used = min(kwh-allocated, p-u)
            usage[i] += used
            allocated += used

        return allocated

    def refund_kwh(self, member, start, end, fare, period, kwh):
        production = self._curves.production(start, end) # member?
        periodMask = self._curves.periodMask(fare, period, start, end)
        usage = self._curves.usage(member, start, end)

        deallocated = 0
        for i, (u, m) in reversed(list(enumerate(zip(usage, periodMask)))):
            if not m: continue # not in period
            unused = min(kwh-deallocated, u)
            usage[i] -= unused
            deallocated += unused

        return deallocated

