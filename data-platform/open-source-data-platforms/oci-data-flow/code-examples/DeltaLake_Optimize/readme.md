# Delta Lake Optimization

Oracle Cloud Infrastructure (OCI) Data Flow is a fully managed Apache Spark service that performs processing tasks on extremely large datasets—without infrastructure to deploy or manage. 
Developers can also use Spark Streaming to perform cloud ETL on their continuously produced streaming data.
However Spark structured streaming application can produce thousants of small files (according to microbatching and number of executors), which leads to performance degradadion.
![small files in datalake](https://github.com/oracle-devrel/technology-engineering/blob/sylwesterdec-patch-6/data-platform/open-source-data-platforms/oci-data-flow/code-examples/DeltaLake_Optimize/files_in_datalake.png)

That's why the most crucial decision is file format for your datalake. Small files can be a problem because they slow down your query reads. Listing, opening and closing many small files incurs expensive overhead. This is called “the Small File Problem”. 
You can reduce the Small File Problem overhead by combining the data into bigger, more efficient files. Instead of doing it manually, pick the datalake format (delta, iceberg) and use build-in functions.

Delta Lake enables building a Lakehouse architecture on top of data lakes. Delta Lake provides ACID transactions, scalable metadata handling, and unifies streaming and batch data processing on top of existing data lakes.
For spark streaming application and realtime processing DeltaLake has one sighificant advantage - [built-in optimization](https://delta.io/blog/delta-lake-optimize/)   
OCI Data Flow supports Delta Lake by default when your Applications run Spark 3.2.1 or later - [doc](https://docs.oracle.com/en-us/iaas/data-flow/using/delta-lake-about.htm)

How to optimize data lake using DeltaLake functions:
Configure your preferences (please check DeltaLake doc):

spark.conf.set('spark.databricks.delta.retentionDurationCheck.enabled', 'False')
spark.conf.set('spark.databricks.delta.optimize.repartition.enabled','True')
spark.conf.set('spark.databricks.delta.optimize.preserveInsertionOrder', 'False')

Preserve vacuum history:
spark.conf.set('spark.databricks.delta.vacuum.logging.enabled','True')

Set retention time for optimized files (ready to delete:  
spark.conf.set("spark.databricks.delta.deletedFileRetentionDuration","0")


Check existing table details (look for numFiles and sizeInBytes:
spark.sql("describe detail atm").show(truncate=False)
+------+------------------------------------+--------------------------------+-----------+----------------------------------------------------+-----------------------+-------------------+------------------+--------+-----------+----------+----------------+----------------+------------------------+
|format|id                                  |name                            |description|location                                            |createdAt              |lastModified       |partitionColumns  |numFiles|sizeInBytes|properties|minReaderVersion|minWriterVersion|tableFeatures           |
+------+------------------------------------+--------------------------------+-----------+----------------------------------------------------+-----------------------+-------------------+------------------+--------+-----------+----------+----------------+----------------+------------------------+
|delta |c15ad4ca-8c0f-4747-b064-1492d7b4b3c4|spark_catalog.default.hsl_trains|NULL       |oci://dataflow_app@fro8fl9kuqli/hsl_trains_data_part|2024-09-05 10:19:10.057|2024-09-06 08:45:01|[year, month, day]|2024    |16333676   |{}        |1               |2               |[appendOnly, invariants]|
+------+------------------------------------+--------------------------------+-----------+----------------------------------------------------+-----------------------+-------------------+------------------+--------+-----------+----------+----------------+----------------+------------------------+

Run optimzation:
spark.sql("OPTIMIZE atm").show(truncate=False)

Check files you can delete:
spark.sql("vacuum atm RETAIN 0 HOURS DRY RUN")

Delete optimized and consolidated files:
spark.sql("vacuum atm RETAIN 0 HOURS")

and check details of your table:
spark.sql("describe detail atm").show(truncate=False)
+----------------+----------------+------------------------+
|format|id                                  |name                            |description|location                                            |createdAt              |lastModified       |partitionColumns  |numFiles|sizeInBytes|properties|minReaderVersion|minWriterVersion|tableFeatures           |
+------+------------------------------------+--------------------------------+-----------+----------------------------------------------------+-----------------------+-------------------+------------------+--------+-----------+----------+----------------+----------------+------------------------+
|delta |c15ad4ca-8c0f-4747-b064-1492d7b4b3c4|spark_catalog.default.hsl_trains|NULL       |oci://dataflow_app@fro8fl9kuqli/hsl_trains_data_part|2024-09-05 10:19:10.057|2024-09-06 08:47:48|[year, month, day]|7       |1583521    |{}        |1               |2               |[appendOnly, invariants]|
+------+------------------------------------+--------------------------------+-----------+----------------------------------------------------+-----------------------+-------------------+------------------+--------+-----------+----------+----------------+----------------+------------------------+                                                                                                 

Enjoy increased performance of your queries!                                                                                                                 
                                                                                                                          
                                                                                                                          
  
# License
Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
