from __future__ import print_function
from pyspark import SparkConf
from pyspark.sql import SparkSession, SQLContext
import sys
from random import random
from operator import add
import argparse
import os
from pyspark.sql.functions import *
from pyspark.sql.functions import col, sum, to_date, from_unixtime, unix_timestamp, expr
from pyspark.sql.types import StringType


def main():
    
    print("Start")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()

    # Set up Spark.
    spark_session = get_dataflow_spark_session()
    sql_context = SQLContext(spark_session)  

    #read csv file
    df = sql_context.read.option("delimiter", ",").option("header", True).csv(args.input_path)

    #Group by Customer ID, multiple values.
    grouped_df = df.groupBy("customer_id").agg(avg("quantity").alias("avg_quantity_ordered"),
                                          (avg("sales_price").alias("avg_sales_price")),
                                          (avg("discount").alias("avg_discount")),
                                          (avg("gross_unit_price").alias("avg_gross_unit_price")),
                                          (avg("shipping_cost").alias("avg_shipping_costs")))

    ## round to 2 decimals
    grouped_df = grouped_df.withColumn('avg_quantity_ordered', round(grouped_df.avg_quantity_ordered, 2))
    grouped_df = grouped_df.withColumn('avg_sales_price', round(grouped_df.avg_sales_price, 2))
    grouped_df = grouped_df.withColumn('avg_discount', round(grouped_df.avg_discount, 2))
    grouped_df = grouped_df.withColumn('avg_gross_unit_price', round(grouped_df.avg_gross_unit_price, 2))
    grouped_df = grouped_df.withColumn('avg_shipping_costs', round(grouped_df.avg_shipping_costs, 2))


    print("Saving output csv in bucket as one file")
    grouped_df.repartition(1).write.mode("overwrite").option("header", True).csv(args.output_path)

    #grouped_df.show()   

    
    
def get_dataflow_spark_session(
    app_name="DataFlow", file_location=None, profile_name=None, spark_config={}
):
    """
    Get a Spark session in a way that supports running locally or in Data Flow.
    """
    if in_dataflow():
        spark_builder = SparkSession.builder.appName(app_name)
    else:
        # Import OCI.
        try:
            import oci
        except:
            raise Exception(
                "You need to install the OCI python library to test locally"
            )

        # Use defaults for anything unset.
        if file_location is None:
            file_location = oci.config.DEFAULT_LOCATION
        if profile_name is None:
            profile_name = oci.config.DEFAULT_PROFILE

        # Load the config file.
        try:
            oci_config = oci.config.from_file(
                file_location=file_location, profile_name=profile_name
            )
        except Exception as e:
            print("You need to set up your OCI config properly to run locally")
            raise e
        conf = SparkConf()
        conf.set("fs.oci.client.auth.tenantId", oci_config["tenancy"])
        conf.set("fs.oci.client.auth.userId", oci_config["user"])
        conf.set("fs.oci.client.auth.fingerprint", oci_config["fingerprint"])
        conf.set("fs.oci.client.auth.pemfilepath", oci_config["key_file"])
        conf.set(
            "fs.oci.client.hostname",
            "https://objectstorage.{0}.oraclecloud.com".format(oci_config["region"]),
        )
        spark_builder = SparkSession.builder.appName(app_name).config(conf=conf)

    # Add in extra configuration.
    for key, val in spark_config.items():
        spark_builder.config(key, val)

    # Create the Spark session.
    session = spark_builder.getOrCreate()
    return session


def in_dataflow():
    """
    Determine if we are running in OCI Data Flow by checking the environment.
    """
    if os.environ.get("HOME") == "/home/dataflow":
        return True
    return False


if __name__ == "__main__":
    main()
