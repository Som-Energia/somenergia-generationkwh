# -*- coding: utf-8 -*-

import datetime
import numpy


class UnconfiguredDataProvider(Exception):
    pass

class SharesCurve(object):
    """ Provides the shares that are active at a give
        day, or either daily or hourly in a date span.
        You need to feed this object with an investment
        provider.
    """
    def __init__(self, provider=None, key=None):
        self._provider = provider
        self._key = key

    def atDay(self, member, day, method):
        return sum(
            investment.shares
            for investment in method()
            if (member is None or investment[self._key] == member)
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

class MemberSharesCurve(SharesCurve):
    def __init__(self,investments=None):
        super(MemberSharesCurve,self).__init__(investments, key='member')
    
    def atDay(self, member, day):
        if self._provider is None:
            raise UnconfiguredDataProvider("InvestmentProvider")
        return super(MemberSharesCurve, self).atDay(member,day,self._provider.shareContracts)

class PlantSharesCurve(SharesCurve):

    def __init__(self,plants=None):
        super(PlantSharesCurve,self).__init__(plants, key='plant')

    def atDay(self, plant, day):
        if self._provider is None:
            raise UnconfiguredDataProvider("PlantProvider");
        return super(PlantSharesCurve, self).atDay(plant, day, self._provider.sharePlants)

# vim: ts=4 sw=4 et
