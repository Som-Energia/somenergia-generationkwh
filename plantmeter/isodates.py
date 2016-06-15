import datetime
import pytz

tz = pytz.timezone('Europe/Madrid')

def asUtc(date):
    if date.tzinfo is None:
        return pytz.utc.localize(date)
    return date.astimezone(pytz.utc)

def toLocal(date):
    if date.tzinfo is None:
        return tz.localize(date)
    return date.astimezone(tz)

def parseLocalTime(string, isSummer=False, format="%Y-%m-%d %H:%M:%S"):
    naive = datetime.datetime.strptime(string, format)
    localized = tz.localize(naive)
    if not isSummer: return localized
    if localized.dst(): return localized
    onehour = datetime.timedelta(hours=1)
    lesser = tz.normalize(localized-onehour)
    return lesser if lesser.dst() else localized

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

def assertLocalDateTime(name, value):
    assert isinstance(value, datetime.datetime), (
        "{} should be a datetime".format(name))
    assert value.tzinfo, (
        "{} should have timezone".format(name))
    assert value.tzname() in ('CET','CEST'), (
        "{} has {} timezone".format(name, value.tzname()))

def addDays(date, ndays):
    resultday = date.date() + datetime.timedelta(days=ndays)
    naiveday = datetime.datetime.combine(resultday, datetime.time(0,0,0))
    return toLocal(naiveday)


