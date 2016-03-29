# -*- coding: utf-8 -*-

import datetime
import numpy


class UnconfiguredDataProvider(Exception):
    pass

class ActiveSharesCurve(object):
    """ Provides the shares that are active at a give
        day, or either daily or hourly in a date span.
        You need to feed this object with an investment
        provider.
    """
    def __init__(self,investments=None, key=None):
        self._investmentProvider = investments
        self._key = key

    def atDay(self, member, day, method):
        if self._investmentProvider is None:
            raise UnconfiguredDataProvider("InvestmentProvider")
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

class ActiveSharesCurveExtend(ActiveSharesCurve):
    def __init__(self,investments=None):
        super(ActiveSharesCurveExtend,self).__init__(investments, key='member')
    
    def atDay(self, member, day):
        if self._investmentProvider is None:
            raise UnconfiguredDataProvider("InvestmentProvider")
        return super(ActiveSharesCurveExtend, self).atDay(member,day,self._investmentProvider.shareContracts)
# vim: ts=4 sw=4 et
