# FOCUS™ Support for OCI

FOCUS™ is a technical specification defined to support a true multi-cloud consistent experience. It will allow customers to access cost and all related data, including billing, in a normalized, cloud-provider agnostic format. The specification will encompass Saas services as well. 

**How does it work**
FOCUS™ specifications are available [here] (https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec).
Dedicated converters are being developed per cloud provider.
Progresses per provider can be found [here] (https://github.com/finopsfoundation/focus_converters/blob/dev/progress/README.md).
The output of converters is provided in Parquet format. This will allow the data from different providers to be imported into ADW and [queried](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/autonomous-database-serverless/doc/query-external-parquet-avro.html) as needed. 
A specific converter for OCI is available [here](https://github.com/finopsfoundation/focus_converters/tree/dev/focus_converter_base/focus_converter/conversion_configs/oci).
