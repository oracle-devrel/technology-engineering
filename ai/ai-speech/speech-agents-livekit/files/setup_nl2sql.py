import json
import os
import time

import requests
import oci
from oci.base_client import BaseClient

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
REGION = ""
SCHEMA_NAME = "ADMIN"

COMPARTMENT_ID = ""
QUERYING_CONNECTION_ID = ""
ENRICHMENT_CONNECTION_ID = ""

SEMANTIC_STORE_ID = None  # created at runtime
SSO_WALLET_SECRET_ID = ""

CONTROL_ENDPOINT = f"https://generativeai.{REGION}.oci.oraclecloud.com"
INFERENCE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"
DBTOOLS_HOST = f"https://dbtools.{REGION}.oci.oraclecloud.com"
API_VERSION_DBTOOLS = "20201005"

POLL_INTERVAL_SECONDS = 30
MAX_POLLS = 24

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
def load_signer():
    config = oci.config.from_file(os.path.expanduser("~/.oci/config"), "DEFAULT")
    token_file = os.path.expanduser(config["security_token_file"])
    with open(token_file, "r", encoding="utf-8") as f:
        token = f.read().strip()
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    signer = oci.auth.signers.SecurityTokenSigner(token=token, private_key=private_key)
    return config, signer


def make_genai_client(config, signer, endpoint):
    return BaseClient(
        "generative_ai",
        config,
        signer,
        {},
        service_endpoint=endpoint,
        retry_strategy=None,
    )


def call_genai(label, client, resource_path, method="GET", body=None):
    print(f"\n== {label} ==")
    try:
        kwargs = {
            "resource_path": resource_path,
            "method": method,
            "response_type": "str",
        }
        if body is not None:
            kwargs["header_params"] = {"content-type": "application/json"}
            kwargs["body"] = body

        resp = client.call_api(**kwargs)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return None

    print(f"  status: {resp.status}")
    data = resp.data
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            print(f"  response: {data[:2000]}")
            return data

    print(json.dumps(data, indent=2))
    return data


def call_dbtools(signer, path, method="GET", body=None):
    url = f"{DBTOOLS_HOST}{path}"
    headers = {"content-type": "application/json"}
    data = json.dumps(body).encode("utf-8") if body else None
    resp = requests.request(method, url, auth=signer, headers=headers, data=data, timeout=120)
    print(f"\n== DB Tools {method} {path} ==")
    print(f"  status: {resp.status_code}")
    print(f"  response: {resp.text[:2000]}")
    try:
        return resp.status_code, resp.json() if resp.text else {}
    except Exception:
        return resp.status_code, {}


# ----------------------------------------------------
# STEP 1: Update DB Tools connections
# ----------------------------------------------------
def update_connections(signer):
    update_body = {
        "type": "ORACLE_DATABASE",
        "keyStores": [
            {
                "keyStoreType": "SSO",
                "keyStoreContent": {
                    "valueType": "SECRETID",
                    "secretId": SSO_WALLET_SECRET_ID,
                },
            }
        ],
    }

    print("\nUpdating enrichment connection...")
    call_dbtools(
        signer,
        f"/{API_VERSION_DBTOOLS}/databaseToolsConnections/{ENRICHMENT_CONNECTION_ID}",
        "PUT",
        update_body,
    )

    print("\nUpdating querying connection...")
    call_dbtools(
        signer,
        f"/{API_VERSION_DBTOOLS}/databaseToolsConnections/{QUERYING_CONNECTION_ID}",
        "PUT",
        update_body,
    )


# ----------------------------------------------------
# STEP 2: Create semantic store
# ----------------------------------------------------
def create_semantic_store(config, signer):
    client = make_genai_client(config, signer, CONTROL_ENDPOINT)
    create_body = {
        "displayName": "TestSemanticStore",
        "description": "Demo semantic store for NL2SQL",
        "freeformTags": {},
        "definedTags": {},
        "dataSource": {
            "queryingConnectionId": QUERYING_CONNECTION_ID,
            "enrichmentConnectionId": ENRICHMENT_CONNECTION_ID,
            "connectionType": "DATABASE_TOOLS_CONNECTION",
        },
        "refreshSchedule": {"type": "ON_CREATE"},
        "compartmentId": COMPARTMENT_ID,
        "schemas": {
            "connectionType": "DATABASE_TOOLS_CONNECTION",
            "schemas": [{"name": SCHEMA_NAME}],
        },
    }

    result = call_genai(
        "Create semantic store",
        client,
        resource_path="/20231130/semanticStores",
        method="POST",
        body=create_body,
    )

    if result and isinstance(result, dict) and result.get("id"):
        return result["id"]

    raise RuntimeError("Semantic store creation failed or did not return an id")


# ----------------------------------------------------
# STEP 3: Trigger enrichment
# ----------------------------------------------------
def trigger_enrichment(config, signer, semantic_store_id):
    client = make_genai_client(config, signer, INFERENCE_ENDPOINT)
    enrichment_body = {
        "displayName": "full-build",
        "description": "Triggered from demo_nl2sql.py",
        "enrichmentJobType": "FULL_BUILD",
        "enrichmentJobConfiguration": {
            "enrichmentJobType": "FULL_BUILD",
            "schemaName": SCHEMA_NAME,
        },
    }

    result = call_genai(
        "Trigger enrichment FULL_BUILD",
        client,
        resource_path=f"/20260325/semanticStores/{semantic_store_id}/actions/enrich",
        method="POST",
        body=enrichment_body,
    )

    job_id = None
    if isinstance(result, dict):
        job_id = result.get("id") or result.get("jobId") or result.get("enrichmentJobId")

    if job_id:
        print(f"  Using enrichment job id: {job_id}")
    else:
        print("  No job id returned directly; will fall back to latest listed job.")

    return job_id


# ----------------------------------------------------
# STEP 4: Poll enrichment
# ----------------------------------------------------
def list_enrichment_jobs(config, signer, semantic_store_id):
    client = make_genai_client(config, signer, INFERENCE_ENDPOINT)
    data = call_genai(
        "List enrichment jobs",
        client,
        resource_path=f"/20260325/semanticStores/{semantic_store_id}/enrichmentJobs",
        method="GET",
    )

    if isinstance(data, dict):
        items = data.get("items") or data.get("data") or data.get("enrichmentJobs") or []
        if isinstance(items, list):
            return items
    if isinstance(data, list):
        return data
    return []


def pick_latest_job_id(jobs):
    if not jobs:
        return None
    first = jobs[0]
    if isinstance(first, dict):
        return first.get("id") or first.get("jobId")
    return None


def poll_enrichment_job(config, signer, semantic_store_id, job_id):
    print("\n=== Polling enrichment job ===")

    for i in range(MAX_POLLS):
        time.sleep(POLL_INTERVAL_SECONDS)

        client = make_genai_client(config, signer, INFERENCE_ENDPOINT)
        data = call_genai(
            f"GET enrichment job [{i + 1}]",
            client,
            resource_path=f"/20260325/semanticStores/{semantic_store_id}/enrichmentJobs/{job_id}",
            method="GET",
        )

        state = data.get("lifecycleState") if isinstance(data, dict) else None
        print(f"  >>> State: {state}")

        if state == "SUCCEEDED":
            print("  ✅ Enrichment complete!")
            return True
        if state == "FAILED":
            print("  ❌ Enrichment failed!")
            return False

    print("  ⚠️ Enrichment job did not finish within the polling window.")
    return False


# ----------------------------------------------------
# STEP 5: Test NL2SQL
# ----------------------------------------------------
def test_generate_sql(config, signer, semantic_store_id):
    client = make_genai_client(config, signer, INFERENCE_ENDPOINT)
    call_genai(
        "GenerateSqlFromNl",
        client,
        resource_path=f"/20260325/semanticStores/{semantic_store_id}/actions/generateSqlFromNl",
        method="POST",
        body={
            "displayName": "test",
            "description": "test",
            "inputNaturalLanguageQuery": "Which rooms are available from June 20 to June 25?",
        },
    )


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
def main():
    config, signer = load_signer()

    update_connections(signer)

    semantic_store_id = create_semantic_store(config, signer)
    print(f"\nUsing semantic store id: {semantic_store_id}")

    job_id = trigger_enrichment(config, signer, semantic_store_id)

    if not job_id:
        jobs = list_enrichment_jobs(config, signer, semantic_store_id)
        job_id = pick_latest_job_id(jobs)

    if not job_id:
        raise RuntimeError("Could not determine enrichment job id")

    poll_enrichment_job(config, signer, semantic_store_id, job_id)

    test_generate_sql(config, signer, semantic_store_id)


if __name__ == "__main__":
    main()