# -*- coding: utf-8 -*-

import numpy
from .isodates import dateToLocal
import datetime

class MemberRightsCurve(object):
    """
        Provides the hourly curve of kWh available for a given
        member in a given time interval.

        Naive and eager versions are provided:

        - Naive version just multiplies the kWh discretized curve
        for one action by the number of active shares.

        - Eager version takes a different profile for each number
        of shares and members with N shares get a kWh with N times
        earlier.

        kWh remainder are accommulated to the next hour so if the
        next hour implies a change of period, that energy is wrongly
        assigned, to be purist.

        That error is bigger for the naive approximation, as the
        error in every period change is up to N kWh if you have N shares.
        The eager version limits the error a 1 kWh.

        On the other hand the Naive version simplifies communicating
        the members the hourly kWh available by providing a single
        kWh/share curve instead of having different curves for each
        number of shares.
    """
    def __init__(self, activeShares, rightsPerShare,
            eager=False, remainders=None):
        self._activeShares = activeShares
        self._rightsPerShare = rightsPerShare
        self._eager = eager
        self._remainders = remainders

    def _get_naive(self, member, start, end):
        assert type(start) == datetime.date
        assert type(end) == datetime.date

        nshares=1
        return (
            numpy.array(self._rightsPerShare.rightsPerShare(
                nshares, start, end)) *
            numpy.array(self._activeShares.hourly(
                start, end, member))
            )

    def _get_eager(self, member, start, end):
        assert type(start) == datetime.date
        assert type(end) == datetime.date

        shares = self._activeShares.hourly(start, end, member)
        choiceset = list(sorted(set(shares)))
        remainders = set([
            nshares
            for nshares, date, wh
            in self._remainders.get()
            ])
        choices = [
            None
            if nshares not in choiceset else
            self._rightsPerShare.rightsPerShare(nshares, start, end)
            if nshares in remainders else
            self._rightsPerShare.rightsPerShare(1, start, end) * nshares
            for nshares in xrange(max(choiceset)+1)
            ]
        self._remainders.init([
            n for n in choiceset
            if n not in remainders
            ])
        return numpy.choose(shares, choices)

    def rights_kwh(self, member, start, end):
        if self._eager:
            return self._get_eager(member, start, end)

        return self._get_naive(member, start, end)

 


# vim: ts=4 sw=4 et
