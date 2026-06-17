#!/bin/bash

for i in $(ls gdsio_s*k_*_*.log); do NAME=$(echo $i | sed 's/k/K/g'); mv $i $NAME ; done
