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

