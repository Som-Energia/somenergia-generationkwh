# -*- coding: utf-8 -*-
from plantmeter.mongotimecurve import MongoTimeCurve


class MemberRightsUsage(object):
    """
        Keeps track of the usage of the rights for each member.
    """

    def __init__(self, db):
        self.db = db
        self.curve = MongoTimeCurve(
            self.db,'memberrightusage')

    def usage(self, member, start, stop):
        return self.curve.get(
            filter=member,
            start=start,
            stop=stop,
            field='usage_kwh',
            )
    def updateUsage(self, member, start, data):
        curve = self.curve.update(
            start=start,
            filter=member,
            field='usage_kwh',
            data=data,
            )

# vim: ts=4 sw=4 et
