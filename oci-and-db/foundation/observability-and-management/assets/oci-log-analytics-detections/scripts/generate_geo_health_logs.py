"""
Generate synthetic multicloud health heartbeat logs for Geographic Health visualization.

Produces NDJSON logs representing health heartbeats from instances across
OCI, Azure, AWS, and GCP regions worldwide. Each log includes lat/lon coordinates,
cloud provider, region, instance metadata, and health metrics — suitable for
plotting on a global map widget in OCI Log Analytics.

Output:
  test_data/multicloud_health.jsonl   Health heartbeat events

Usage:
  python3 scripts/generate_geo_health_logs.py
  python3 scripts/generate_geo_health_logs.py --unhealthy-pct 10
  python3 scripts/generate_geo_health_logs.py --interval 5  # minutes between heartbeats
"""

import json
import os
import random
import sys
import uuid
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import COMPARTMENT_ID
from test_data_manifest import rebuild_manifest

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / 'test_data'

BASE_TIME = datetime.now(timezone.utc) - timedelta(hours=1)

# ═══════════════════════════════════════════════════════════════════
#  Multicloud Region Definitions (with real lat/lon for map plotting)
# ═══════════════════════════════════════════════════════════════════

OCI_REGIONS = [
    {"region": "us-ashburn-1",       "display": "US East (Ashburn)",      "lat": 39.0438, "lon": -77.4874, "country": "US"},
    {"region": "us-phoenix-1",       "display": "US West (Phoenix)",      "lat": 33.4484, "lon": -112.0740, "country": "US"},
    {"region": "us-chicago-1",       "display": "US Midwest (Chicago)",   "lat": 41.8781, "lon": -87.6298, "country": "US"},
    {"region": "eu-frankfurt-1",     "display": "Germany Central (Frankfurt)", "lat": 50.1109, "lon": 8.6821, "country": "DE"},
    {"region": "eu-amsterdam-1",     "display": "Netherlands (Amsterdam)", "lat": 52.3676, "lon": 4.9041, "country": "NL"},
    {"region": "uk-london-1",        "display": "UK South (London)",      "lat": 51.5074, "lon": -0.1278, "country": "GB"},
    {"region": "ap-tokyo-1",         "display": "Japan East (Tokyo)",     "lat": 35.6762, "lon": 139.6503, "country": "JP"},
    {"region": "ap-mumbai-1",        "display": "India West (Mumbai)",    "lat": 19.0760, "lon": 72.8777, "country": "IN"},
    {"region": "ap-sydney-1",        "display": "Australia East (Sydney)", "lat": -33.8688, "lon": 151.2093, "country": "AU"},
    {"region": "sa-saopaulo-1",      "display": "Brazil East (Sao Paulo)", "lat": -23.5505, "lon": -46.6333, "country": "BR"},
    {"region": "me-jeddah-1",        "display": "Saudi Arabia (Jeddah)",  "lat": 21.4858, "lon": 39.1925, "country": "SA"},
    {"region": "af-johannesburg-1",  "display": "South Africa (Johannesburg)", "lat": -26.2041, "lon": 28.0473, "country": "ZA"},
]

AZURE_REGIONS = [
    {"region": "eastus",             "display": "East US (Virginia)",      "lat": 37.3719, "lon": -79.8164, "country": "US"},
    {"region": "westus2",            "display": "West US 2 (Washington)",  "lat": 47.2330, "lon": -119.8526, "country": "US"},
    {"region": "westeurope",         "display": "West Europe (Netherlands)", "lat": 52.3667, "lon": 4.8945, "country": "NL"},
    {"region": "northeurope",        "display": "North Europe (Ireland)",  "lat": 53.3478, "lon": -6.2597, "country": "IE"},
    {"region": "uksouth",            "display": "UK South (London)",       "lat": 51.5074, "lon": -0.1278, "country": "GB"},
    {"region": "southeastasia",      "display": "Southeast Asia (Singapore)", "lat": 1.3521, "lon": 103.8198, "country": "SG"},
    {"region": "japaneast",          "display": "Japan East (Tokyo)",      "lat": 35.6762, "lon": 139.6503, "country": "JP"},
    {"region": "australiaeast",      "display": "Australia East (Sydney)", "lat": -33.8688, "lon": 151.2093, "country": "AU"},
    {"region": "centralindia",       "display": "Central India (Pune)",    "lat": 18.5204, "lon": 73.8567, "country": "IN"},
    {"region": "brazilsouth",        "display": "Brazil South (Sao Paulo)", "lat": -23.5505, "lon": -46.6333, "country": "BR"},
    {"region": "canadacentral",      "display": "Canada Central (Toronto)", "lat": 43.6532, "lon": -79.3832, "country": "CA"},
    {"region": "koreacentral",       "display": "Korea Central (Seoul)",   "lat": 37.5665, "lon": 126.9780, "country": "KR"},
]

GCP_REGIONS = [
    {"region": "us-east1",           "display": "US East (S. Carolina)",   "lat": 33.8361, "lon": -81.1637, "country": "US"},
    {"region": "us-west1",           "display": "US West (Oregon)",        "lat": 45.5945, "lon": -121.1787, "country": "US"},
    {"region": "us-central1",        "display": "US Central (Iowa)",       "lat": 41.2619, "lon": -95.8608, "country": "US"},
    {"region": "europe-west1",       "display": "Europe West (Belgium)",   "lat": 50.4473, "lon": 3.8196, "country": "BE"},
    {"region": "europe-west3",       "display": "Europe West 3 (Frankfurt)", "lat": 50.1109, "lon": 8.6821, "country": "DE"},
    {"region": "europe-north1",      "display": "Europe North (Finland)",  "lat": 60.5693, "lon": 27.1878, "country": "FI"},
    {"region": "asia-east1",         "display": "Asia East (Taiwan)",      "lat": 24.0717, "lon": 120.5624, "country": "TW"},
    {"region": "asia-northeast1",    "display": "Asia NE (Tokyo)",         "lat": 35.6762, "lon": 139.6503, "country": "JP"},
    {"region": "asia-south1",        "display": "Asia South (Mumbai)",     "lat": 19.0760, "lon": 72.8777, "country": "IN"},
    {"region": "australia-southeast1", "display": "Australia SE (Sydney)", "lat": -33.8688, "lon": 151.2093, "country": "AU"},
    {"region": "southamerica-east1", "display": "S. America East (Sao Paulo)", "lat": -23.5505, "lon": -46.6333, "country": "BR"},
    {"region": "me-west1",           "display": "Middle East (Tel Aviv)",  "lat": 32.0853, "lon": 34.7818, "country": "IL"},
]

AWS_REGIONS = [
    {"region": "us-east-1",          "display": "US East (N. Virginia)",   "lat": 38.9072, "lon": -77.0369, "country": "US"},
    {"region": "us-east-2",          "display": "US East (Ohio)",          "lat": 39.9612, "lon": -82.9988, "country": "US"},
    {"region": "us-west-2",          "display": "US West (Oregon)",        "lat": 45.5152, "lon": -122.6784, "country": "US"},
    {"region": "eu-west-1",          "display": "Europe (Ireland)",        "lat": 53.3498, "lon": -6.2603, "country": "IE"},
    {"region": "eu-central-1",       "display": "Europe (Frankfurt)",      "lat": 50.1109, "lon": 8.6821, "country": "DE"},
    {"region": "eu-west-2",          "display": "Europe (London)",         "lat": 51.5074, "lon": -0.1278, "country": "GB"},
    {"region": "ap-south-1",         "display": "Asia Pacific (Mumbai)",   "lat": 19.0760, "lon": 72.8777, "country": "IN"},
    {"region": "ap-southeast-1",     "display": "Asia Pacific (Singapore)","lat": 1.3521,  "lon": 103.8198, "country": "SG"},
    {"region": "ap-northeast-1",     "display": "Asia Pacific (Tokyo)",    "lat": 35.6762, "lon": 139.6503, "country": "JP"},
    {"region": "ap-southeast-2",     "display": "Asia Pacific (Sydney)",   "lat": -33.8688,"lon": 151.2093, "country": "AU"},
    {"region": "sa-east-1",          "display": "South America (Sao Paulo)","lat": -23.5505,"lon": -46.6333, "country": "BR"},
    {"region": "ca-central-1",       "display": "Canada (Central)",        "lat": 45.4215, "lon": -75.6972, "country": "CA"},
]

# ─── Instance Templates ──────────────────────────────────────────

INSTANCE_ROLES = [
    {"role": "web-server",     "service": "nginx",     "tier": "frontend"},
    {"role": "app-server",     "service": "tomcat",     "tier": "application"},
    {"role": "api-gateway",    "service": "envoy",      "tier": "edge"},
    {"role": "db-primary",     "service": "postgresql",  "tier": "database"},
    {"role": "db-replica",     "service": "postgresql",  "tier": "database"},
    {"role": "cache-node",     "service": "redis",       "tier": "cache"},
    {"role": "worker-node",    "service": "celery",      "tier": "compute"},
    {"role": "k8s-node",       "service": "kubelet",     "tier": "orchestration"},
    {"role": "monitoring",     "service": "prometheus",  "tier": "observability"},
    {"role": "log-collector",  "service": "fluentd",     "tier": "observability"},
]


def ts(offset_minutes=0, base_time=None):
    """Generate ISO8601 timestamp with optional offset from a base time."""
    if base_time is None:
        base_time = BASE_TIME
    t = base_time + timedelta(minutes=offset_minutes, seconds=random.randint(0, 59))
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_instance_id(cloud, region_info):
    """Generate a cloud-provider-appropriate instance ID."""
    hex8 = uuid.uuid4().hex[:8]
    if cloud == "OCI":
        return f"ocid1.instance.oc1.{region_info['region']}.{uuid.uuid4().hex[:40]}"
    if cloud == "Azure":
        return f"/subscriptions/{uuid.uuid4().hex[:8]}-xxxx/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-{hex8}"
    if cloud == "AWS":
        return f"i-{uuid.uuid4().hex[:17]}"
    # GCP
    if region_info["region"].count("-") == 2:
        zone = f"{region_info['region']}-a"
    else:
        zone = region_info["region"]
    return f"projects/prod-project/zones/{zone}/instances/vm-{hex8}"


def generate_private_ip():
    """Generate a random RFC1918 private IP."""
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def generate_health_metrics(status):
    """Generate realistic health metrics based on instance status."""
    if status == "healthy":
        return {
            "cpu_pct": round(random.uniform(5.0, 65.0), 1),
            "memory_pct": round(random.uniform(20.0, 75.0), 1),
            "disk_pct": round(random.uniform(15.0, 70.0), 1),
            "network_in_mbps": round(random.uniform(0.5, 100.0), 2),
            "network_out_mbps": round(random.uniform(0.1, 50.0), 2),
            "uptime_hours": random.randint(24, 8760),
            "open_connections": random.randint(10, 500),
            "response_time_ms": random.randint(1, 50),
        }
    elif status == "degraded":
        return {
            "cpu_pct": round(random.uniform(80.0, 95.0), 1),
            "memory_pct": round(random.uniform(85.0, 98.0), 1),
            "disk_pct": round(random.uniform(75.0, 92.0), 1),
            "network_in_mbps": round(random.uniform(0.1, 10.0), 2),
            "network_out_mbps": round(random.uniform(0.05, 5.0), 2),
            "uptime_hours": random.randint(1, 48),
            "open_connections": random.randint(800, 2000),
            "response_time_ms": random.randint(200, 2000),
        }
    else:  # unreachable
        return {
            "cpu_pct": 0.0,
            "memory_pct": 0.0,
            "disk_pct": 0.0,
            "network_in_mbps": 0.0,
            "network_out_mbps": 0.0,
            "uptime_hours": 0,
            "open_connections": 0,
            "response_time_ms": -1,
        }


def build_instance_fleet():
    """Build a deterministic fleet of instances across all clouds/regions.

    Returns a list of instance dicts, each with cloud, region, role, and IDs.
    Assigns 2-3 instances per region to create a realistic multi-region fleet.
    """
    fleet = []
    instance_idx = 0

    for cloud, regions in [
        ("OCI", OCI_REGIONS),
        ("Azure", AZURE_REGIONS),
        ("AWS", AWS_REGIONS),
        ("GCP", GCP_REGIONS),
    ]:
        for region_info in regions:
            # 2-3 instances per region
            n_instances = random.choice([2, 2, 3])
            for _ in range(n_instances):
                role_info = INSTANCE_ROLES[instance_idx % len(INSTANCE_ROLES)]
                hostname = f"{role_info['role']}-{region_info['region'].split('-')[0]}-{instance_idx:03d}"
                fleet.append({
                    "cloud_provider": cloud,
                    "region": region_info["region"],
                    "region_display": region_info["display"],
                    "country": region_info["country"],
                    "latitude": region_info["lat"],
                    "longitude": region_info["lon"],
                    "instance_id": generate_instance_id(cloud, region_info),
                    "hostname": hostname,
                    "private_ip": generate_private_ip(),
                    "role": role_info["role"],
                    "service": role_info["service"],
                    "tier": role_info["tier"],
                    "os": random.choice(["Oracle Linux 8", "Oracle Linux 9", "Ubuntu 22.04", "RHEL 9"]) if cloud != "Azure"
                           else random.choice(["Windows Server 2022", "Ubuntu 22.04", "RHEL 9"]),
                    "instance_type": {
                        "OCI": random.choice(["VM.Standard.E4.Flex", "VM.Standard3.Flex", "VM.Standard.A1.Flex", "BM.Standard3.64"]),
                        "Azure": random.choice(["Standard_D4s_v5", "Standard_E4s_v5", "Standard_B2ms", "Standard_F4s_v2"]),
                        "AWS": random.choice(["m6i.xlarge", "c6i.xlarge", "r6i.xlarge", "t3.large"]),
                        "GCP": random.choice(["e2-standard-4", "n2-standard-4", "c2-standard-4", "t2a-standard-4"]),
                    }[cloud],
                })
                instance_idx += 1

    return fleet


def generate_heartbeat(instance, offset_minutes, status="healthy", base_time=None):
    """Generate a single health heartbeat log event."""
    metrics = generate_health_metrics(status)

    return {
        "Timestamp": ts(offset_minutes, base_time=base_time),
        "Cloud Provider": instance["cloud_provider"],
        "Region": instance["region"],
        "Region Display": instance["region_display"],
        "Country": instance["country"],
        "Latitude": instance["latitude"],
        "Longitude": instance["longitude"],
        "Instance ID": instance["instance_id"],
        "Host Name": instance["hostname"],
        "IP Address": instance["private_ip"],
        "Instance Role": instance["role"],
        "Service": instance["service"],
        "Tier": instance["tier"],
        "Operating System": instance["os"],
        "Instance Type": instance["instance_type"],
        "Status": status,
        "Status Code": {"healthy": 200, "degraded": 503, "unreachable": 0}[status],
        "CPU Percent": metrics["cpu_pct"],
        "Memory Percent": metrics["memory_pct"],
        "Disk Percent": metrics["disk_pct"],
        "Network In Mbps": metrics["network_in_mbps"],
        "Network Out Mbps": metrics["network_out_mbps"],
        "Uptime Hours": metrics["uptime_hours"],
        "Open Connections": metrics["open_connections"],
        "Response Time Ms": metrics["response_time_ms"],
        "Heartbeat Sequence": 0,  # set by caller
        "Log Source": "SOC Multicloud Health Logs",
        "msg": "",  # set by caller
    }


def generate_all_heartbeats(interval_minutes=5, duration_minutes=60,
                             unhealthy_pct=5, degraded_pct=8):
    """Generate heartbeat logs for entire fleet over a time window.

    Args:
        interval_minutes: Time between heartbeats per instance.
        duration_minutes: Total time window to cover.
        unhealthy_pct: Percentage of heartbeats that should be 'unreachable'.
        degraded_pct: Percentage of heartbeats that should be 'degraded'.
    """
    random.seed(42)  # Reproducible output
    fleet = build_instance_fleet()
    events = []
    n_beats = duration_minutes // interval_minutes
    window_start = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)

    # Pre-select a few instances that will have issues (persistent, not random)
    n_degraded_instances = max(1, int(len(fleet) * degraded_pct / 100))
    n_unhealthy_instances = max(1, int(len(fleet) * unhealthy_pct / 100))

    degraded_instances = set(random.sample(range(len(fleet)), n_degraded_instances))
    remaining = [i for i in range(len(fleet)) if i not in degraded_instances]
    unhealthy_instances = set(random.sample(remaining, min(n_unhealthy_instances, len(remaining))))

    for beat_idx in range(n_beats):
        offset = beat_idx * interval_minutes
        for inst_idx, instance in enumerate(fleet):
            if inst_idx in unhealthy_instances:
                status = "unreachable"
            elif inst_idx in degraded_instances:
                status = "degraded"
            else:
                status = "healthy"

            event = generate_heartbeat(instance, offset, status, base_time=window_start)
            event["Heartbeat Sequence"] = beat_idx + 1

            # Human-readable message
            if status == "healthy":
                event["msg"] = (
                    f"HEARTBEAT OK: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
                    f"cpu={event['CPU Percent']}% mem={event['Memory Percent']}% "
                    f"uptime={event['Uptime Hours']}h status=healthy"
                )
            elif status == "degraded":
                event["msg"] = (
                    f"HEARTBEAT WARN: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
                    f"cpu={event['CPU Percent']}% mem={event['Memory Percent']}% "
                    f"response_time={event['Response Time Ms']}ms status=degraded"
                )
            else:
                event["msg"] = (
                    f"HEARTBEAT FAIL: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
                    f"status=unreachable — no response from agent"
                )

            events.append(event)

    return events, fleet


def write_output(events, fleet):
    """Write events to JSONL and print summary."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / 'multicloud_health.jsonl'

    with open(output_file, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')

    manifest = rebuild_manifest(OUTPUT_DIR)

    # Summary stats
    cloud_counts = {}
    region_counts = {}
    status_counts = {"healthy": 0, "degraded": 0, "unreachable": 0}
    for e in events:
        cloud_counts[e["Cloud Provider"]] = cloud_counts.get(e["Cloud Provider"], 0) + 1
        region_counts[e["Region"]] = region_counts.get(e["Region"], 0) + 1
        status_counts[e["Status"]] = status_counts.get(e["Status"], 0) + 1

    print(f"\n{'═' * 65}")
    print(f"  Multicloud Geographic Health Log Generator")
    print(f"{'═' * 65}")
    print(f"  Output:     {output_file}")
    print(f"  Events:     {len(events):,}")
    print(f"  Manifest:   {OUTPUT_DIR / 'manifest.json'} ({manifest['total_events']:,} total events)")
    print(f"  Instances:  {len(fleet)}")
    print(f"  Regions:    {len(region_counts)}")
    print(f"{'─' * 65}")
    print(f"  Cloud Distribution:")
    for cloud, count in sorted(cloud_counts.items()):
        n_instances = len([i for i in fleet if i['cloud_provider'] == cloud])
        n_regions = len(set(i['region'] for i in fleet if i['cloud_provider'] == cloud))
        print(f"    {cloud:8s}  {count:5,} events  ({n_instances} instances, {n_regions} regions)")
    print(f"{'─' * 65}")
    print(f"  Health Status:")
    for status, count in status_counts.items():
        pct = count / len(events) * 100
        indicator = {"healthy": "OK", "degraded": "WARN", "unreachable": "FAIL"}[status]
        print(f"    [{indicator:4s}]  {status:12s}  {count:5,} ({pct:.1f}%)")
    print(f"{'═' * 65}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate multicloud health heartbeat logs for geographic visualization."
    )
    parser.add_argument("--interval", type=int, default=5,
                        help="Minutes between heartbeats (default: 5)")
    parser.add_argument("--duration", type=int, default=60,
                        help="Total duration in minutes (default: 60)")
    parser.add_argument("--unhealthy-pct", type=int, default=5,
                        help="Percentage of instances marked unreachable (default: 5)")
    parser.add_argument("--degraded-pct", type=int, default=8,
                        help="Percentage of instances marked degraded (default: 8)")
    args = parser.parse_args()

    events, fleet = generate_all_heartbeats(
        interval_minutes=args.interval,
        duration_minutes=args.duration,
        unhealthy_pct=args.unhealthy_pct,
        degraded_pct=args.degraded_pct,
    )

    write_output(events, fleet)


if __name__ == "__main__":
    main()
