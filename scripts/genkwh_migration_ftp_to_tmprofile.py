#!/usr/bin/env python
#-*- encoding: utf8 -*-

import dbconfig
import pymongo
from plantmeter.isodates import naiveisodatetime
from yamlns import namespace as ns
import datetime
import erppeek


client = pymongo.MongoClient("mongodb://localhost:27017/")
print "client", client
db = client["somenergia"]
col_from = db["generationkwh.production.measurement"]
col_to = db["tm_profile"]

meter_name = '501600324' # Alcolea, para Matallana seria "68308479"

oldest_date = col_to.find({
	'name': meter_name,
	}).sort([
	('utc_gkwh_timestamp', pymongo.ASCENDING),
	]).limit(1)[0]['utc_gkwh_timestamp']

from plantmeter.isodates import (
	assertNaiveTime,
	toLocal,
	addHours,
	asUtc,
)

# The oldest date in tm_profile is 2017-12-02T19:00:00Z

def genkwhutc2localtime(utcdatetime):
	"""
	Takes a utc-1 date and returns a tuple of localtime (tz naive)
	plus the season 'W' or 'S'.

	>>> from plantmeter.isodates import (
	... 	naiveisodatetime,
	... 	localisodatetime,
	... )
	>>> genkwhutc2localtime(localisodatetime("2016-01-01 10:00:00"))
	Traceback (most recent call last):
	...
	AssertionError: utcdatetime has CET timezone
	>>> genkwhutc2localtime(naiveisodatetime("2016-01-01 10:00:00"))
	(datetime.datetime(2016, 1, 1, 12, 0), 'W')
	>>> genkwhutc2localtime(naiveisodatetime("2016-07-01 10:00:00"))
	(datetime.datetime(2016, 7, 1, 13, 0), 'S')
	"""

	assertNaiveTime('utcdatetime',  utcdatetime)
	utcdatetime = asUtc(utcdatetime)
	deoffsetted = addHours(utcdatetime,1)
	local = toLocal(deoffsetted)
	season = "S" if local.tzname() == "CEST" else "W"
	return local.replace(tzinfo=None),season


def main():
	erp = erppeek.Client(**dbconfig.erppeek)

	for old in col_from.find({'datetime': {'$lt': oldest_date}}):
		old = ns(old)

		name = old.name # TODO: apply this
		creation_date = old.create_at # TODO: apply this
		lectura = old.ae
		localtime,season = genkwhutc2localtime(old.datetime)

		new = ns(
			#create_uid = 1,
			#create_date = datetime.datetime.now(),
			#write_uid = 1,
			#write_date = datetime.datetime.now(),
			#id = 3, # Id sequencial
			name = meter_name,
			valid = True,
			valid_date =  datetime.datetime.now(), # TODO: De que campo es?
			timestamp = localtime, # TODO: obtenerla a partir de utc_gkw_timestamp
			season = season, # S,W # TODO: obtenerla a partir de utc_gkw_timestamp
			#utc_timestamp = naiveisodatetime("2017-12-31 23:00:00"), # TODO: obtenerla a partir de utc_gkw_timestamp
			#utc_gkwh_timestamp = utc_gkwh_timestamp,
			magn = 1000, # All are 1000
			ae = lectura,
			ai = 0, # 0-8
			r1 = 0, # 0,1
			r2 = 0, # 0-194
			r3 = 0, # 0-9
			r4 = 0, # 0-8
			quality_ae = 0, # 0, 2, 8, 16, 130, 146
			quality_ai = 0, # 0, 2, 8, 16, 130, 146
			quality_r1 = 0, # 0, 2, 8, 16, 130, 146
			quality_r2 = 0, # 0, 2, 8, 16, 130, 146
			quality_r3 = 0, # 0, 2, 8, 16, 130, 146
			quality_r4 = 0, # 0, 2, 8, 16, 130, 146
			ae_fact = 0, # all 0
			ai_fact = 0, # all 0
			r1_fact = 0, # all 0
			r2_fact = 0, # all 0
			r3_fact = 0, # all 0
			r4_fact = 0, # all 0
			cch_fact = False, # All are false
			firm_fact = False, # All are false
			cch_bruta = True, # False, True
		)
		print new.dump()

		#newid = erp.TmProfile.create(new)



if __name__ == '__main__' :
	main()



# vim: noet ts=4 sw=4
