#!/usr/bin/env python3
"""
OCI Metrics Report Generator - CLI Script

Generate HTML metric reports directly from the command line.
Designed for use in OCI CloudShell and automated environments.

Usage:
    # Basic usage with auto-detected authentication
    python generate_report.py -c <compartment_ocid> -n oci_computeagent -m CpuUtilization

    # Multiple metrics
    python generate_report.py -c <compartment_ocid> -n oci_computeagent \
        -m CpuUtilization -m MemoryUtilization -m NetworkBytesIn

    # With custom time range and MQL
    python generate_report.py -c <compartment_ocid> -n oci_computeagent \
        --mql "CpuUtilization[1h].groupBy(resourceId).mean()" --hours 168

    # CloudShell with instance principal
    python generate_report.py --auth instance_principal -c <compartment_ocid> \
        -n oci_computeagent -m CpuUtilization

Examples:
    # Generate report for compute metrics in the last 24 hours
    python generate_report.py -c ocid1.compartment.oc1..xxx -n oci_computeagent \
        -m CpuUtilization -m MemoryUtilization -o compute_report.html

    # Generate report using raw MQL
    python generate_report.py -c ocid1.compartment.oc1..xxx -n oci_computeagent \
        --mql "CpuUtilization[1h].groupBy(availabilityDomain).max()" -o cpu_by_ad.html
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import OCIMonitoringClient, AuthType, detect_auth_type


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate OCI Monitoring metrics report as HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authentication Methods:
  --auth config_file        Use OCI config file (default)
  --auth instance_principal Use instance principal (CloudShell, compute instances)
  --auth resource_principal Use resource principal (OCI Functions)
  --auth security_token     Use security token (CloudShell delegation)

Examples:
  # List available namespaces in a compartment
  python generate_report.py -c <compartment_id> --list-namespaces

  # List available metrics in a namespace
  python generate_report.py -c <compartment_id> -n oci_computeagent --list-metrics

  # Generate report with multiple metrics
  python generate_report.py -c <compartment_id> -n oci_computeagent \\
      -m CpuUtilization -m MemoryUtilization -o report.html

  # Use MQL query directly
  python generate_report.py -c <compartment_id> -n oci_computeagent \\
      --mql "CpuUtilization[1h].groupBy(resourceId).mean()" -o report.html
        """
    )

    # Authentication options
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument(
        '--auth', choices=['config_file', 'instance_principal', 'resource_principal', 'security_token'],
        default=None, help='Authentication method (auto-detected if not specified)'
    )
    auth_group.add_argument(
        '--config-file', default='~/.oci/config',
        help='OCI config file path (default: ~/.oci/config)'
    )
    auth_group.add_argument(
        '--profile', default='DEFAULT',
        help='OCI config profile (default: DEFAULT)'
    )
    auth_group.add_argument(
        '--region', help='OCI region (overrides config/auto-detection)'
    )

    # Query options
    query_group = parser.add_argument_group('Query Options')
    query_group.add_argument(
        '-c', '--compartment', required=True,
        help='Compartment OCID to query'
    )
    query_group.add_argument(
        '-n', '--namespace',
        help='Metric namespace (e.g., oci_computeagent)'
    )
    query_group.add_argument(
        '-m', '--metric', action='append', dest='metrics',
        help='Metric name(s) to include (can specify multiple)'
    )
    query_group.add_argument(
        '--mql', action='append', dest='mql_queries',
        help='Raw MQL query (can specify multiple)'
    )
    query_group.add_argument(
        '-i', '--interval', default='1h',
        choices=['1m', '5m', '15m', '1h', '6h', '1d'],
        help='Aggregation interval (default: 1h)'
    )
    query_group.add_argument(
        '-s', '--statistic', default='mean',
        choices=['mean', 'max', 'min', 'sum', 'count', 'rate', 'p50', 'p90', 'p95', 'p99'],
        help='Aggregation statistic (default: mean)'
    )
    query_group.add_argument(
        '-g', '--group-by',
        help='Dimension to group by (e.g., resourceId, availabilityDomain)'
    )
    query_group.add_argument(
        '--resource-group',
        help='Filter by resource group'
    )

    # Time range options
    time_group = parser.add_argument_group('Time Range')
    time_group.add_argument(
        '--hours', type=int, default=24,
        help='Hours of data to fetch (default: 24)'
    )
    time_group.add_argument(
        '--start-time',
        help='Start time (ISO format, e.g., 2024-01-01T00:00:00Z)'
    )
    time_group.add_argument(
        '--end-time',
        help='End time (ISO format, e.g., 2024-01-02T00:00:00Z)'
    )

    # Output options
    output_group = parser.add_argument_group('Output')
    output_group.add_argument(
        '-o', '--output', default='oci_metrics_report.html',
        help='Output HTML file path (default: oci_metrics_report.html)'
    )
    output_group.add_argument(
        '--title', default='OCI Metrics Report',
        help='Report title'
    )
    output_group.add_argument(
        '--json', action='store_true',
        help='Output raw JSON instead of HTML'
    )

    # Discovery options
    discovery_group = parser.add_argument_group('Discovery')
    discovery_group.add_argument(
        '--list-namespaces', action='store_true',
        help='List available metric namespaces and exit'
    )
    discovery_group.add_argument(
        '--list-metrics', action='store_true',
        help='List available metrics in namespace and exit'
    )
    discovery_group.add_argument(
        '--list-compartments', action='store_true',
        help='List available compartments and exit'
    )

    return parser.parse_args()


def get_auth_type(auth_str: Optional[str]) -> Optional[AuthType]:
    """Convert auth string to AuthType enum."""
    if auth_str is None:
        return None
    mapping = {
        'config_file': AuthType.CONFIG_FILE,
        'instance_principal': AuthType.INSTANCE_PRINCIPAL,
        'resource_principal': AuthType.RESOURCE_PRINCIPAL,
        'security_token': AuthType.SECURITY_TOKEN
    }
    return mapping.get(auth_str)


def build_mql(metric: str, interval: str, statistic: str,
              group_by: Optional[str] = None,
              resource_group: Optional[str] = None) -> str:
    """Build MQL query from components."""
    # Handle percentile statistics
    stat_map = {
        'p50': 'percentile(0.5)',
        'p90': 'percentile(0.9)',
        'p95': 'percentile(0.95)',
        'p99': 'percentile(0.99)'
    }
    stat = stat_map.get(statistic, statistic)

    mql = f"{metric}[{interval}]"

    if resource_group:
        mql += f'{{resourceGroup="{resource_group}"}}'

    if group_by:
        mql += f".groupBy({group_by})"

    mql += f".{stat}()"

    return mql


def generate_html_report(results: List[Dict], title: str, args) -> str:
    """Generate HTML report from query results."""
    # Prepare chart data
    charts_data = []
    for idx, result in enumerate(results):
        chart_id = f"chart_{idx}"
        datasets = []

        for series_idx, series in enumerate(result.get('metric_data', [])):
            data_points = [
                {"x": dp['timestamp'], "y": dp['value']}
                for dp in series.get('data_points', [])
            ]
            datasets.append({
                "label": series.get('label', f"Series {series_idx}"),
                "data": data_points,
                "borderColor": get_color(series_idx),
                "backgroundColor": get_color(series_idx, 0.1),
                "fill": False,
                "tension": 0.1
            })

        charts_data.append({
            "id": chart_id,
            "query": result.get('query', 'Unknown'),
            "namespace": result.get('namespace', ''),
            "datasets": datasets
        })

    charts_json = json.dumps(charts_data, default=str)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, #312D2A 0%, #4a4541 100%);
            color: white;
            padding: 30px 20px;
            margin-bottom: 30px;
        }}
        header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        header .meta {{ opacity: 0.8; font-size: 14px; }}
        header .meta span {{ margin-right: 20px; }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 24px;
            overflow: hidden;
        }}
        .card-header {{
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            background: #fafafa;
        }}
        .card-header h2 {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        .card-header .namespace {{
            font-size: 12px;
            color: #666;
            font-family: monospace;
        }}
        .card-body {{ padding: 20px; }}
        .chart-container {{ height: 300px; position: relative; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .summary-item .label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .summary-item .value {{ font-size: 24px; font-weight: 600; color: #312D2A; }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 16px;
        }}
        .data-table th, .data-table td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .data-table th {{ background: #f9f9f9; font-weight: 600; }}
        .data-table tr:hover {{ background: #f5f5f5; }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
        .toggle-table {{
            background: #f0f0f0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            margin-top: 10px;
        }}
        .toggle-table:hover {{ background: #e0e0e0; }}
        .hidden {{ display: none; }}
        @media print {{
            header {{ background: #333 !important; -webkit-print-color-adjust: exact; }}
            .card {{ break-inside: avoid; }}
            .toggle-table {{ display: none; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <div class="meta">
                <span>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
                <span>Compartment: {args.compartment[:30]}...</span>
                <span>Time Range: {args.hours} hours</span>
            </div>
        </div>
    </header>

    <main class="container">
        <div class="summary">
            <div class="summary-item">
                <div class="label">Total Queries</div>
                <div class="value">{len(results)}</div>
            </div>
            <div class="summary-item">
                <div class="label">Time Range</div>
                <div class="value">{args.hours}h</div>
            </div>
            <div class="summary-item">
                <div class="label">Namespace</div>
                <div class="value">{args.namespace or 'Multiple'}</div>
            </div>
        </div>

        <div id="charts">
            <!-- Charts will be rendered here -->
        </div>
    </main>

    <footer>
        <p>Generated by OCI Metrics Report Generator</p>
    </footer>

    <script>
        const chartsData = {charts_json};
        const colors = [
            'rgb(49, 45, 42)', 'rgb(40, 167, 69)', 'rgb(220, 53, 69)',
            'rgb(255, 193, 7)', 'rgb(111, 66, 193)', 'rgb(23, 162, 184)',
            'rgb(253, 126, 20)', 'rgb(108, 117, 125)'
        ];

        function initCharts() {{
            const container = document.getElementById('charts');

            chartsData.forEach((chartData, idx) => {{
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="card-header">
                        <h2>${{chartData.query}}</h2>
                        <div class="namespace">${{chartData.namespace}}</div>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="${{chartData.id}}"></canvas>
                        </div>
                        <button class="toggle-table" onclick="toggleTable('table_${{idx}}')">
                            Show Data Table
                        </button>
                        <div id="table_${{idx}}" class="hidden">
                            ${{generateTable(chartData.datasets)}}
                        </div>
                    </div>
                `;
                container.appendChild(card);

                // Create chart
                const ctx = document.getElementById(chartData.id).getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{ datasets: chartData.datasets }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        plugins: {{
                            legend: {{ display: true, position: 'top' }}
                        }},
                        scales: {{
                            x: {{
                                type: 'time',
                                time: {{ displayFormats: {{ hour: 'MMM d, HH:mm', day: 'MMM d' }} }},
                                title: {{ display: true, text: 'Time (UTC)' }}
                            }},
                            y: {{
                                beginAtZero: true,
                                title: {{ display: true, text: 'Value' }}
                            }}
                        }}
                    }}
                }});
            }});
        }}

        function generateTable(datasets) {{
            if (!datasets.length || !datasets[0].data.length) return '<p>No data</p>';

            let html = '<table class="data-table"><thead><tr><th>Timestamp</th>';
            datasets.forEach(ds => {{ html += `<th>${{ds.label}}</th>`; }});
            html += '</tr></thead><tbody>';

            const timestamps = [...new Set(datasets.flatMap(ds => ds.data.map(d => d.x)))].sort();
            timestamps.forEach(ts => {{
                html += `<tr><td>${{new Date(ts).toLocaleString()}}</td>`;
                datasets.forEach(ds => {{
                    const point = ds.data.find(d => d.x === ts);
                    html += `<td>${{point ? point.y.toFixed(2) : '-'}}</td>`;
                }});
                html += '</tr>';
            }});

            html += '</tbody></table>';
            return html;
        }}

        function toggleTable(id) {{
            const el = document.getElementById(id);
            el.classList.toggle('hidden');
        }}

        initCharts();
    </script>
</body>
</html>'''

    return html


def get_color(index: int, alpha: float = 1.0) -> str:
    """Get color for chart series."""
    colors = [
        f"rgba(49, 45, 42, {alpha})",
        f"rgba(40, 167, 69, {alpha})",
        f"rgba(220, 53, 69, {alpha})",
        f"rgba(255, 193, 7, {alpha})",
        f"rgba(111, 66, 193, {alpha})",
        f"rgba(23, 162, 184, {alpha})",
        f"rgba(253, 126, 20, {alpha})",
        f"rgba(108, 117, 125, {alpha})"
    ]
    return colors[index % len(colors)]


def main():
    """Main entry point."""
    args = parse_args()

    # Initialize OCI client
    print(f"Initializing OCI client...")
    try:
        auth_type = get_auth_type(args.auth)
        client = OCIMonitoringClient(
            config_file=args.config_file,
            profile=args.profile,
            auth_type=auth_type,
            region=args.region
        )
        print(f"  Auth type: {client.auth_type.value}")
        print(f"  Region: {client.config.get('region', 'unknown')}")
        print(f"  Tenancy: {client.tenancy_id[:30]}...")
    except Exception as e:
        print(f"Error: Failed to initialize OCI client: {e}")
        sys.exit(1)

    # Handle discovery commands
    if args.list_compartments:
        print("\nAvailable Compartments:")
        print("-" * 60)
        compartments = client.list_compartments()
        for comp in compartments:
            print(f"  {comp['path']}")
            print(f"    OCID: {comp['id']}")
        sys.exit(0)

    if args.list_namespaces:
        print(f"\nMetric Namespaces in compartment:")
        print("-" * 60)
        namespaces = client.list_metric_namespaces(args.compartment)
        for ns in namespaces:
            print(f"  {ns}")
        sys.exit(0)

    if args.list_metrics:
        if not args.namespace:
            print("Error: --namespace is required for --list-metrics")
            sys.exit(1)
        print(f"\nMetrics in namespace '{args.namespace}':")
        print("-" * 60)
        metrics = client.list_metrics(args.compartment, args.namespace)
        for metric in metrics:
            dims = ", ".join(metric['dimensions']) if metric['dimensions'] else "none"
            print(f"  {metric['name']}")
            print(f"    Dimensions: {dims}")
        sys.exit(0)

    # Validate required arguments for report generation
    if not args.namespace and not args.mql_queries:
        print("Error: --namespace is required (unless using --mql)")
        sys.exit(1)

    if not args.metrics and not args.mql_queries:
        print("Error: At least one --metric or --mql is required")
        sys.exit(1)

    # Calculate time range
    if args.start_time and args.end_time:
        start_time = datetime.fromisoformat(args.start_time.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(args.end_time.replace('Z', '+00:00'))
    else:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=args.hours)

    print(f"\nTime range: {start_time.isoformat()} to {end_time.isoformat()}")

    # Build queries
    queries = []

    # Add MQL queries
    if args.mql_queries:
        for mql in args.mql_queries:
            queries.append({
                'namespace': args.namespace,
                'mql': mql
            })

    # Build queries from metric names
    if args.metrics:
        for metric in args.metrics:
            mql = build_mql(
                metric=metric,
                interval=args.interval,
                statistic=args.statistic,
                group_by=args.group_by,
                resource_group=args.resource_group
            )
            queries.append({
                'namespace': args.namespace,
                'mql': mql
            })

    # Execute queries
    results = []
    print(f"\nExecuting {len(queries)} queries...")

    for idx, query in enumerate(queries):
        print(f"  [{idx + 1}/{len(queries)}] {query['mql']}")
        try:
            result = client.query_metrics(
                compartment_id=args.compartment,
                namespace=query['namespace'],
                query=query['mql'],
                start_time=start_time,
                end_time=end_time
            )
            results.append(result)
            data_points = sum(len(s['data_points']) for s in result.get('metric_data', []))
            print(f"           -> {len(result.get('metric_data', []))} series, {data_points} data points")
        except Exception as e:
            print(f"           -> Error: {e}")
            results.append({
                'query': query['mql'],
                'namespace': query['namespace'],
                'error': str(e),
                'metric_data': []
            })

    # Generate output
    if args.json:
        output = json.dumps(results, indent=2, default=str)
        output_file = args.output.replace('.html', '.json') if args.output.endswith('.html') else args.output
    else:
        output = generate_html_report(results, args.title, args)
        output_file = args.output

    # Write output
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"\nReport generated: {output_file}")
    print(f"  Total queries: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if 'error' not in r)}")

    # Print file size
    file_size = os.path.getsize(output_file)
    if file_size > 1024 * 1024:
        print(f"  File size: {file_size / 1024 / 1024:.2f} MB")
    else:
        print(f"  File size: {file_size / 1024:.2f} KB")


if __name__ == '__main__':
    main()
