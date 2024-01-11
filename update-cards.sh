#!/bin/bash
# Check and update cards after adding/modifying them
set -eu

dir=$(dirname "$0")

run () {
    script=$1
    shift
    (set -x; poetry run -C "$dir" "$dir/$script" "$@")
}


run validate.py
run add-pitch-accents.py
run make-bold-examples.py
run find-missing-examples.py
