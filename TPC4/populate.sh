#!/bin/bash

PY=python3
PYFLAGS="-o ontologias/biblioteca_temporal.ttl"

if [ "$1" == "true" ]; then
  PYFLAGS="$PYFLAGS -d"
fi

$PY ./scripts/populate.py ./ontologias/biblioteca_temporal_base.ttl $PYFLAGS ./datasets/dataset_temporal_v2_100.json