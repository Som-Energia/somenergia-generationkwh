#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Copyright 2014 David García Garzón, Guifibaix SCCL

This file is part of Suro.

Suro is free software: you can redistribute it and/or modify
it under the terms of the Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Suro is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
Affero General Public License for more details.

You should have received a copy of the Affero General Public License
along with Suro. If not, see <http://www.gnu.org/licenses/>.
"""


def sequence(string) :
	"""
	Interprets strings like the ones in the standard Print Dialog
	uses to specify pages to be printed.
	ie. "2,4,6-9,13" means "2, 4, from 6 to 9 and 13"

	>>> sequence("2")
	[2]
	>>> sequence("2,9")
	[2, 9]
	>>> sequence("2,9,4")
	[2, 4, 9]
	>>> sequence("2-4")
	[2, 3, 4]
	>>> sequence("2-4,9")
	[2, 3, 4, 9]
	>>> sequence("2-4,3-5")
	[2, 3, 4, 5]
	>>> sequence("2-4,b")
	Traceback (most recent call last):
	...
	ValueError: invalid literal for int() with base 10: 'b'
	>>> sequence("2-b,7")
	Traceback (most recent call last):
	...
	ValueError: invalid literal for int() with base 10: 'b'
	>>> sequence("2-4-5,7")
	Traceback (most recent call last):
	...
	ValueError: more than two hyphen separated values
	"""
	def processItem(item):
		if '-' not in item: return [int(item)]
		values = item.split("-")
		if len(values) != 2:
			raise ValueError("more than two hyphen separated values")
		a,b = values
		return list(range(int(a),int(b)+1))

	return sorted(set(sum(
		( processItem(a) for a in string.split(',') )
		,[])))

def load_tests(loader, tests, ignore):
	import doctest
	tests.addTests(doctest.DocTestSuite())
	return tests

if __name__ == '__main__' :
	import unittest
	import sys
	sys.exit(unittest.main())




