#!/bin/sh
. ./set-local-vars.sh

mkdir dist
rsync -aC --exclude node_modules --exclude dist --exclude '.git' --exclude '*.sh' --exclude test --exclude '.gitignore' . ./dist
cd dist
fn -v deploy --app $FN_APP_NAME
cd ..
#copy the updated func.yaml back for versioning?
rm -rf dist
