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
  ## create connection
    producer = KafkaProducer(bootstrap_servers = f'cell-1.streaming.{region}.oci.oraclecloud.com:9092', linger_ms = 50, batch_size  = 2,
                         security_protocol = 'SASL_SSL', sasl_mechanism = 'PLAIN',
                         value_serializer = lambda v: v.encode('utf-8'),
                         sasl_plain_username = f'{tenancy_name}/{user_name}/{stream_pool_ocid}',
                         sasl_plain_password = auth_token)
  #create random data
    pd_list = []
    
    for i in range(500):

        #set randomness, so each goes up and down together
        randomness_sun_price = random.uniform(0.95, 1.015)
        randomness_wspd = random.uniform(0.90, 0.95)
        cust_id = str(uuid.uuid4())
        kwh_producing = round(random.uniform(0.11, 5.55), 2)
        kwh_consuming = round(random.uniform(3.55, 19.55), 2)

        ##weather info 
        temp = randomness_sun_price
        wspd =  randomness_wspd
        tsun = randomness_sun_price *1.22 
        energy_price = randomness_sun_price *0.89

        pd_list.append([cust_id, kwh_producing, kwh_consuming, temp, wspd, tsun, energy_price])

    df_out = pd.DataFrame(pd_list, columns = ["cust_id", "kwh_producing", "kwh_consuming", "temp", "windspeed","sun_light", "energy_price"])

  #push random data to stream
    for index, row in df_out.iterrows():
        row_json = row.to_json(orient='records', lines=True)
        producer.send(stream_name, value=row_json)
        producer.flush()
        print(f"Producing to stream: {row_json}")
        sleep(5)


if __name__ == '__main__':
    main()