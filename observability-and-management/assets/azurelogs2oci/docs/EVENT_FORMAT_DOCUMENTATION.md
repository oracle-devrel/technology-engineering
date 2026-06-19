# Microsoft Azure Event Hub Format for OCI Streaming

## 📋 Event Type Being Sent

The Azure Function sends **EntraID Audit logs** in the **Microsoft Azure Event Hub format** to OCI Streaming.

### 🎯 Source System
- **Azure Event Hub** (Microsoft Azure)
- **Log Type**: EntraID Audit logs (Azure Active Directory audit events)
- **Workload**: `AzureActiveDirectory`

### 📊 Event Structure

Each event sent to OCI Streaming follows this exact format from Azure Event Hub:

```json
{
  "TimeGenerated": "2025-12-04T16:41:27.385849+00:00",
  "Id": "2c0113df-342e-482e-b63b-6425d31dea3d",
  "Operation": "Add member to group",
  "RecordType": 11,
  "ResultStatus": "Failure",
  "UserType": "Admin",
  "UserId": "user3679@example.com",
  "UserKey": "11bfead6-20de-405e-a265-e75dfbb48a65",
  "Workload": "AzureActiveDirectory",
  "ObjectId": "19c66d27-6602-43b5-ac0e-5eb87b9f6c8d",
  "ClientIP": "71.29.189.247",
  "OrganizationId": "7c38a3a9-2710-4798-83e6-82f14ba656bd",
  "Version": 1,
  "CreationTime": "2025-12-04T16:41:27",
  "AzureActiveDirectoryEventType": 2,
  "ExtendedProperties": [
    {
      "Name": "UserAgent",
      "Value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    {
      "Name": "RequestType",
      "Value": "OAuth2:Token"
    }
  ],
  "Actor": [
    {
      "ID": "91af402b-5540-4d3d-9029-ff26768def1e",
      "Type": 0
    },
    {
      "ID": "user3939@example.com",
      "Type": 5
    }
  ],
  "ActorContextId": "3cd6474d-ca79-445c-a336-7e21738e935f",
  "ActorIpAddress": "118.248.128.23",
  "InterSystemsId": "2632722a-4354-471b-8356-08d44451f803",
  "IntraSystemId": "ec6869c2-b550-492c-a5f3-b29ee1bd1f43",
  "Target": [
    {
      "ID": "aea77556-60a8-479f-8afc-3c6ecfddbf1f",
      "Type": 0
    }
  ],
  "TargetContextId": "b4c245f3-521b-456d-9eb1-ca5a86d28394",
  "ApplicationId": "00000002-0000-0ff1-ce00-000000000000"
}
```

## 🔍 Field Descriptions

### Core Event Fields
- **`TimeGenerated`**: ISO 8601 timestamp when the event was generated
- **`Id`**: Unique event identifier (UUID)
- **`Operation`**: The operation that was performed (e.g., "Add user", "UserLoggedIn")
- **`RecordType`**: Numeric code indicating the type of audit record (1-20)
- **`ResultStatus`**: "Success" or "Failure"
- **`Workload`**: Always "AzureActiveDirectory" for EntraID events

### User & Identity Fields
- **`UserId`**: Email address of the user who performed the action
- **`UserKey`**: Internal user identifier
- **`UserType`**: "Member", "Guest", or "Admin"
- **`Actor`**: Array of actor objects with ID and Type
- **`ActorContextId`**: Context identifier for the actor
- **`ActorIpAddress`**: IP address of the actor

### Target & Object Fields
- **`ObjectId`**: ID of the object that was affected
- **`Target`**: Array of target objects affected by the operation
- **`TargetContextId`**: Context identifier for the target

### Additional Metadata
- **`ClientIP`**: Client IP address
- **`OrganizationId`**: Azure AD tenant/organization identifier
- **`ApplicationId`**: Application identifier (often Microsoft Graph API)
- **`Version`**: Event schema version
- **`CreationTime`**: When the event was created
- **`AzureActiveDirectoryEventType`**: Specific EntraID event type (1-5)
- **`ExtendedProperties`**: Additional key-value properties
- **`InterSystemsId`**: Internal system identifier
- **`IntraSystemId`**: Internal system identifier

## 🚀 Data Flow

```
Azure Event Hub → Azure Function → OCI Streaming
     ↓              ↓              ↓
EntraID Audit   Transform     PutMessages API
   Events       Format       (Base64 encoded)
```

### Message Transformation

The Azure Function transforms events using `message_transformer.py`:

```json
{
  "source": "AzureEventHub",
  "event_data": {
    // Original EntraID Audit log (above format)
  },
  "metadata": {
    "ingestion_time": null,
    "eventhub_metadata": {
      "partition_id": "...",
      "sequence_number": ...,
      "offset": "...",
      "enqueued_time": "...",
      "properties": {}
    }
  }
}
```

### OCI Streaming Storage

Messages are sent to OCI Streaming using the PutMessages API with Base64 encoding:

- **API**: `PUT /20180418/messages`
- **Encoding**: Base64 encoded JSON
- **Partitioning**: Automatic (based on message key if provided)
- **Limits**: Max 1MB per message, 100 messages per batch

## ✅ Verification

Test with 50 dummy events:

```bash
cd "<repo-root>/Azure-Sentinel/Solutions/Oracle Cloud Infrastructure/Data Connectors"
python3 test_oci_streaming_real.py --count 50 --mock
```

**Expected Output:**
- ✅ 50 EntraID Audit logs generated
- ✅ Microsoft Azure Event Hub format validated
- ✅ Batched into 5 batches of 10 messages each
- ✅ All messages successfully sent to OCI Streaming

## 🔗 Related Components

- **`AzureFunctionOCILogsToStream/`**: Original Event Hub → OCI function
- **`message_transformer.py`**: Event transformation logic
- **`test_send_to_oci.py`**: Existing test script for EntraID logs
- **`test_oci_streaming_real.py`**: Updated test with correct Event Hub format

## 📝 Notes

- **Event Type**: EntraID Audit logs (not Activity logs, not Sign-in logs)
- **Format**: Exact Microsoft Azure Event Hub schema
- **Source**: Azure Event Hub consumer groups
- **Destination**: OCI Streaming service via PutMessages API
- **Encoding**: Base64 JSON in message body
- **Batching**: Automatic batching with configurable sizes
