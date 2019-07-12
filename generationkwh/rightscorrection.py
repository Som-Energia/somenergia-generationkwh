# -*- coding: utf-8 -*-

from plantmeter.mongotimecurve import MongoTimeCurve
from .isodates import dateToLocal
import datetime

class RightsCorrection(object):
    """
        Keeps tracks of the differences between the rights directly
        computed from actual production, and the granted rights.
        The difference can come from a recomputation that must
        respect the rights already granted.
        Positive rights correction means than more rights are granted
        than the ones derived from the production.
    """

    def __init__(self, db):
        self.db = db
        self.curve = MongoTimeCurve(
            self.db,'generationkwh_rightscorrection')

    def rightsCorrection(self, nshares, start, stop):
        """
            Returns the curve of hourly rights correction in kwh
            for members with `nshares` active shares,
            between start and stop dates both included.
        """
        # TODO: No remainder for nshares? -> create 0Wh remainder and use 1 shares and multiply by n

        assert type(start) == datetime.date
        assert type(stop) == datetime.date

        return self.curve.get(
            filter=str(nshares),
            start=dateToLocal(start),
            stop=dateToLocal(stop),
            field='rights_kwh',
            )

    def updateRightsCorrection(self, nshares, start, data):
        """
            Sets the curve of hourly rights correction in kwh
            for members with nshares active shares,
            between start and stop dates both included.
        """

        assert type(start) == datetime.date

        curve = self.curve.update(
            start=dateToLocal(start),
            filter=str(nshares),
            field='rights_kwh',
            data=data,
            )

# vim: ts=4 sw=4 et
