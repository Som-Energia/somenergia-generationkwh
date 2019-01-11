import json
from datetime import datetime, timedelta

from consolemsg import step, error, success, fail
from yamlns import namespace as ns

import erppeek
import dbconfig


if __name__ == "__main__":
    step("Checking whether the production meassures have been imported properly")

    O = erppeek.Client(**dbconfig.erppeek)

    twoDaysAgo = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

    last_pulls_ids = O.GenerationkwhProductionNotifier.search([('date_pull', '>', twoDaysAgo)])
    last_pulls = O.GenerationkwhProductionNotifier.read(last_pulls_ids)

    print(ns(imports=last_pulls).dump())

    if not last_pulls:
        fail("No data pull for the last 2 days")

    for pull in last_pulls[::-1]:
        if pull.status != 'done':
            error('Pull at {date_pull} from meter {id[1]} failed: {status]: {message}', **pull)
        else:
            success('Pull at {date_pull} from meter {id[1]} successful: {message}', **pull)

    if any(pull.status!=done for pull in last_pulls):
        fail("Failed pulls detected")
    success("The last imports were successfull")


