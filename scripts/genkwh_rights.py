from generationkwh.isodates import localisodate
import numpy as np

import erppeek
import dbconfig

c = erppeek.Client(**dbconfig.erppeek)

activeshares=2000
start='2015-01-01'
ndays=730
nshares=30

production=np.tile(np.array([0]*12+[2000000]*4+[0]*8+[0]), ndays)
c.GenerationkwhTesthelper.clear_mongo_collections([
    'rightspershare',
    'memberrightusage',
])

for nshare in range(30):
    rights_per_share=production*nshare/activeshares
    c.GenerationkwhTesthelper.setup_rights_per_share(
        nshare, start, rights_per_share.tolist())

    c.GenerationkwhRemainderTesthelper.updateRemainders(
            [(nshare, start, 0)]
            )
