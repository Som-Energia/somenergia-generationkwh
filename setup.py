#!/usr/bin/env python
from setuptools import setup, find_packages

readme = open("README.rst").read()

setup(
	name = "plantmeter",
	version = "0.8",
	description =
		"OpenERP module and library to manage multisite energy generation",
	author = "Som Energia SCCL",
	author_email = "info@somenergia.coop",
	url = 'https://github.com/Som-Energia/plantmeter',
	long_description = readme,
	license = 'GNU General Public License v3 or later (GPLv3+)',
	packages=find_packages(exclude=['*[tT]est*']),
	scripts=[
		],
	install_requires=[
        'pymongo<3.0',
        'numpy',
        'xlrd',
        'yamlns',
        'pytz',
	],
	include_package_data = True,
	test_suite = 'plantmeter',
#	test_runner = 'colour_runner.runner.ColourTextTestRunner',
	classifiers = [
		'Programming Language :: Python',
		'Programming Language :: Python :: 3',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Intended Audience :: Developers',
		'Development Status :: 2 - Pre-Alpha',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Operating System :: OS Independent',
	],
)

