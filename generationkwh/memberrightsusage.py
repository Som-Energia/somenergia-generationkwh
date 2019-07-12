# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve
from .isodates import dateToLocal
import datetime

class MemberRightsUsage(object):
    """
        Keeps track of the usage of the rights for each member.
    """

    def __init__(self, db):
        self.db = db
        self.curve = MongoTimeCurve(
            self.db,'memberrightusage')

    def usage(self, member, start, stop):
        assert type(start) == datetime.date
        assert type(stop) == datetime.date

        return self.curve.get(
            filter=member,
            start=dateToLocal(start),
            stop=dateToLocal(stop),
            field='usage_kwh',
            )

    def updateUsage(self, member, start, data):
        assert type(start) == datetime.date

        curve = self.curve.update(
            start=dateToLocal(start),
            filter=member,
            field='usage_kwh',
            data=data,
            )

# vim: ts=4 sw=4 et
