from plantmeter.mongotimecurve import toLocal
import datetime

def localisodate(string):
    return string and toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

def naiveisodate(string):
    return string and datetime.datetime.strptime(string, "%Y-%m-%d")

def isodate(string):
    return string and datetime.datetime.strptime(string, "%Y-%m-%d").date()

def naiveisodatetime(string):
    return string and datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def localisodatetime(string):
    return string and toLocal(datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S"))


def dateToLocal(date):
    # TODO: optimize dateToLocal
    return localisodate(str(date))

def assertDate(name, date):
    assert type(date)==datetime.date, (
        "{} should be a datetime.date but it is {}"
        .format(name, date))
    return date

def assertDateOrNone(name, date):
    if date is None: return date
    assert type(date)==datetime.date, (
        "{} should be a datetime.date or None but it is {}"
        .format(name, date))
    return date

def assertNaiveTime(name, date):
    assert type(date)==datetime.datetime, (
        "{} should be a datetime.datetime with no timezone (naive) but it is {}"
        .format(name, date))
    return date

