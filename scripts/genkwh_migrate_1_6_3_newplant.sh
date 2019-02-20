#!/bin/bash

function step() {
    echo -e '\033[34;1m'"$*"'\033[0m'
}
function error() {
    echo -e '\033[31;1m'"$*"'\033[0m'
}
function warn() {
    echo -e '\033[33m'"$*"'\033[0m'
}
function fail() {
    error "$*"
    exit -1
}
function run() {
    echo -e '\033[33;1m'"$*"'\033[0m'
    "$@"
}

ALCOLEA_COUNTER_SERIAL='501600324'
FONTIVSOLAR_TOTAL_SHARES=20000 # TODO: review
FONTIVSOLAR_COUNTER_SERIAL='68308479'
FONTIVSOLAR_START_DATE='2019-02-20'

step "Current state"
run scripts/genkwh_production.py list
step "Renaming Alcolea meter"
run scripts/genkwh_production.py meterset \
    GenerationkWh Alcolea "1" name "$ALCOLEA_COUNTER_SERIAL"  ||
    fail "Unable to change the name"

step "Adding the new plant"
run scripts/genkwh_production.py addplant \
    GenerationkWh Fontivsolar Fontivsolar "$FONTIVSOLAR_TOTAL_SHARES" ||
        fail "Unable to add the new Fontivsolar plant"

step "Adding the plant meter"
run scripts/genkwh_production.py addmeter \
    GenerationkWh Fontivsolar "$FONTIVSOLAR_COUNTER_SERIAL" \
    "Fontivsolar main meter" "none://" "$FONTIVSOLAR_START_DATE" ||
        fail "Unable to add the meter for Fontivsolar plant"

step "Enabling new plant"
run scripts/genkwh_production.py plantset GenerationkWh Fontivsolar enabled '1' ||
    fail "Unable to enable the new plant"
step "Enabling new meter"
run scripts/genkwh_production.py meterset GenerationkWh Fontivsolar 68308479 enabled '1' ||
    fail "Unable to enable the new meter"

step "Resulting state"
run scripts/genkwh_production.py list



