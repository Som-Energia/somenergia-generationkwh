# -*- coding: utf-8 -*-

import datetime
import numpy
from plantmeter.mongotimecurve import curveIndexToDate, dateToCurveIndex, toLocal

class MemberSharesCurve(object):
    """ Provides the shares that are active at a give
        day, or either daily or hourly in a date span.
        You need to feed this object with an investment
        provider.
    """
    def __init__(self, investments):
        self._provider = investments

    def atDay(self, day, member=None):
        assert type(day) == datetime.date

        return sum(
            investment.shares
            for investment in self._provider.shareContracts()
            if (member is None or investment.member == member)
            and investment.lastEffectiveDate >= day
            and investment.firstEffectiveDate <= day
        )

    def hourly(self, start, end, member=None):
        assert type(start) == datetime.date
        assert type(end) == datetime.date

        if end<start:
            return numpy.array([], dtype=int)
        hoursADay=25
        nDays=(end-start).days+1 # To Review
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)

        for investment in self._provider.shareContracts():
            if member is not None:
                if investment.member != member:
                    continue
            if investment.lastEffectiveDate:
                if investment.lastEffectiveDate < start: continue

            if not investment.firstEffectiveDate:
                continue

            if investment.firstEffectiveDate > end: continue

            firstIndex = hoursADay*max(
                (investment.firstEffectiveDate-start).days,
                0)
            lastIndex = hoursADay*(min(
                (investment.lastEffectiveDate-start).days+1,
                nDays) if investment.lastEffectiveDate else 
                nDays)

            result[firstIndex:lastIndex]+=investment.shares
        return result


class PlantSharesCurve(MemberSharesCurve):
    def __init__(self,shares):
        self.shares = shares

    def atDay(self, day, member=None):
        return self.shares

    def _hourly(self, start, end, member=None):
        if end<start:
            return numpy.array([], dtype=int)

        hoursADay=25
        nDays=(end-start).days+1
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)
        result[:]=self.shares
        return result

    def hourly(self, start, end):
        return self._hourly(start,end,None)

# vim: ts=4 sw=4 et
