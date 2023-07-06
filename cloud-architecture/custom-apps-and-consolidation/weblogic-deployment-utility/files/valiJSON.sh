#!/bin/bash
# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: Validate JSON.
# @author: Vasudeva Manikandan.

count=`wc -l input_v3.json | cut -d " " -f1`
sed "${count}s/","//" input_v3.json > input.json
checkTrue=`grep "True" input.json`
if [ $? -eq 0 ]; then
  sed -e 's/"True"/"true"/' input.json > input.json.tmp
  mv input.json.tmp input.json
fi
checkFalse=`grep "False" input.json`
if [ $? -eq 0 ]; then
  sed -e 's/"False"/"false"/' input.json > input.json.tmp
  mv input.json.tmp input.json
fi
echo "Resultant JSON as follows"
cat input.json


