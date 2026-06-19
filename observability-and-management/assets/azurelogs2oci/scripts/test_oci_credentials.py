#!/usr/bin/env python3
"""
Test OCI credentials and connectivity to ensure the Azure Function can authenticate
"""

import os
import sys
import json
import logging
import re
from dotenv import load_dotenv

# Add the function directory to path (eventhub_to_oci package)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'function', 'EventHubsNamespaceToOCIStreaming', 'eventhub_to_oci'))

try:
    # Import the function's OCI utilities when Azure Functions deps are present.
    from __init__ import get_oci_config_from_env, validate_env, mask, parse_key
except ModuleNotFoundError as exc:
    if exc.name != "azure.functions":
        raise

    def parse_key(key_input: str) -> str:
        try:
            import textwrap

            normalized = (key_input or "").replace("\\n", "\n").strip()
            begin_line = re.search(r'-----BEGIN [A-Z ]+-----', normalized).group()
            end_line = re.search(r'-----END [A-Z ]+-----', normalized).group()
            key_block = normalized[normalized.index(begin_line) + len(begin_line): normalized.index(end_line)]

            encr_lines = ''
            proc_type_line = re.search(r'Proc-Type: [^\n]+', key_block)
            dec_info_line = re.search(r'DEK-Info: [^\n]+', key_block)
            if proc_type_line:
                encr_lines += proc_type_line.group().strip() + '\n'
                key_block = key_block.replace(proc_type_line.group(), '')
            if dec_info_line:
                encr_lines += dec_info_line.group().strip() + '\n'
                key_block = key_block.replace(dec_info_line.group(), '')

            body_compact = re.sub(r'\s+', '', key_block)
            wrapped_body = '\n'.join(textwrap.wrap(body_compact, 64))
            parts = [begin_line]
            if encr_lines:
                parts.append(encr_lines.rstrip('\n'))
            parts.append(wrapped_body)
            parts.append(end_line)
            return '\n'.join(parts)
        except Exception as error:
            raise Exception('Error while reading private key.') from error

    def mask(value: str, keep: int = 6) -> str:
        if not value:
            return ""
        if len(value) <= keep:
            return "***"
        return f"{value[:keep]}...***"

    def get_oci_config_from_env() -> dict:
        return {
            "user": os.environ['user'],
            "key_content": parse_key(os.environ['key_content']),
            "pass_phrase": os.environ.get('pass_phrase', ''),
            "fingerprint": os.environ['fingerprint'],
            "tenancy": os.environ['tenancy'],
            "region": os.environ['region'],
        }

    def validate_env():
        endpoint = env_value("MessageEndpoint", "OCI_MESSAGE_ENDPOINT")
        stream_ocid = env_value("StreamOcid", "OCI_STREAM_OCID")
        if not endpoint or not stream_ocid:
            raise RuntimeError("Missing MessageEndpoint/StreamOcid (or OCI_MESSAGE_ENDPOINT/OCI_STREAM_OCID)")
        if "streampool" in stream_ocid:
            raise RuntimeError("StreamOcid points to a Stream Pool. Use the Stream OCID (ocid1.stream...) instead.")
        return endpoint, stream_ocid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def env_value(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""

def test_oci_credentials():
    """Test OCI credentials and connectivity"""

    print("=" * 80)
    print("🧪 OCI Credentials and Connectivity Test")
    print("=" * 80)
    print()

    # Try to load environment variables
    env_candidates = [
        os.path.join(os.path.dirname(__file__), '.env.local'),
        os.path.join(os.path.dirname(__file__), '..', '.env.local'),
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.path.dirname(__file__), '..', 'function', 'EventHubsNamespaceToOCIStreaming', '.env.local'),
        os.path.join(os.path.dirname(__file__), '..', 'function', 'EventHubsNamespaceToOCIStreaming', '.env')
    ]

    env_loaded = False
    for env_file in env_candidates:
        if os.path.exists(env_file):
            print(f"📄 Loading environment from: {env_file}")
            load_dotenv(env_file)
            env_loaded = True
            break

    if not env_loaded:
        print("❌ No .env.local or .env file found. Checking environment variables directly...")

    # Check environment variables
    required_vars = [
        ('user', ('user',)),
        ('key_content', ('key_content',)),
        ('fingerprint', ('fingerprint',)),
        ('tenancy', ('tenancy',)),
        ('region', ('region',)),
        ('MessageEndpoint', ('OCI_MESSAGE_ENDPOINT', 'MessageEndpoint')),
        ('StreamOcid', ('OCI_STREAM_OCID', 'StreamOcid')),
    ]
    missing_vars = []

    print("\n🔍 Environment Variables Check:")
    for label, candidates in required_vars:
        value = env_value(*candidates)
        if value:
            print(f"  ✅ {label}: {mask(value)}")
        else:
            print(f"  ❌ {label}: NOT SET")
            missing_vars.append(label)

    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n💡 Make sure these are set in your Azure Function App Settings:")
        for var in missing_vars:
            print(f"   - {var}")
        return False

    print("\n✅ All required environment variables are present")

    # Test OCI configuration
    try:
        print("\n🔧 Testing OCI Configuration...")
        cfg = get_oci_config_from_env()
        print("✅ OCI configuration built successfully")

        # Test OCI validation
        import oci
        oci.config.validate_config(cfg)
        print("✅ OCI configuration validation passed")

        # Test Stream endpoint validation
        endpoint, stream_ocid = validate_env()
        print(f"✅ Stream endpoint validated: {mask(endpoint)}")
        print(f"✅ Stream OCID validated: {mask(stream_ocid)}")

        # Test Stream client initialization
        print("\n🌐 Testing OCI Stream Client...")
        stream_client = oci.streaming.StreamClient(cfg, service_endpoint=endpoint)
        admin_client = oci.streaming.StreamAdminClient(cfg)
        print("✅ OCI Stream client initialized successfully")

        # Try a simple API call to test authentication
        print("\n🔐 Testing OCI Authentication...")
        try:
            # Try to get stream info (this will test if credentials work)
            response = admin_client.get_stream(stream_ocid)
            print("✅ OCI authentication successful!")
            print(f"   Stream name: {response.data.name}")
            print(f"   Stream state: {response.data.lifecycle_state}")
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                print("⚠️  Stream not found - but authentication worked!")
                print("   This means your credentials are correct, but the stream OCID might be wrong")
            else:
                print(f"❌ OCI API authentication failed: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error during authentication test: {e}")
            return False

    except Exception as e:
        print(f"❌ OCI configuration test failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("🎉 OCI Credentials Test PASSED!")
    print("   ✅ All environment variables present")
    print("   ✅ OCI configuration valid")
    print("   ✅ Authentication successful")
    print("   ✅ Stream client can connect")
    print("=" * 80)

    return True

def test_sample_message():
    """Test sending a sample message to OCI"""

    print("\n📤 Testing Sample Message Send...")

    try:
        # Import the OCI sender
        try:
            from __init__ import OciStreamSender, HubBuffer
        except ModuleNotFoundError as exc:
            if exc.name != "azure.functions":
                raise

            from base64 import b64encode
            from oci.streaming.models import PutMessagesDetails, PutMessagesDetailsEntry

            class OciStreamSender:
                def __init__(self, config: dict, message_endpoint: str, stream_ocid: str):
                    import oci

                    oci.config.validate_config(config)
                    self.client = oci.streaming.StreamClient(config, service_endpoint=message_endpoint)
                    self.stream_ocid = stream_ocid

                def send_batch(self, payloads):
                    entries = [
                        PutMessagesDetailsEntry(value=b64encode(payload.encode("utf-8")).decode("utf-8"))
                        for payload in payloads
                    ]
                    req = PutMessagesDetails(messages=entries)
                    resp = self.client.put_messages(self.stream_ocid, req)
                    sent = failed = 0
                    for entry in (resp.data.entries or []):
                        if getattr(entry, "error", None):
                            failed += 1
                        else:
                            sent += 1
                    return sent, failed

            class HubBuffer:
                def __init__(self, sender, max_count: int, max_bytes: int):
                    self.sender = sender
                    self.sent = 0
                    self.failed = 0
                    self.buf = []

                def add(self, payload: str):
                    self.buf.append(payload)

                def flush(self):
                    sent, failed = self.sender.send_batch(self.buf)
                    self.sent += sent
                    self.failed += failed
                    self.buf.clear()

        # Get configuration
        endpoint, stream_ocid = validate_env()
        cfg = get_oci_config_from_env()

        # Create sender
        sender = OciStreamSender(cfg, endpoint, stream_ocid)
        buffer = HubBuffer(sender, max_count=10, max_bytes=1024*1024)

        # Create a sample EntraID audit log
        sample_log = {
            "TimeGenerated": "2025-12-04T17:00:00.000Z",
            "Id": "test-event-123",
            "Operation": "Test: User login",
            "RecordType": 15,
            "ResultStatus": "Success",
            "UserType": "Member",
            "UserId": "test@example.com",
            "UserKey": "test-user-key",
            "Workload": "AzureActiveDirectory",
            "ObjectId": "test-object-id",
            "ClientIP": "192.168.1.1",
            "OrganizationId": "test-org-id",
            "Version": 1,
            "CreationTime": "2025-12-04T17:00:00",
            "AzureActiveDirectoryEventType": 1,
            "ApplicationId": "00000002-0000-0ff1-ce00-000000000000"
        }

        # Send the sample message
        json_message = json.dumps(sample_log)
        print(f"📝 Sample message size: {len(json_message)} bytes")
        print(f"📄 Sample message: {json_message[:200]}...")

        buffer.add(json_message)
        buffer.flush()

        sent = buffer.sent
        failed = buffer.failed

        if sent > 0 and failed == 0:
            print("✅ Sample message sent successfully to OCI Streaming!")
            return True
        else:
            print(f"❌ Sample message send failed: sent={sent}, failed={failed}")
            return False

    except Exception as e:
        print(f"❌ Sample message test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_oci_credentials()
    if success:
        # If credentials work, test sending a sample message
        test_sample_message()

    sys.exit(0 if success else 1)
