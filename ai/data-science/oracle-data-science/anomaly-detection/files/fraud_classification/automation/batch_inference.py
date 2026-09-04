import math
import requests
import pandas as pd
import io
import oci
import os
import ads
from oci.auth.signers import get_resource_principals_signer

ads.set_auth(auth='resource_principal')

FILE_NAME = os.environ.get("FILE_NAME")

base_name = os.path.basename(FILE_NAME)                       
name_without_ext = os.path.splitext(base_name)[0]             
output_filename = f"results/{name_without_ext}_prediction.csv"

bucket = "your_bucket_name"
endpoint = "your_endpoint"


print(f"Input file:  {FILE_NAME}")
print(f"Output file: {output_filename}")


def load_data_from_oci(bucket, file):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    
    namespace = client.get_namespace().data
    response = client.get_object(namespace, bucket, file)
    df = pd.read_csv(io.BytesIO(response.data.content))
    return df

df = load_data_from_oci(bucket, FILE_NAME)
print(f"Loaded {df.shape[0]} rows")

def clean_payload(payload):
    return {
        k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
        for k, v in payload.items()
    }

def score_dataframe(df, endpoint):
    signer = get_resource_principals_signer()
    predictions = []
    for _, row in df.iterrows():
        payload = clean_payload(row.drop('is_fraud').to_dict())
        response = requests.post(endpoint, json=payload, auth=signer)
        fraud_prob = response.json()['prediction'][0]
        predictions.append(round(fraud_prob))
        if len(predictions) % 500 == 0:
            print(f"Scored {len(predictions)}/{len(df)} rows")
    return predictions

preds = score_dataframe(df, endpoint)

# ── Build results DataFrame ────────────────────────────────────────────────
results_df = pd.DataFrame({
    'Unnamed: 0': df['Unnamed: 0'].values,
    'prediction': preds
})

# ── Upload results ─────────────────────────────────────────────────────────
def upload_results(results_df, bucket, filename):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    namespace = client.get_namespace().data
    csv_buffer = io.BytesIO()
    results_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    client.put_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=filename,
        put_object_body=csv_buffer.getvalue()
    )
    print(f"Uploaded {filename} to {bucket}")

upload_results(results_df, bucket, output_filename)