# plantmeter 

OpenERP module and library to manage multisite energy generation

## CHANGES

### Next

- Deprecated `genkwh_pull_status.py` and `genkwh_pull_status.sh`
- `genkwh_production.py`: added `pull_status` as subcommand
- `genkwh_production.py pull_status`: nicer output and exit status
- `genkwh_migration_ftp_to_tmprofile.py` migration script

### 1.6.1 2019-01-03

- Show erp configuration at the begining of every command
- Protect `genkwh_production.py clear` againts lossy fingers

### 1.6.0 2019-01-03

- Python 3 supported (python module, not yet the erp code)
- Migrated to pymongo 3
- MongoTimeCurve takes some field names as parameters (_timestamp_ and _creation_)
- Abstracted ResourceParent from ProductionPlant and ProductionAggregator
- `genkwh_production.py list`: list all the resorce hierarchy (mixes, plants, meters)
- `genkwh_production.py addmix`: to add an aggregator, now 'mix'
- `genkwh_production.py addplant`: to add a plant
- `genkwh_production.py addmeter`: to add a meter
- `genkwh_production.py curve`: to extract stored curves as TSV (production, rights...)
- `genkwh_production.py` commmand documentation






