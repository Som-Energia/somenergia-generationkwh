# -*- coding: utf-8 -*-

from plantmeter.mongotimecurve import MongoTimeCurve

class RightsPerShare(object):
    """
        Keeps tracks of the rights consolidated for a given number of shares.
    """

    def __init__(self, db):
        self.db = db
        self.curve = MongoTimeCurve(
            self.db,'rightspershare')

    def rightsPerShare(self, nshares, start, stop):
        """
            Returns the curve of hourly generated rights in kwh
            for members with `nshares` active shares,
            between start and stop dates both included.
        """
        # TODO: No remainder for nshares? -> create 0Wh remainder and use 1 shares and multiply by n

        return self.curve.get(
            filter=str(nshares),
            start=start,
            stop=stop,
            field='rights_kwh',
            )

    def updateRightsPerShare(self, nshares, start, data):
        """
            Sets the curve of hourly consolidated rights in kwh
            for members with nshares active shares,
            between start and stop dates both included.
        """

        curve = self.curve.update(
            start=start,
            filter=str(nshares),
            field='rights_kwh',
            data=data,
            )

# vim: ts=4 sw=4 et
