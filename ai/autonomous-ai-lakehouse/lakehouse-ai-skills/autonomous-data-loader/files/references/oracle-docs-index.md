# Oracle documentation index

Use official Oracle documentation as the authority for syntax, restrictions, and supported options.

## Core data loading

- Load Data into Autonomous AI Database: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/load-data-autonomous.html
- About Data Loading: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/load-data-intro.html
- Load Data from Files in the Cloud: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/load-data-cloud.html
- Load Data into Autonomous AI Database from OCI Object Storage: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-database-load-data-from-oci.html
- Create Credentials and Copy Data into an Existing Table: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/load-data-cloud-copy.html

## JSON document loading

- Load JSON on Autonomous AI Database: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/load-data-cloud-json.html
- Load JSON Documents with Autonomous AI Database: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-json-load.html
- About Loading JSON Documents: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-json-load-about.html
- Monitor and Troubleshoot COPY_COLLECTION Loads: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-json-load-monitor.html

## DBMS_CLOUD reference

- DBMS_CLOUD package reference: https://docs.oracle.com/en/database/oracle/oracle-database/26/arpls/dbms_cloud.html
- DBMS_CLOUD Package Format Options: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/format-options.html
- DBMS_CLOUD Package Format Options for Avro, ORC, or Parquet: https://docs.oracle.com/en/cloud/paas/autonomous-database/adbsa/dbms-cloud-avro-orc-parquet-options.html

## Monitoring and troubleshooting

- Monitor and Troubleshoot COPY_DATA Loads: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/load-data-cloud-monitor.html
- Monitor and Troubleshoot COPY_COLLECTION Loads: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-json-load-monitor.html

## Object operations

- DBMS_CLOUD object and file operations such as LIST_OBJECTS and GET_OBJECT are covered in the DBMS_CLOUD package reference: https://docs.oracle.com/en/database/oracle/oracle-database/26/arpls/dbms_cloud.html

## Notes for this skill

- This skill treats XML loading as version-specific. Verify the exact Autonomous documentation for the user's environment before generating XML load workflows.
- This skill does not bundle examples for Data Pump or DBMS_CLOUD_PIPELINE.

## Apache Iceberg on OCI Object Storage

- Query Apache Iceberg Tables: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/query-external-data-apache-iceberg.html
- Setup Requirements for Iceberg: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/query-external-data-apache-iceberg.html#GUID-3F19A6A1-022B-4C87-A0F1-5D9F9938A52B
- Hadoop/Filesystem direct metadata and OCI Object Storage examples: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/query-external-data-apache-iceberg.html

Notes for this skill:

- Generate only OCI Object Storage Iceberg patterns: direct `metadata.json` and HadoopCatalog on OCI.
- Do not generate Unity, Polaris, AWS Glue, S3, Azure, or GCS Iceberg workflows in this skill.
- Iceberg external tables provide query access and do not copy Iceberg data into Autonomous.
