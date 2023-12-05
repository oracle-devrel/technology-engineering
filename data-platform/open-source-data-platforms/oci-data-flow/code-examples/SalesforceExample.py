from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from simple_salesforce import Salesforce
import os
import argparse
from datetime import datetime, timedelta
from salesforceCredentials import username,password,security_token
import time

# Salesforce credentials
sf = Salesforce(username=username, password=password, security_token=security_token)

parser = argparse.ArgumentParser()
parser.add_argument('--auth-type', default='PLAIN')
parser.add_argument('--bootstrap-port', default='9092')
parser.add_argument('--bootstrap-server', default='cell-1.streaming.<OCI Region>.oci.oraclecloud.com')
parser.add_argument('--checkpoint-location', default='oci://<bucketname>@<namespace>/<checkpoint folder>')
parser.add_argument('--encryption', default='SASL_SSL')
parser.add_argument('--ocid')
parser.add_argument('--output-location', default='oci://<bucketname>@<namespace>/<output folder>')
parser.add_argument('--output-mode', default='file')
parser.add_argument('--stream-password',default='<Token>')
parser.add_argument('--raw-stream', default='<Topic name>')
parser.add_argument('--stream-username',default='<tenancy name>/<username>/<streampool OCID>')
args = parser.parse_args()

if args.bootstrap_server is None:
    args.bootstrap_server = os.environ.get('BOOTSTRAP_SERVER')
if args.raw_stream is None:
    args.raw_stream = os.environ.get('RAW_STREAM')
if args.stream_username is None:
    args.stream_username = os.environ.get('STREAM_USERNAME')
if args.stream_password is None:
    args.stream_password = os.environ.get('STREAM_PASSWORD')

assert args.bootstrap_server is not None, "Kafka bootstrap server (--bootstrap-server) name must be set"
assert args.checkpoint_location is not None, "Checkpoint location (--checkpoint-location) must be set"
assert args.output_location is not None, "Output location (--output-location) must be set"
assert args.raw_stream is not None, "Kafka topic (--raw-stream) name must be set"

if args.ocid is not None:
    jaas_template = 'com.oracle.bmc.auth.sasl.ResourcePrincipalsLoginModule required intent="streamPoolId:{ocid}";'
    args.auth_type = 'OCI-RSA-SHA256'
else:
    jaas_template = 'org.apache.kafka.common.security.plain.PlainLoginModule required username="{username}" password="{password}";'

# Function to fetch updated records from Salesforce
def fetch_updated_records(last_extracted_timestamp):
    soql_query = f"SELECT Id, Name, LastModifiedDate FROM Account WHERE LastModifiedDate > {last_extracted_timestamp}"
    result = sf.query_all(query=soql_query)
    return result.get('records', [])

# Function to convert Salesforce records to PySpark DataFrame
def records_to_dataframe(records):
    spark = SparkSession.builder.appName("SalesforceApp") \
                                .getOrCreate()
    #spark.sparkContext.setLogLevel('ERROR')
    # Check if records is not empty and has the expected structure
    if records and isinstance(records, list) and isinstance(records[0], dict):
        # Extract values from each record
        data = [(record.get("Id", ""), record.get("Name", ""), record.get("LastModifiedDate", "")) for record in records]
        schema = ["Id", "Name", "LastModifiedDate"]
        return spark.createDataFrame(data, schema=schema)
    else:
        # If records are not in the expected format, return an empty DataFrame
        return spark.createDataFrame([], schema=["Id", "Name", "LastModifiedDate"])


# Main streaming ingestion process
def main():
    #Dummy last extracted timestamp
    last_extracted_timestamp = '2000-01-01T00:00:00Z'
    while True:
        # Fetch updated records from Salesforce
        records = fetch_updated_records(last_extracted_timestamp)
        if records:
            # Convert records to DataFrame
            df = records_to_dataframe(records)
            
            # Write to Kafka
            df_transformed = df.selectExpr("CAST(Id AS STRING) AS key", "CAST(Name AS STRING) AS value", "CAST(LastModifiedDate AS TIMESTAMP) AS timestamp")
            # Kafka configuration            
            df_transformed \
                .write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", '{}:{}'.format(args.bootstrap_server,
                                            args.bootstrap_port)) \
                .option("kafka.enable.idempotence", "false") \
                .option("kafka.sasl.jaas.config", jaas_template.format(
                                        username=args.stream_username, password=args.stream_password
                                        )) \
                .option('kafka.sasl.mechanism', args.auth_type) \
                .option('kafka.security.protocol', args.encryption) \
                .option("topic", args.raw_stream) \
                .option("kafka.max.partition.fetch.bytes", "1024 * 1024") \
                .option("checkpointLocation", args.checkpoint_location) \
                .mode("append") \
                .save()
            # Update the last extraction timestamp
            last_extracted_timestamp = max([record["LastModifiedDate"] for record in records])
        # Sleep for a specified interval before the next iteration
        time.sleep(10) 

if __name__ == "__main__":
    # Start the streaming ingestion process
    main()
