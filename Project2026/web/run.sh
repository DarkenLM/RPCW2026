#!/bin/bash

SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

if [[ "${_VENV_ACTIVATED:-}" != "true" ]]; then
    if [[ -f "$SCRIPTPATH/makeenv.sh" ]]; then
        . "$SCRIPTPATH/makeenv.sh"
    elif [[ -f ./makeenv.sh ]]; then
        . ./makeenv.sh
    fi
fi

[ -f .env ] && set -a && source .env && set +a
PYTHONPATH="$SCRIPTPATH/src" python -m main $@
