# OCI Data Flow Reading files from Object Storage in Streaming mode

Reviewed: 11.11.2025

Sometimes you would like to continously monitor a Object Storage (S3 compatible) location and incrementally process new incoming data.</br>
With Spark we can create a StreamingQuery using ObjectStorage source and process data from files in streaming mode .... without streaming platform.
All we need is to use spark.readStream with a location - object storage or S3 compatible. 
It looks like this:

## START 

### Define source and target locations
namespace = 'objstr_namespace' </br>
source_bucket = 'src_bucket'</br>
inc_folder = 'inc_folder'</br>
target_bucket = 'trg_bucket'</br>
target_folder = 'trg_folder'</br>
checkpoint_bucket = 'check_bucket'</br>
checkpoint_folder = 'check_folder'</br>
input_path = 'oci://'+source_bucket+'@'+namespace+'/'+inc_folder</br>
archivelocation = 'oci://archivebucket+'@'+namespace+'/arch_folder'</br>

### Infer schema from sample file
example_file = 'oci://'+source_bucket+'@'+namespace+'/'+inc_folder+'/example_file.parquet'</br>
example = spark.read.option("basePath", input_path).option("inferSchema", "true").parquet(example_file)</br>
schema = example.schema</br>

### Read files in streaming mode - streaming query
kafka = spark.readStream.schema(schema).parquet(input_path)</br>
stream_path = 'oci://'+target_bucket+'@'+namespace+'/'+target_folder</br>

wr = kafka.writeStream.queryName('StreamObjects').format("parquet").option("path", stream_path).option("checkpointLocation", 'oci://'+checkpoint_bucket+'@'+namespace+'/'+checkpoint_folder).option("cleanSource", "archive").option("sourceArchiveDir", archivelocation).start()

### Stop streaming query
wr.awaitTermination(60)</br>
wr.stop()</br>

### Check streamed data 
nd = spark.read.option("inferSchema", "true").parquet(stream_path+'/*.parquet')</br>
nd.count()</br>

## END of code

## Additional comments:
You may to provide :</br>
option("checkpointLocation") - to persist medatada about processed files</br>
Option("cleanSource") — It can archive or delete the source file after processing. Values can be archive, delete and default is off.</br>
Option("sourceArchiveDir")  — Archive directory if the cleanSource option is set to archive.</br>


How to use this asset?
Review the code in the notebook and add the code to your personal OCI Data Flow application.

License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
