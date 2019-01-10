import datetime
import pytz

tz = pytz.timezone('Europe/Madrid')

def asUtc(date):
    """
    If date is a naive date, take it as being UTC.
    If date is local, converts to the equivalent UTC.
    """
    if date.tzinfo is None:
        return pytz.utc.localize(date)
    return date.astimezone(pytz.utc)

def toLocal(date):
    """
    If date is a naive date, take it as being Madrid TZ.
    If date is local, converts to the equivalent Madrid TZ.
    """
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

def addHours(normalized, hours):
    hours = datetime.timedelta(hours=hours)
    return tz.normalize(normalized + hours)

def localisodate(string):
    """Takes a date string and returns it as local datetime"""
    return string and toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

def utcisodate(string):
    """Takes a date string and returns it as utc datetime"""
    return string and asUtc(datetime.datetime.strptime(string, "%Y-%m-%d"))

def naiveisodate(string):
    """Takes a date string and returns it as naive datetime"""
    return string and datetime.datetime.strptime(string, "%Y-%m-%d")

def isodate(string):
    """Takes a date string and returns it as date (no time)"""
    return string and datetime.datetime.strptime(string, "%Y-%m-%d").date()

def naiveisodatetime(string):
    """Takes a date-time string and returns a naive date"""
    return string and datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def localisodatetime(string):
    """Takes a date-time string and returns a local date"""
    return string and toLocal(datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S"))

def utcisodatetime(string):
    """Takes a date-time string and returns it as utc date"""
    return string and asUtc(datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S"))

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

def assertUtcDateTime(name, value):
    assert isinstance(value, datetime.datetime), (
        "{} should be a datetime".format(name))
    assert value.tzinfo, (
        "{} should have timezone".format(name))
    assert value.tzname() == 'UTC', (
        "{} has {} timezone".format(name, value.tzname()))

def addDays(date, ndays):
    resultday = date.date() + datetime.timedelta(days=ndays)
    naiveday = datetime.datetime.combine(resultday, datetime.time(0,0,0))
    return toLocal(naiveday)

# TODO: TOTEST
def daterange(start_date, end_date, **kwds):
    """
    Generates dates from start_date to end_date,
    additional parameters provides paramenters for the
    timedelta constructor to be used as step.
    """
    step = kwds or dict(days=1)
    if not end_date:
        end_date = start_date + datetime.timedelta(days=1)
    for n in range(int ((end_date - start_date).days)):
        yield start_date + n*datetime.timedelta(**step)



