# Fraud Detection Kafka Demo

This project demonstrates a real-time fraud detection pipeline using Kafka, OCI Object Storage, OCI Data Science model deployment and OCI Monitoring. A producer replays sample transaction data into Kafka, while a consumer scores each transaction with a deployed model, publishes detected fraud events, writes scored results to Object Storage and emits operational metrics.

Two services are included:

- `consumer`: consumes Kafka messages, scores them, publishes fraud events, writes scored CSV files to Object Storage and emits metrics.
- `producer`: reads sample transactions from Object Storage and publishes them to Kafka.

## Prerequisites

- The default configuration file assumes you are working in /home/opc
- Linux host with `systemd` available
- Python 3
- OCI CLI config available at `~/.oci/config`
- Access to OCI Object Storage
- Access to Kafka
- A deployed OCI model endpoint that accepts the transaction fields used by this project

## 1. Clone

```bash
git clone <repository-url>
cd /path/to/fraud-detection-demo
```

## 2. Configure

Create local config files:

```bash
cp producer/app_config.yaml.example producer/app_config.yaml
cp producer/kafka_client.properties.example producer/kafka_client.properties
cp consumer/app_config.yaml.example consumer/app_config.yaml
cp consumer/kafka_client.properties.example consumer/kafka_client.properties
```

Edit the copied files with your OCI and Kafka values.

In the consumer config, replace the model endpoint with your deployed OCI model URL:

```yaml
model:
  endpoint: "https://<your-model-endpoint>/predict"
```


## 3. Kafka Topics

Create the Kafka topics before starting the pipeline.

The producer topic must match the consumer input topic.

Example:

- Producer topic: `sample-transactions`
- Consumer input topic: `sample-transactions`
- Consumer output topic: `fraud-scored-transactions`

## 4. Install

```bash
sudo bash scripts/install_services.sh
```

The services run from this cloned repository folder.

## 5. Start Services

```bash
bash scripts/start_services.sh
```

This starts the Flask services for the consumer and producer. It does not start processing messages yet.

## 6. Start Pipeline

```bash
bash scripts/start_pipeline.sh
```

This starts the actual pipeline processing by calling the consumer and producer `/start` endpoints.

Start the consumer before the producer so messages are consumed as they are produced. `start_pipeline.sh` does this order for you.

## 7. Check Status

```bash
bash scripts/status_services.sh
```

Endpoints:

```text
Consumer: http://localhost:5001/status
Producer: http://localhost:5000/status
```

## Logs

```bash
sudo journalctl -u fraud-producer -n 100 -l --no-pager
sudo journalctl -u fraud-consumer -n 100 -l --no-pager
```

## Stop

```bash
bash scripts/stop_services.sh
```
