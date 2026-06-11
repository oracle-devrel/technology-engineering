# How to enable a Public Endpoint Add-on for OCI Streaming with Apache Kafka

OCI Streaming with Apache Kafka(OSAK), is Oracle Cloud Infrastructure’s managed Kafka service. 
It provides Oracle managed Apache Kafka clusters on OCI and exposes Kafka 100% APIs, so Kafka applications and tools can connect without code rewrites.
The most recent OSAK update provdes **Public Endpoint**, which can expose your cluster to public network and allow external application to connect to your cluster. 

It's easy to add **Public Endpoint** to your cluster with the latest OCI CLI - https://github.com/oracle/oci-cli/releases/tag/v3.86.0 :

### 1. Install and verify OCI CLI verion:
OCI Cloud Shell and a Linux/Windows host can be used:

```
python -m pip install "oci-cli==3.86.0" 
oci --version
3.86.0
```

### 2. Review Kafka OCI CLI addons help:
```
oci kafka cluster install-public-connectivity-addon
Usage: oci kafka cluster install-public-connectivity-addon 
           [OPTIONS]

Error: Missing option(s) --name, --authentication-mechanism, --network-cidrs, --kafka-cluster-id.
```

### 3. Generate the network-cidrs.json template
```
oci kafka cluster install-public-connectivity-addon --generate-param-json-input network-cidrs > network-cidrs.json
```
IT Generates a sample JSON file for the --network-cidrs parameter.
The network-cidrs.json file should contain the public IP ranges allowed to access the Kafka public endpoint.
Example:
```
[
  "203.0.113.10/32",
  "198.51.100.0/24"
]
```
### 4. Install the public connectivity add-on
```
oci kafka cluster install-public-connectivity-addon \
  --kafka-cluster-id <cluster-ocid> \
  --name <endpoint-name> \
  --authentication-mechanism SASL \
  --network-cidrs file://network-cidrs.json \
  --wait-for-state SUCCEEDED
```
Parameter	Explanation:
> --kafka-cluster-id	The OCID of the OSAK Kafka cluster.<br>
> --name	The name of the public connectivity add-on.<br>
> --authentication-mechanism SASL	Enables SASL-based authentication for the public endpoint add-on.(SASL or MTLS) <br>
> --network-cidrs file://network-cidrs.json	Loads the allowed CIDR list from the local JSON file, generated in 3.<br>
> --wait-for-state SUCCEEDED	Waits until the OCI work request completes successfully.<br>


### 5. List installed add-ons for the Kafka cluster
```
oci kafka cluster list-addons \
  --kafka-cluster-id <cluster-ocid> \
  --all
```

### 6. Get details for the public endpoint add-on
```
oci kafka cluster get-addon \
  --kafka-cluster-id <cluster-ocid> \
  --addon-name <endpoint-name>
```
The expected output:
```
{
  "data": {
    "addon-type": "PUBLICCONNECTIVITY",
    "authentication-mechanism": "SASL",
    "bootstrap-url": "bootstrap.....com:xxxx",
    "description": null,
    "lifecycle-state": "ACTIVE",
    "name": "SylwekPE",
    "network-cidrs": [
      "0.0.0.0/0"
    ],
    "time-created": "2026-06-11T10:40:50.694000+00:00",
    "time-updated": "2026-06-11T11:08:39.870000+00:00"
  },
  "etag": "1e0c068328174268e1d2ac758c2338e71e7e8236a92da4fc9758cb9bcce176df--gzip"
}
```

Now you can connect to your cluster using provided bootstrap-url from any location (or restriced to CIDRs ranges)





