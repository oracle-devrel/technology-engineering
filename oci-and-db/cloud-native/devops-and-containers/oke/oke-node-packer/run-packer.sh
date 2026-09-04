#!/bin/bash

# Run Packer build with -on-error=ask so that you can decide what to do in case of an error
# Add the -debug flag in case you want to debug the packer script
packer build -var-file=vars.pkrvars.hcl -on-error=ask .
