#!/bin/bash
set -e

# Environment variables expected:
# INPUT_BUCKET: 
# INPUT_OBJECT: 
# OUTPUT_FILENAME
# OCI_BUCKET
# OCI_NAMESPACE
# OCI_REGION

if [[ -z "$INPUT_BUCKET" || -z "$INPUT_OBJECT" ]]; then
  echo "Error: INPUT_BUCKET and INPUT_OBJECT environment variables are required."
  exit 1
fi

OUTPUT_FILENAME="${OUTPUT_FILENAME:-output.avi}"
OCI_BUCKET="${OCI_BUCKET:-output_files}"

if [[ -z "$OCI_NAMESPACE" || -z "$OCI_REGION" ]]; then
  echo "Error: OCI_NAMESPACE and OCI_REGION environment variables are required for upload."
  exit 2
fi

echo "Fetching $INPUT_OBJECT from bucket $INPUT_BUCKET (Namespace: $OCI_NAMESPACE, Region: $OCI_REGION) using Resource Principals"
oci --region "$OCI_REGION" --auth resource_principal os object get \
  -ns "$OCI_NAMESPACE" \
  -bn "$INPUT_BUCKET" \
  --name "$INPUT_OBJECT" \
  --file input.mp4 \

echo "Converting input.mp4 to $OUTPUT_FILENAME"
ffmpeg -y -i input.mp4 "$OUTPUT_FILENAME"

echo "Uploading $OUTPUT_FILENAME to OCI Bucket: $OCI_BUCKET (Namespace: $OCI_NAMESPACE, Region: $OCI_REGION) using Resource Principals"
oci --region "$OCI_REGION" --auth resource_principal os object put \
  -ns "$OCI_NAMESPACE" \
  -bn "$OCI_BUCKET" \
  --file "$OUTPUT_FILENAME" \
  --name "$OUTPUT_FILENAME" \

echo "Upload complete."