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
    def __init__(self, provider):
        self._provider = provider

    def atDay(self, member, day):
        return sum(
            investment.shares
            for investment in self._datagetter()
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
    def __init__(self,investments):
        super(MemberSharesCurve,self).__init__(investments)
        self._datagetter = investments.shareContracts
        self._key = "member"
    
class PlantSharesCurve(object):
    def __init__(self,shares):
        self.shares = shares
    def atDay(self, plant, day):
        return self.shares
    def hourly(self, member, start, end):
        return 25*[5000]
# vim: ts=4 sw=4 et
