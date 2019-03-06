# -*- coding: utf-8 -*-

import datetime
import numpy

class LayeredShareCurve(object):
    """
    Provides a time curve of shares by adding a series of temporary bounded items
    adding each one a fixed amount of shares.
    Items is a list of namespaces with
    `firstEffectiveDate`,
    `lastEffectiveDate`,
    `nshares` and a definible filter attribute.
    """
    def __init__(self, items, filterAttribute):
        self._provider = items
        self._filterAttribute = filterAttribute

    def atDay(self, day, filterValue=None):
        assert type(day) == datetime.date

        return sum(
            investment.shares
            for investment in self._provider.items()
            if (filterValue is None or investment[self._filterAttribute] == filterValue)
            and investment.lastEffectiveDate >= day
            and investment.firstEffectiveDate <= day
        )

    def hourly(self, start, end, filterValue=None):
        assert type(start) == datetime.date
        assert type(end) == datetime.date

        if end<start:
            return numpy.array([], dtype=int)
        hoursADay=25
        nDays=(end-start).days+1 # To Review
        result = numpy.zeros(nDays*hoursADay, dtype=numpy.int)

        for investment in self._provider.items():
            if filterValue is not None:
                if investment[self._filterAttribute] != filterValue:
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


class MemberSharesCurve(LayeredShareCurve):
    """
    Provides a time curve of active shares from the investments
    of a given member.
    You need to feed this object with an investment
    provider returning a list of namespaces with attributes
    `firstEffectiveDate`,
    `lastEffectiveDate`,
    `nshares` and `member`
    """
    def __init__(self, investments):
        super(MemberSharesCurve, self).__init__(investments, 'member')

class MixTotalSharesCurve(LayeredShareCurve):
    """
    Provides a time curve of active built shares from the plants
    of a given mix (pe. GenerationkWh).
    You need to feed this object with an investment
    provider returning a list of namespaces with attributes
    `firstEffectiveDate`,
    `lastEffectiveDate`,
    `nshares` and `mix`
    """
    def __init__(self, plants):
        super(MixTotalSharesCurve, self).__init__(plants, 'mix')



class PlantSharesCurve(LayeredShareCurve):
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
