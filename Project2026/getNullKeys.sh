#!/bin/bash
cat records_xoai.json | jq -cr 'paths as $p | select(getpath($p) == null) | $p | .[1]' | sort | uniq