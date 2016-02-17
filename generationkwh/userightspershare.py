# -*- coding: utf-8 -*-

import numpy

class UserRightsPerShare(object):
    """
        Provides the hourly curve of kWh available for a member
        with a given number of shares.
    """
    def __init__(self, production):
        self._production = production

    def get(self, nshares, start, end):
        hoursADay = 25
        return numpy.zeros(hoursADay)


import unittest
import datetime

class Curve_MockUp(object):
    def __init__(self, value):
        self._value = value

    def get(self, *args, **kwd):
        return self._value


def isodate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').date()


class UserRightsPerShare_Test(unittest.TestCase):

    def test(self):
        curve = UserRightsPerShare(
            production = Curve_MockUp(25*[0]),
            )
        result = curve.get(
            nshares=1,
            start=isodate('2015-01-02'),
            end=isodate('2015-01-02'),
            )
        self.assertEqual(list(result), 25*[0])


# vim: ts=4 sw=4 et
