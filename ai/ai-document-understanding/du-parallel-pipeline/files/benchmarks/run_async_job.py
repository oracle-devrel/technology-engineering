"""Time the asynchronous Object Storage processor-job path for comparison.

This is the officially supported route for documents over 5 pages (up to
2,000 pages / 500 MB). It is benchmark-only here: the job is queued and
polled, so end-to-end latency is dominated by queueing rather than
processing — which is exactly what the parallel synchronous pipeline avoids.

Requires an existing bucket in a Document Understanding region:
    export DU_BUCKET_NAME=<bucket>          # required
    export DU_BUCKET_NAMESPACE=<namespace>  # optional, discovered if unset

Usage:
    python benchmarks/run_async_job.py document.pdf
"""

import argparse
import os
import sys
import time

import oci
import oci.ai_document.models as ai_document_models

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from du_pipeline.config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="Path to a PDF (any page count up to 2,000)")
    parser.add_argument("--features", default="table,text")
    parser.add_argument("--profile", help="OCI config profile (default: DEFAULT)")
    parser.add_argument(
        "--prefix", default="du-async-benchmark", help="Output prefix in the bucket"
    )
    args = parser.parse_args()

    bucket = os.environ.get("DU_BUCKET_NAME")
    if not bucket:
        sys.exit("Set DU_BUCKET_NAME to a bucket in a Document Understanding region.")

    settings = Settings.from_env(profile=args.profile)
    oci_config = oci.config.from_file(settings.config_file, settings.profile)

    object_storage = oci.object_storage.ObjectStorageClient(oci_config)
    namespace = os.environ.get("DU_BUCKET_NAMESPACE") or object_storage.get_namespace().data
    object_name = f"{args.prefix}/{os.path.basename(args.pdf)}"

    feature_models = {
        "table": ai_document_models.DocumentTableExtractionFeature(
            feature_type="TABLE_EXTRACTION"
        ),
        "text": ai_document_models.DocumentTextExtractionFeature(
            feature_type="TEXT_EXTRACTION"
        ),
        "key_value": ai_document_models.DocumentKeyValueExtractionFeature(
            feature_type="KEY_VALUE_EXTRACTION"
        ),
    }
    features = [feature_models[name.strip()] for name in args.features.split(",")]

    started = time.perf_counter()

    print(f"Uploading {args.pdf} to {bucket}/{object_name}...")
    with open(args.pdf, "rb") as handle:
        object_storage.put_object(
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=object_name,
            put_object_body=handle,
        )
    upload_done = time.perf_counter()

    client = oci.ai_document.AIServiceDocumentClient(oci_config)
    composite = oci.ai_document.AIServiceDocumentClientCompositeOperations(client)

    print("Creating processor job and waiting for completion...")
    response = composite.create_processor_job_and_wait_for_state(
        create_processor_job_details=ai_document_models.CreateProcessorJobDetails(
            compartment_id=settings.compartment_id,
            input_location=ai_document_models.ObjectStorageLocations(
                source_type="OBJECT_STORAGE_LOCATIONS",
                object_locations=[
                    ai_document_models.ObjectLocation(
                        namespace_name=namespace,
                        bucket_name=bucket,
                        object_name=object_name,
                    )
                ],
            ),
            output_location=ai_document_models.OutputLocation(
                namespace_name=namespace,
                bucket_name=bucket,
                prefix=f"{args.prefix}-results",
            ),
            processor_config=ai_document_models.GeneralProcessorConfig(
                processor_type="GENERAL",
                features=features,
            ),
        ),
        wait_for_states=["SUCCEEDED", "FAILED"],
        waiter_kwargs={"max_wait_seconds": 3600},
    )
    finished = time.perf_counter()

    job = response.data
    print(f"\nJob {job.id} finished with state: {job.lifecycle_state}")
    print(f"Upload time:      {upload_done - started:.1f}s")
    print(f"Job time:         {finished - upload_done:.1f}s (queue + processing + polling)")
    print(f"Total async time: {finished - started:.1f}s")
    print(f"Results are under {bucket}/{args.prefix}-results/ in Object Storage.")


if __name__ == "__main__":
    main()
