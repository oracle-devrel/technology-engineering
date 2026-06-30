"""
Continuous multicloud health heartbeat streamer for OCI Log Analytics.

Two-phase operation:
  Phase 1 — BACKFILL: Upload historical heartbeats (default: 5 days) via the
            Log Analytics Upload API in batched JSONL files.
  Phase 2 — LIVE:     Stream real-time heartbeats at a regular interval
            (default: 5 min) for a configurable duration (default: 5 hours)
            via OCI Streaming → Service Connector Hub → Log Analytics.

The backfill phase uses direct upload (faster for bulk data), while the live
phase uses OCI Streaming for real-time ingestion.

Prerequisites:
  1. OCI CLI configured (~/.oci/config)
  2. Log Analytics service enabled
  3. (Live phase) Run setup_streaming_pipeline.py to create the stream

Usage:
  # Full run: 5 days backfill + 5 hours live streaming
  python3 scripts/stream_geo_health.py

  # Backfill only (no live streaming)
  python3 scripts/stream_geo_health.py --backfill-only

  # Live only (no backfill)
  python3 scripts/stream_geo_health.py --live-only

  # Custom durations
  python3 scripts/stream_geo_health.py --backfill-days 3 --live-hours 2

  # Direct upload mode (no OCI Streaming required)
  python3 scripts/stream_geo_health.py --mode direct
"""

import argparse
import base64
import io
import json
import os
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    COMPARTMENT_ID, PROJECT_DIR, TEST_DATA_DIR,
    get_oci_config, get_la_client, get_namespace, ensure_log_group,
    require_oci_config,
    SOURCE_CANDIDATE_GROUPS,
    list_available_log_sources,
    resolve_source_from_candidates,
)

# Reuse fleet/region definitions from the batch generator
from generate_geo_health_logs import (
    OCI_REGIONS, AZURE_REGIONS, GCP_REGIONS, INSTANCE_ROLES,
    generate_instance_id, generate_private_ip, generate_health_metrics,
)

STREAMING_CONFIG_PATH = os.path.join(PROJECT_DIR, 'config', 'streaming_config.json')
LOG_SOURCE_NAME = "SOC Multicloud Health Logs"
UPLOAD_NAME_PREFIX = "soc-health-backfill"

# Graceful shutdown flag
_shutdown = False


def _signal_handler(sig, frame):
    global _shutdown
    print("\n\n  Received shutdown signal — finishing current batch...")
    _shutdown = True


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ═══════════════════════════════════════════════════════════════════
#  Fleet Builder (deterministic — same fleet across backfill + live)
# ═══════════════════════════════════════════════════════════════════

def build_fleet(seed=42):
    """Build a deterministic fleet consistent with generate_geo_health_logs.py."""
    random.seed(seed)
    fleet = []
    idx = 0
    for cloud, regions in [("OCI", OCI_REGIONS), ("Azure", AZURE_REGIONS), ("GCP", GCP_REGIONS)]:
        for region_info in regions:
            n = random.choice([2, 2, 3])
            for _ in range(n):
                role = INSTANCE_ROLES[idx % len(INSTANCE_ROLES)]
                hostname = f"{role['role']}-{region_info['region'].split('-')[0]}-{idx:03d}"
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
                    "role": role["role"],
                    "service": role["service"],
                    "tier": role["tier"],
                    "os": (random.choice(["Oracle Linux 8", "Oracle Linux 9", "Ubuntu 22.04", "RHEL 9"])
                           if cloud != "Azure"
                           else random.choice(["Windows Server 2022", "Ubuntu 22.04", "RHEL 9"])),
                    "instance_type": {
                        "OCI": random.choice(["VM.Standard.E4.Flex", "VM.Standard3.Flex",
                                              "VM.Standard.A1.Flex", "BM.Standard3.64"]),
                        "Azure": random.choice(["Standard_D4s_v5", "Standard_E4s_v5",
                                                "Standard_B2ms", "Standard_F4s_v2"]),
                        "GCP": random.choice(["e2-standard-4", "n2-standard-4",
                                              "c2-standard-4", "t2a-standard-4"]),
                    }[cloud],
                })
                idx += 1
    return fleet


def select_problem_instances(fleet, degraded_pct=8, unhealthy_pct=5, seed=42):
    """Select which instances will have persistent issues.

    Returns (degraded_set, unhealthy_set) of fleet indices.
    Some instances will have intermittent issues (flip between healthy/degraded).
    """
    random.seed(seed + 100)
    n_degraded = max(1, int(len(fleet) * degraded_pct / 100))
    n_unhealthy = max(1, int(len(fleet) * unhealthy_pct / 100))

    degraded = set(random.sample(range(len(fleet)), n_degraded))
    remaining = [i for i in range(len(fleet)) if i not in degraded]
    unhealthy = set(random.sample(remaining, min(n_unhealthy, len(remaining))))

    return degraded, unhealthy


def make_heartbeat(instance, timestamp, status):
    """Build a single heartbeat event dict."""
    metrics = generate_health_metrics(status)

    if status == "healthy":
        msg = (f"HEARTBEAT OK: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
               f"cpu={metrics['cpu_pct']}% mem={metrics['memory_pct']}% "
               f"uptime={metrics['uptime_hours']}h status=healthy")
    elif status == "degraded":
        msg = (f"HEARTBEAT WARN: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
               f"cpu={metrics['cpu_pct']}% mem={metrics['memory_pct']}% "
               f"response_time={metrics['response_time_ms']}ms status=degraded")
    else:
        msg = (f"HEARTBEAT FAIL: {instance['hostname']} ({instance['cloud_provider']}/{instance['region']}) "
               f"status=unreachable — no response from agent")

    return {
        "Timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
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
        "Heartbeat Sequence": 0,
        "Log Source": LOG_SOURCE_NAME,
        "msg": msg,
    }


def get_instance_status(inst_idx, degraded_set, unhealthy_set, beat_number):
    """Determine instance status with occasional flapping for realism.

    Unhealthy instances stay unreachable. Degraded instances occasionally
    recover (10% of beats) then degrade again, simulating flapping.
    """
    if inst_idx in unhealthy_set:
        return "unreachable"
    if inst_idx in degraded_set:
        # 10% chance of temporary recovery per beat
        if random.random() < 0.10:
            return "healthy"
        return "degraded"
    # Healthy instances have 1% chance of brief degradation
    if random.random() < 0.01:
        return "degraded"
    return "healthy"


# ═══════════════════════════════════════════════════════════════════
#  Phase 1: Backfill via Direct Upload
# ═══════════════════════════════════════════════════════════════════

def run_backfill(la_client, namespace, log_group_id, resolved_source,
                 fleet, degraded_set, unhealthy_set,
                 backfill_days=5, interval_minutes=5):
    """Generate and upload historical heartbeats in daily batches."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=backfill_days)
    beats_per_day = (24 * 60) // interval_minutes  # 288 at 5-min interval
    total_events = beats_per_day * len(fleet) * backfill_days

    print(f"\n{'═' * 65}")
    print(f"  Phase 1: BACKFILL — {backfill_days} days of historical heartbeats")
    print(f"{'═' * 65}")
    print(f"  Period:     {start.strftime('%Y-%m-%d %H:%M')} → {now.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"  Interval:   {interval_minutes} min")
    print(f"  Fleet:      {len(fleet)} instances")
    print(f"  Events:     ~{total_events:,} ({beats_per_day} beats/day × {len(fleet)} instances × {backfill_days} days)")
    print(f"  Log Source: {resolved_source}")
    print(f"{'─' * 65}")

    uploaded_total = 0
    seq = 0

    for day_offset in range(backfill_days):
        if _shutdown:
            break

        day_start = start + timedelta(days=day_offset)
        day_label = day_start.strftime("%Y-%m-%d")
        events = []

        for beat_idx in range(beats_per_day):
            ts = day_start + timedelta(minutes=beat_idx * interval_minutes,
                                       seconds=random.randint(0, 30))
            seq += 1
            for inst_idx, inst in enumerate(fleet):
                status = get_instance_status(inst_idx, degraded_set, unhealthy_set, seq)
                event = make_heartbeat(inst, ts, status)
                event["Heartbeat Sequence"] = seq
                events.append(json.dumps(event))

        # Upload this day as a single batch
        body = "\n".join(events)
        file_body = io.BytesIO(body.encode("utf-8"))
        upload_name = f"{UPLOAD_NAME_PREFIX}-{day_label}"

        try:
            import oci
            response = la_client.upload_log_file(
                namespace_name=namespace,
                upload_name=upload_name,
                log_source_name=resolved_source,
                filename=f"health_backfill_{day_label}.jsonl",
                opc_meta_loggrpid=log_group_id,
                upload_log_file_body=file_body,
                content_type="application/octet-stream",
                char_encoding="UTF-8",
            )
            n = len(events)
            uploaded_total += n
            print(f"  [{day_label}]  {n:,} events uploaded  (HTTP {response.status})  "
                  f"cumulative: {uploaded_total:,}")
        except Exception as e:
            print(f"  [{day_label}]  FAILED: {e}")

    print(f"{'─' * 65}")
    print(f"  Backfill complete: {uploaded_total:,} events uploaded")
    return uploaded_total


# ═══════════════════════════════════════════════════════════════════
#  Phase 2: Live Streaming via OCI Streaming
# ═══════════════════════════════════════════════════════════════════

def stream_one_beat(stream_client, stream_id, fleet, degraded_set, unhealthy_set,
                     beat_number):
    """Generate and publish one heartbeat round for all instances."""
    import oci as oci_sdk
    now = datetime.now(timezone.utc)
    messages = []

    for inst_idx, inst in enumerate(fleet):
        status = get_instance_status(inst_idx, degraded_set, unhealthy_set, beat_number)
        event = make_heartbeat(inst, now, status)
        event["Heartbeat Sequence"] = beat_number
        payload = json.dumps(event)
        messages.append(oci_sdk.streaming.models.PutMessagesDetailsEntry(
            key=base64.b64encode(f"health-{inst['hostname']}-{beat_number}".encode()).decode(),
            value=base64.b64encode(payload.encode("utf-8")).decode(),
        ))

    # Publish in batches of 50
    published = 0
    failed = 0
    for i in range(0, len(messages), 50):
        batch = messages[i:i + 50]
        details = oci_sdk.streaming.models.PutMessagesDetails(messages=batch)
        try:
            resp = stream_client.put_messages(stream_id, details)
            f = resp.data.failures or 0
            published += len(batch) - f
            failed += f
        except Exception as e:
            print(f"    Stream error: {e}")
            failed += len(batch)

    return published, failed


def stream_one_beat_direct(la_client, namespace, log_group_id, resolved_source,
                            fleet, degraded_set, unhealthy_set, beat_number):
    """Generate and upload one heartbeat round via direct upload (fallback)."""
    now = datetime.now(timezone.utc)
    events = []

    for inst_idx, inst in enumerate(fleet):
        status = get_instance_status(inst_idx, degraded_set, unhealthy_set, beat_number)
        event = make_heartbeat(inst, now, status)
        event["Heartbeat Sequence"] = beat_number
        events.append(json.dumps(event))

    body = "\n".join(events)
    file_body = io.BytesIO(body.encode("utf-8"))
    upload_name = f"soc-health-live-{now.strftime('%Y%m%d-%H%M%S')}"

    try:
        la_client.upload_log_file(
            namespace_name=namespace,
            upload_name=upload_name,
            log_source_name=resolved_source,
            filename=f"health_live_{now.strftime('%Y%m%dT%H%M%S')}.jsonl",
            opc_meta_loggrpid=log_group_id,
            upload_log_file_body=file_body,
            content_type="application/octet-stream",
            char_encoding="UTF-8",
        )
        return len(events), 0
    except Exception as e:
        print(f"    Upload error: {e}")
        return 0, len(events)


def run_live(mode, fleet, degraded_set, unhealthy_set,
             live_hours=5, interval_minutes=5,
             la_client=None, namespace=None, log_group_id=None, resolved_source=None):
    """Stream live heartbeats for the configured duration."""
    total_beats = (live_hours * 60) // interval_minutes
    interval_sec = interval_minutes * 60

    print(f"\n{'═' * 65}")
    print(f"  Phase 2: LIVE STREAMING — {live_hours}h of real-time heartbeats")
    print(f"{'═' * 65}")
    print(f"  Mode:       {mode}")
    print(f"  Interval:   {interval_minutes} min ({interval_sec}s)")
    print(f"  Beats:      {total_beats} ({live_hours}h ÷ {interval_minutes}min)")
    print(f"  Events/beat:{len(fleet)}")
    print(f"  Total:      ~{total_beats * len(fleet):,} events")
    print(f"  End time:   ~{(datetime.now(timezone.utc) + timedelta(hours=live_hours)).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'─' * 65}")
    print(f"  Press Ctrl+C to stop gracefully\n")

    # Set up streaming client if using streaming mode
    stream_client = None
    stream_id = None
    if mode == "streaming":
        import oci as oci_sdk
        if not os.path.exists(STREAMING_CONFIG_PATH):
            print(f"  WARN: {STREAMING_CONFIG_PATH} not found — falling back to direct upload")
            mode = "direct"
        else:
            with open(STREAMING_CONFIG_PATH) as f:
                scfg = json.load(f)
            stream_key = "soc-detection-multicloud-health"
            if stream_key in scfg:
                config = get_oci_config()
                stream_client = oci_sdk.streaming.StreamClient(
                    config, service_endpoint=scfg[stream_key]["messages_endpoint"]
                )
                stream_id = scfg[stream_key]["stream_id"]
                print(f"  Connected to stream: {stream_key}")
            else:
                print(f"  WARN: Stream '{stream_key}' not in config — falling back to direct upload")
                mode = "direct"

    total_published = 0
    total_failed = 0

    for beat in range(1, total_beats + 1):
        if _shutdown:
            break

        beat_start = time.time()
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

        if mode == "streaming" and stream_client:
            pub, fail = stream_one_beat(
                stream_client, stream_id, fleet, degraded_set, unhealthy_set, beat
            )
        else:
            pub, fail = stream_one_beat_direct(
                la_client, namespace, log_group_id, resolved_source,
                fleet, degraded_set, unhealthy_set, beat
            )

        total_published += pub
        total_failed += fail
        elapsed = time.time() - beat_start

        remaining = total_beats - beat
        eta_min = (remaining * interval_sec) / 60

        print(f"  [{now_str}]  Beat {beat:>4}/{total_beats}  "
              f"published={pub}  failed={fail}  "
              f"total={total_published:,}  "
              f"ETA={eta_min:.0f}min  ({elapsed:.1f}s)")

        # Sleep until next interval (minus processing time)
        if beat < total_beats and not _shutdown:
            sleep_time = max(0, interval_sec - elapsed)
            # Sleep in small increments to catch shutdown signal
            slept = 0
            while slept < sleep_time and not _shutdown:
                chunk = min(5, sleep_time - slept)
                time.sleep(chunk)
                slept += chunk

    print(f"\n{'─' * 65}")
    print(f"  Live streaming complete: {total_published:,} published, {total_failed:,} failed")
    return total_published


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Continuous multicloud health heartbeat streamer for OCI Log Analytics."
    )
    parser.add_argument("--mode", choices=["direct", "streaming"], default="direct",
                        help="Ingestion mode for live phase (default: direct)")
    parser.add_argument("--backfill-days", type=int, default=5,
                        help="Days of historical data to backfill (default: 5)")
    parser.add_argument("--live-hours", type=int, default=5,
                        help="Hours of live streaming (default: 5)")
    parser.add_argument("--interval", type=int, default=5,
                        help="Minutes between heartbeats (default: 5)")
    parser.add_argument("--backfill-only", action="store_true",
                        help="Only run backfill, skip live streaming")
    parser.add_argument("--live-only", action="store_true",
                        help="Only run live streaming, skip backfill")
    parser.add_argument("--unhealthy-pct", type=int, default=5,
                        help="Percentage of instances that are unreachable (default: 5)")
    parser.add_argument("--degraded-pct", type=int, default=8,
                        help="Percentage of instances that are degraded (default: 8)")
    args = parser.parse_args()

    require_oci_config()

    print(f"\n{'═' * 65}")
    print(f"  Multicloud Geographic Health — Continuous Streamer")
    print(f"{'═' * 65}")

    # Build fleet (deterministic)
    fleet = build_fleet()
    degraded_set, unhealthy_set = select_problem_instances(
        fleet, args.degraded_pct, args.unhealthy_pct
    )

    cloud_summary = {}
    for inst in fleet:
        cloud_summary[inst["cloud_provider"]] = cloud_summary.get(inst["cloud_provider"], 0) + 1
    print(f"  Fleet: {len(fleet)} instances — " +
          ", ".join(f"{c}: {n}" for c, n in sorted(cloud_summary.items())))
    print(f"  Status: {len(fleet) - len(degraded_set) - len(unhealthy_set)} healthy, "
          f"{len(degraded_set)} degraded, {len(unhealthy_set)} unreachable")

    # Connect to OCI
    print(f"\n  Connecting to OCI Log Analytics...")
    la_client = get_la_client()
    namespace = get_namespace(la_client)
    log_group_id = ensure_log_group(la_client, namespace)
    available = list_available_log_sources(la_client, namespace, COMPARTMENT_ID)
    resolved_source = resolve_source_from_candidates(
        available, SOURCE_CANDIDATE_GROUPS["multicloud_health"]
    ) or LOG_SOURCE_NAME
    print(f"  Namespace:  {namespace}")
    print(f"  Log Source: {resolved_source}")

    grand_total = 0

    # Phase 1: Backfill
    if not args.live_only:
        n = run_backfill(
            la_client, namespace, log_group_id, resolved_source,
            fleet, degraded_set, unhealthy_set,
            backfill_days=args.backfill_days,
            interval_minutes=args.interval,
        )
        grand_total += n

    # Phase 2: Live
    if not args.backfill_only and not _shutdown:
        n = run_live(
            mode=args.mode,
            fleet=fleet,
            degraded_set=degraded_set,
            unhealthy_set=unhealthy_set,
            live_hours=args.live_hours,
            interval_minutes=args.interval,
            la_client=la_client,
            namespace=namespace,
            log_group_id=log_group_id,
            resolved_source=resolved_source,
        )
        grand_total += n

    # Final summary
    print(f"\n{'═' * 65}")
    print(f"  DONE — {grand_total:,} total events ingested")
    print(f"{'═' * 65}\n")


if __name__ == "__main__":
    main()
