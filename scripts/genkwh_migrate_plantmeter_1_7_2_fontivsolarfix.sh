#!/bin/bash

export PYTHONIOENCODING=utf8

function step() { echo -e '\033[34;1m'"$*"'\033[0m'; }
function error() { echo -e '\033[31;1m'"$*"'\033[0m'; }
function warn() { echo -e '\033[33m'"$*"'\033[0m'; }
function fail() { error "$*"; exit -1; }
function run() { echo -e '\033[35;1m'Running: '\033[33;1m'"$*"'\033[0m'; "$@"; }
function capture() { echo -e '\033[35;1m'Running: '\033[33;1m'"${*:2}"'\033[0m'; "${@:2}" > "$OUTPUTDIR/${@:1:1}"; }

GENERATIONKWH_MIX_ID=1
MATALLANA_COUNTER_SERIAL='68308479'
FONTIVSOLAR_COUNTER_SERIAL='501815908'
EXECUTION_DATE=$(date +%F-%H%M%S)

OUTPUTDIR="migrationrun-${EXECUTION_DATE}"

run mkdir $OUTPUTDIR

(
step "Running migration $0 at ${EXECUTION_DATE}"

step "Current state"
run scripts/genkwh_plants.py list

step "Dumping current mongo collections"
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump" --db somenergia -c tm_profile
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump" --db somenergia -c rightspershare
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump" --db somenergia -c generationkwh_rightscorrection

step "Fixing Fontivsolar meter serial number"
run scripts/genkwh_plants.py editmeter \
    GenerationkWh Fontivsolar "$MATALLANA_COUNTER_SERIAL" name "$FONTIVSOLAR_COUNTER_SERIAL" ||
        fail "Unable to change Fontivsolar meter serial"

step "Resulting state"
run scripts/genkwh_plants.py list

step "Dumping previous granted rights"
capture rightspershare-pre-120.csv scripts/genkwh_mtc.py curve rightspershare 120
capture rightspershare-pre-20.csv  scripts/genkwh_mtc.py curve rightspershare 20
capture rightspershare-pre-1.csv   scripts/genkwh_mtc.py curve rightspershare 1
capture remainders-pre.cvs genkwh_remainders.py active

step "Recomputing rights"
run genkwh_rightsgranter.py recompute --id "$GENERATIONKWH_MIX_ID" ||
    fail "Rights recomputation failed"

step "Dumping resulting granted rights"
capture rightspershare-120.csv scripts/genkwh_mtc.py curve rightspershare 120
capture rightspershare-20.csv  scripts/genkwh_mtc.py curve rightspershare 20
capture rightspershare-1.csv   scripts/genkwh_mtc.py curve rightspershare 1
capture remainders.cvs genkwh_remainders.py active

step "Dumping corrections"
capture rightscorrection-120.csv scripts/genkwh_mtc.py curve rightscorrection 120
capture rightscorrection-20.csv  scripts/genkwh_mtc.py curve rightscorrection 20
capture rightscorrection-1.csv   scripts/genkwh_mtc.py curve rightscorrection 1

step "Dumping current mongo collections"
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump-result" --db somenergia -c tm_profile
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump-result" --db somenergia -c rightspershare
run ${MONGOBINPATH}mongodump $MONGOOPTS -o "$OUTPUTDIR/dump-result" --db somenergia -c generationkwh_rightscorrection

) 2>&1 | tee $OUTPUTDIR/migration.log


step "Undo commands:"
echo scripts/genkwh_plants.py editmeter GenerationkWh Fontivsolar 501815908 name 68308479



