#!/bin/bash

./scripts/genkwh_investments.py clear
./scripts/genkwh_assignments.py clear
./scripts/genkwh_rights.py clear
./scripts/genkwh_investments.py create \
        --start 2015-06-30 \
        --stop 2015-06-30 \
        --wait 1

./scripts/genkwh_assignments.py default --all
./scripts/genkwh_rights.py init \
    --start 2015-07-02 --ndays 2 --nshares 1 \
    0 0 0 0 0 0 0 0 0 0 0 1000 1500 2000 15000 1000 0 0 0 0 0 0 0 0 0



