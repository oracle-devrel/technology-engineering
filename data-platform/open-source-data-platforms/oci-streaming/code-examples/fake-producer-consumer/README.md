# Example of Producing and Consuming for OCI Streaming

Reviewed: 22.10.2024

1. Create compute instance. Oracle Linux 7.
2. Run the below to install Git, clone the repo, and install several packages
  ```
  sudo dnf install git-all -y
  git clone https://github.com/bobpeulen/apache_kafka.git
  sudo pip3 install kafka-python3 pandas numpy datetime
  ```

3. Run the producer. 

```
python apache_kafka/oci_streaming/producer.py  \
-tenancy_name 'oraemeadatamgmt' \
-region 'eu-frankfurt-1' \
-user_name 'OracleIdentityCloudService/bob.peulen@oracle.com' \
-stream_name 'OpenSourceData_stream_1' \
-stream_pool_ocid 'ocid1.streampool.oc1.eu-frankfurt-1.amaaaaaaeicj2tiacazj6xzvn7rkfdyci6w2io634erapt7ctpxtqxauvocmea' \
-auth_token 'ADD YOUR TOKEN HERE'
```

4. Run the consumer.
 ```
  python apache_kafka/oci_streaming/consumer.py  \
  -tenancy_name 'oraemeadatamgmt' \
  -region 'eu-frankfurt-1' \
  -user_name 'OracleIdentityCloudService/bob.peulen@oracle.com' \
  -stream_name 'OpenSourceData_stream_1' \
  -stream_pool_ocid 'ocid1.streampool.oc1.eu-frankfurt-1.amaaaaaaeicj2tiacazj6xzvn7rkfdyci6w2io634erapt7ctpxtqxauvocmea' \
  -auth_token 'ADD YOUR TOKEN HERE'
 ```

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.