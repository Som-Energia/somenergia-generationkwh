plantmeter
==========

OpenERP module and library to manage multisite energy generation

INSTALL
-------

.. code:: bash

    pip install -e .
    nosetests plantmeter # Run unit tests
    nosetests scripts # Run erp tests (require a working erp)

CHANGES
-------

1.7.1 2019-04-04
~~~~~~~~~~~~~~~~

-  Removed deprecated scripts ``genkwh_pull_status`` and
   ``genkwh_export``
-  Removed deprecated ``genkwh_production`` subcommands: pull-status,
   load-meassures and update-kwh
-  Script ``genkwh_production.py`` installed by setup.py

1.7.0 2019-04-02
~~~~~~~~~~~~~~~~

-  Meters and plants have ``first_active_date`` attribute
-  Built plant shares is not a constant curve anymore, changes when
   adding new plants
-  Meter ``first_active_date`` filters out earlier meassures
-  Fix: lastMesurement in a mix/plant is the first one of
   lastMeasurement of the childs
-  ``genkwh_migrate_1_6_3_newplant.sh``: Script to migrate old plant and
   incorporate the new one
-  In general, fixes to really enable multiple plants
-  ``genkwh_production.py``: editmix, editplant, editmeter
-  ``genkwh_production.py``: editmix, editplant, editmeter
-  ``genkwh_production.py``: delmix, delplant, delmeter
-  ``genkwh_production.py``: meterset -> editmeter

1.6.2 2019-01-21
~~~~~~~~~~~~~~~~

-  Deprecated ``genkwh_pull_status.py`` and ``genkwh_pull_status.sh``
-  ``genkwh_production.py``: added ``pull_status`` as subcommand
-  ``genkwh_production.py pull_status``: nicer output and exit status
-  ``genkwh_migration_ftp_to_tmprofile.py`` migration script

1.6.1 2019-01-03
~~~~~~~~~~~~~~~~

-  Show erp configuration at the begining of every command
-  Protect ``genkwh_production.py clear`` againts lossy fingers

1.6.0 2019-01-03
~~~~~~~~~~~~~~~~

-  Python 3 supported (python module, not yet the erp code)
-  Migrated to pymongo 3
-  MongoTimeCurve takes some field names as parameters (*timestamp* and
   *creation*)
-  Abstracted ResourceParent from ProductionPlant and
   ProductionAggregator
-  ``genkwh_production.py list``: list all the resorce hierarchy (mixes,
   plants, meters)
-  ``genkwh_production.py addmix``: to add an aggregator, now 'mix'
-  ``genkwh_production.py addplant``: to add a plant
-  ``genkwh_production.py addmeter``: to add a meter
-  ``genkwh_production.py curve``: to extract stored curves as TSV
   (production, rights...)
-  ``genkwh_production.py`` commmand documentation
