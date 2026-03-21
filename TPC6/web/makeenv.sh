#!/bin/bash

if [[ $_VENV_ACTIVATED == "true" ]]; then exit; fi

SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

python3 -m venv $SCRIPTPATH/.venv
source $SCRIPTPATH/.venv/bin/activate
echo Virtual environment activated.

if [ "$1" = "install" ]; then
    echo Installing dependencies.
    pip install -r requirements.txt
fi

PATH=$SCRIPTPATH/bin:$PATH

_VENV_ACTIVATED="true"
export _VENV_ACTIVATED
