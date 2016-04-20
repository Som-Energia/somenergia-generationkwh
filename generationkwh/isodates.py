from plantmeter.mongotimecurve import toLocal
import datetime

def localisodate(string):
    return string and toLocal(datetime.datetime.strptime(string, "%Y-%m-%d"))

