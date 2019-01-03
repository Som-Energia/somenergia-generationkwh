plantmeter
==========

OpenERP module and library to manage multisite energy generation

CHANGES
-------

1.6.0
~~~~~

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
