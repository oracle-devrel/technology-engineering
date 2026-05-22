import oci, io
import pandas as pd
from config import LOW_CARD_THRESHOLD

def load_data_from_oci(bucket, file):
    try:
        config = oci.config.from_file()
        client = oci.object_storage.ObjectStorageClient(config)
    except oci.exceptions.ConfigFileNotFound:
        signer = oci.auth.signers.get_resource_principals_signer()
        client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    
    namespace = client.get_namespace().data
    response = client.get_object(namespace, bucket, file)
    df = pd.read_csv(io.BytesIO(response.data.content))
    return df
    
# def load_data_from_oci(bucket, file):

#     config = oci.config.from_file()
#     client = oci.object_storage.ObjectStorageClient(config)

#     namespace = client.get_namespace().data
#     response = client.get_object(namespace, bucket, file)

#     df = pd.read_csv(io.BytesIO(response.data.content))

#     return df

def split_column_types(df):

    numeric_cols = df.select_dtypes(include=["int64","float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object","category"]).columns.tolist()

    low_card = [c for c in categorical_cols if df[c].nunique() <= LOW_CARD_THRESHOLD]
    high_card = [c for c in categorical_cols if df[c].nunique() > LOW_CARD_THRESHOLD]

    return numeric_cols, low_card, high_card