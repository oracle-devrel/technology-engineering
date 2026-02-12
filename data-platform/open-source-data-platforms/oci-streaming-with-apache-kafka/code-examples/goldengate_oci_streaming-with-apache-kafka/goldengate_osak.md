# OCI GoldenGate connection to OCI Streaming with Apache Kafka

### This guide documents how to set up OCI GoldenGate connection to OCI Streaming with Apache Kafka (OSAK) cluster.
---

#### Requirments:
1. OCI GoldenGate for Distributed Applications and Analytics (previously named Big Data) is created and is accessible
2. OCI Streaming with Apache Kafka cluster and OCI GoldenGate are in the same VCN or VCN peering is enabled.
3. SASL-SCRAM amd superuser is enabled for OCI Streaming with Apache Kafka cluster
4. Check your OSAK bootstrap:port - we will need it 

---

1. Go to OCI GoldenGate Connections tab and **Create Connection**

2. Choose your connection Name, Description and select Apache Kafka from **Type** list:
<img width="898" height="754" alt="image" src="https://github.com/user-attachments/assets/59abcf2b-0921-40e5-a6df-0dabab5ec09d" />

3. Enter your bootstrap and  port:
<img width="1284" height="207" alt="image" src="https://github.com/user-attachments/assets/8de3524c-09d3-4770-880a-d185a5fdde70" />

4. Select SASL over SSL:
<img width="874" height="296" alt="image" src="https://github.com/user-attachments/assets/a504b2c2-d508-4813-857d-c8c7b3ba9f67" />

5. Enter super-user

6. Scroll down to **Advanced options** and deselect Use Vaults:
<img width="668" height="344" alt="image" src="https://github.com/user-attachments/assets/08881cc9-8b94-46d4-8f8e-48c68aaf3fb2" />

7. Enter your superuser password

8. Create a text file producer.properties (name it as you wish):
    ```
    security.protocol: SASL_SSL
    sasl.mechanism: SCRAM-SHA-512
    ```
  
9. Scroll down to **Settings** and pick Producer properties - Drop a file or select a file :
<img width="892" height="385" alt="image" src="https://github.com/user-attachments/assets/18b83976-5702-4c4a-aff9-8e787d7445c4" />

10. Click **Create** and the connection is done
    
11. Go to Assigned Deployment and **Assign Deployment** button to select your OCI GG-DAA deployment:
<img width="758" height="476" alt="image" src="https://github.com/user-attachments/assets/ad5234ec-0272-45f1-9642-cc16a8163c41" />

12. Now you can login to OCI GoldenGate console, Create GG Replicat and stream data to OSAK cluster

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.