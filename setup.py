#!/usr/bin/env python
from setuptools import setup, find_packages

readme = open("README.md").read()

setup(
	name = "somenergia-generationkwh",
	version = "0.2",
	description =
		"OpenERP module and library to manage Som Energia's Generation kWh",
	author = "Som Energia SCCL",
	author_email = "info@somenergia.coop",
	url = 'https://github.com/Som-Energia/somenergia-generationkwh',
	long_description = readme,
	license = 'GNU Affero General Public License v3 or later (AGPLv3+)',
	packages=find_packages(exclude=['*[tT]est*']),
	scripts=[
		],
	install_requires=[
		'yamlns',
		'b2btest',
		'numpy',
		'plantmeter',
#		'libfacturacioatr',
	],
	include_package_data = True,
	test_suite = 'generationkwh',
#	test_runner = 'colour_runner.runner.ColourTextTestRunner',
	classifiers = [
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Intended Audience :: Developers',
		'Development Status :: 2 - Pre-Alpha',
		'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
		'Operating System :: OS Independent',
	],
)

