import io
import pandas as pd
import requests
from datetime import datetime, timezone
from oci.monitoring.models import Datapoint, MetricDataDetails, PostMetricDataDetails

def read_csv_from_object_storage(client, namespace, bucket, folder_name, object_name):
    full_object_name = f"{folder_name}/{object_name}"

    resp = client.get_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=full_object_name
    )

    return pd.read_csv(io.StringIO(resp.data.text))


def call_deployed_model(endpoint, signer, payload):
    response = requests.post(endpoint, json=payload, auth=signer, timeout=60)
    return response.json()

def create_aggregated_df(df):
    agg_df = (
        df.groupby('Date', as_index=False)
          .agg({
              'Store': 'nunique',
              'Dept': 'count',
              'IsHoliday': 'sum',
              'Weekly_Sales': 'sum',
              'Temperature': 'mean',
              'Fuel_Price': 'mean',
              'MarkDown1': 'mean',
              'MarkDown2': 'mean',
              'MarkDown3': 'mean',
              'MarkDown4': 'mean',
              'MarkDown5': 'mean',
              'CPI': 'mean',
              'Unemployment': 'mean',
              'Type': 'mean',
              'Size': 'mean'
          })
          .sort_values('Date')
          .reset_index(drop=True)
    )

    return agg_df

def push_forecast_metrics(
    monitoring_client,
    compartment_id,
    namespace,
    metric_name,
    actual,
    predicted,
    lower,
    upper,
    resource_group=None,
    timestamp=None):
    ts = timestamp or datetime.now(timezone.utc)

    metric_data = [
        MetricDataDetails(
            compartment_id=compartment_id,
            namespace=namespace,
            name=metric_name,
            resource_group=resource_group,
            dimensions={"series": "actual"},
            datapoints=[Datapoint(timestamp=ts, value=float(actual))],
        ),
        MetricDataDetails(
            compartment_id=compartment_id,
            namespace=namespace,
            name=metric_name,
            resource_group=resource_group,
            dimensions={"series": "predicted"},
            datapoints=[Datapoint(timestamp=ts, value=float(predicted))],
        ),
        MetricDataDetails(
            compartment_id=compartment_id,
            namespace=namespace,
            name=metric_name,
            resource_group=resource_group,
            dimensions={"series": "lower"},
            datapoints=[Datapoint(timestamp=ts, value=float(lower))],
        ),
        MetricDataDetails(
            compartment_id=compartment_id,
            namespace=namespace,
            name=metric_name,
            resource_group=resource_group,
            dimensions={"series": "upper"},
            datapoints=[Datapoint(timestamp=ts, value=float(upper))],
        ),
    ]

    payload = PostMetricDataDetails(
        metric_data=metric_data,
        batch_atomicity="NON_ATOMIC",
    )

    return monitoring_client.post_metric_data(payload)