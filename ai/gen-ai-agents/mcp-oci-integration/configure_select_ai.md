# Select AI Configuration

## Introduction
**Select AI** is a functionality provided by **Oracle Autonomous Database (ADB)**.

It enables to do easily **Text2SQL**, in other words to translate a request for data, expressed in Natural Language (NL),
in a SQL statement working in your Database.

Example:

* (NL): List the names of all F1 drivers.
* (SQL): SELECT DRIVER_NAME from F1USER.F1_DRIVERS

## Configuration
To use **Select AI** you need an ADB, with the schema where you want to run your SQL statements, and a Large Language Model (LLM).
You can use a model provided by **OCI Generative AI** service, or a model from another supported provider (see Oracle docs for the list).

In this short note, we will provide information to configure Select AI using OCI Generative AI.

### Store credentials and create a Select AI **Profile**
Create in your OCI account (enabled to use Generative AI) an API key. Save the keys.

Create and store a **credential**, with a name, inside your DB schema (the schema you're using to execute Select AI, not the data schema). 

Execute the following procedure, with your data

```
BEGIN
  DBMS_CLOUD.create_credential(
    credential_name => 'MY_CREDENTIAL_NAME',
    user_ocid       => 'ocid1.user.oc1..my_user_oci',
    tenancy_ocid    => 'ocid1.tenancy.oc1..my_tenancy_ocid',
    fingerprint     => 'fingerprint of my key',
    private_key     => 'cut&paste your private key here'
  );
END;
/
```

Create a **Select AI profile**. Execute the following procedure, again with your data.
(put the list of the object in the schema you need to make visible to Select AI)

```
BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
      profile_name => 'OCI_GENERATIVE_AI_PROFILE' ,
      attributes   =>
      '{
        "provider": "oci",
        "region": "us-chicago-1",
        "oci_compartment_id": "ocid1.compartment.oc1..my compartment ocid",
        "credential_name": "MY_CREDENTIAL_NAME",
        "object_list": [
          {"owner": "SH", "name": "CHANNELS"},
          {"owner": "SH", "name": "COSTS"},
          {"owner": "SH", "name": "COUNTRIES"},
          {"owner": "SH", "name": "CUSTOMERS"},
          {"owner": "SH", "name": "PRODUCTS"},
          {"owner": "SH", "name": "PROMOTIONS"},
          {"owner": "SH", "name": "SALES"},
          {"owner": "SH", "name": "SUPPLEMENTARY_DEMOGRAPHICS"},
          {"owner": "SH", "name": "TIMES"}
        ],
        "model": "xai.grok-4"
      }');

END;
```

## Test Select AI
You can test that the configuration is correctly working using code like the one in [test select AI](./test_selectai01.py)

The code is using the new library from Oracle: **select-ai**
To use it, you need also to have installed in your Python environment the library: **oracledb**

```
pip install select_ai
pip install oracledb
```

## References
For more information, see 
* [Getting Started with Select AI](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/select-ai-get-started.html)
* [How to use Select AI: A step-by-step guide](https://blogs.oracle.com/datawarehousing/post/how-to-use-oracle-select-ai-a-stepbystep-guide-generative-ai)
