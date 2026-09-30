from kafka3 import KafkaConsumer, KafkaProducer
import pandas as pd
from time import sleep
import datetime
import numpy as np
from datetime import datetime, timedelta
import random
import argparse
import uuid

#get arguments
parser = argparse.ArgumentParser()

parser.add_argument("-tenancy_name", "--tenancy_name", help="tenancy_name", required=True)
parser.add_argument("-region", "--region", help="region",required=True)
parser.add_argument("-user_name", "--user_name", help="user_name including OracleIdentityCloudService", required=True)
parser.add_argument("-stream_name", "--stream_name", help="stream_name / topic", required=True)
parser.add_argument("-stream_pool_ocid", "--stream_pool_ocid", help="stream_pool_ocid", required=True)
parser.add_argument("-auth_token", "--auth_token", help="auth_token", required=True)


args = parser.parse_args()
tenancy_name = args.tenancy_name
region = args.region
user_name = args.user_name
stream_name = args.stream_name
stream_pool_ocid = args.stream_pool_ocid
auth_token = args.auth_token


def main():
  consumer = KafkaConsumer(stream_name, bootstrap_servers = f'cell-1.streaming.{region}.oci.oraclecloud.com:9092', 
                         security_protocol = 'SASL_SSL', sasl_mechanism = 'PLAIN',
                         sasl_plain_username = f'{tenancy_name}/{user_name}/{stream_pool_ocid}',
                         sasl_plain_password = auth_token)

  for message in consumer:
    print(f"{message.key}: {message.value}")


if __name__ == '__main__':
    main()