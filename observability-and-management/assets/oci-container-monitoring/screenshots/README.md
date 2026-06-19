# Screenshots Directory

This directory contains screenshots demonstrating the complete monitoring stack in action.

## Required Screenshot Files

Please add the following screenshot files to this directory:

1. **`grafana-metrics-explorer.png`** - Grafana Metrics Explorer showing container metrics
   - Should show: Container CPU/memory usage, network I/O, custom application metrics
   - Access: http://YOURIP:3000

2. **`application-webpage.png`** - Application webpage showing monitoring architecture
   - Should show: 7-container architecture overview, health status, component links
   - Access: http://YOURIP/

3. **`prometheus-targets.png`** - Prometheus targets health status page
   - Should show: cAdvisor (UP), Node Exporter (UP), Application metrics (UP)
   - Access: http://YOURIP:9090/targets

4. **`cadvisor-metrics.png`** - cAdvisor metrics output (raw Prometheus format)
   - Should show: container_cpu_usage_seconds_total, container_memory_usage_bytes, etc.
   - Access: http://YOURIP:8080/metrics

## File Format

- Format: PNG (preferred) or JPG
- Resolution: At least 1920x1080 for clarity
- File naming: Use lowercase with hyphens (as specified above)

## Adding Screenshots

1. Capture screenshots from the current deployment (IP: YOURIP)
2. Save files with the exact names specified above
3. Place them in this directory (`/screenshots/`)
4. The README.md will automatically reference these images

## Current Status

🟡 **Screenshots pending** - Please add the 4 screenshot files as specified above.
