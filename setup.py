#!/usr/bin/env python
from setuptools import setup, find_packages
from generationkwh import __version__
readme = open("README.md").read()

setup(
    name = "somenergia-generationkwh",
    version = __version__,
    description =
        "OpenERP module and library to manage Som Energia's Generation kWh",
    author = "Som Energia SCCL",
    author_email = "info@somenergia.coop",
    url = 'https://github.com/Som-Energia/somenergia-generationkwh',
    long_description = readme,
    license = 'GNU Affero General Public License v3 or later (AGPLv3+)',
    packages=find_packages(exclude=['*[tT]est*']),
    scripts=[
        'scripts/genkwh_assignments.py',
        'scripts/genkwh_investments.py',
        'scripts/genkwh_productionloader.py',
        'scripts/genkwh_rightsgranter.py',
        'scripts/genkwh_rights.py',
        'scripts/genkwh_usage.py',
        'scripts/genkwh_curve.py',
        'scripts/genkwh_mtc.py',
        'scripts/genkwh_plants.py',
        'scripts/genkwh_remainders.py',
        ],
    install_requires=[
        'yamlns>=0.6',
        'b2btest',
        'numpy',
        'plantmeter',
        'python-dateutil',
        'decorator',
        'python-dateutil',
        'consolemsg>=0.3',
#        'libfacturacioatr',
    ],
    include_package_data = True,
    test_suite = 'generationkwh',
#    test_runner = 'colour_runner.runner.ColourTextTestRunner',
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

