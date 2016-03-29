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
        return self.curve.get(
            filter=str(nshares),
            start=start,
            stop=stop,
            field='rights_kwh',
            )
    def updateRightsPerShare(self, nshares, start, data):
        curve = self.curve.update(
            start=start,
            filter=str(nshares),
            field='rights_kwh',
            data=data,
            )

# vim: ts=4 sw=4 et
