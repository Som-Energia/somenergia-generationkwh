import json
from datetime import datetime, timedelta

import erppeek
import dbconfig


if __name__ == "__main__":

    O = erppeek.Client(**dbconfig.erppeek)

    date_2 = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

    last_pulls_ids = O.GenerationkwhProductionNotifier.search([('date_pull', '>', date_2)])

    last_pulls = O.GenerationkwhProductionNotifier.read(last_pulls_ids)

    print(json.dumps(last_pulls, indent=4, sort_keys=True))
