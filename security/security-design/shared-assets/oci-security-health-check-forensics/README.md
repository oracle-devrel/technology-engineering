# OCI Security Health Check Forensics Tool

Last updated: 11 June 2025

The OCI Security Health Check Forensics Tool (the tool) is designed to load and analyze data from Oracle Cloud Infrastructure (OCI) environments. This tool enables users to import CSV files containing OCI resource information (e.g., compute instances, users, compartments) and perform SQL queries on the data. This data is used to investigate configuration issues etc.

The tool can also digest audit events and cloud guard problems. These resources can be loaded with different snapshots from a certain date with a number of days prior to that date.

This data can be used to investiage anomalies.

## Features
- Automatic OCI data fetching using showoci integration
- **Audit events** and **Cloud Guard problems** fetching with parallel processing
- Advanced filtering capabilities for age-based and compartment analysis
- Interactive tenancy selection from combined OCI configuration files
- Load CSV files with OCI data from multiple tenancies
- Execute SQL queries on the loaded data using DuckDB backend. Stay tuned for autonomous DB support.
- Support for `SHOW TABLES` and `DESCRIBE table_name` commands
- Command history and help system
- Batch query execution from YAML files

The tool will be used for forensic purposes. Data can be collected by the customer and shipped to Oracle for forensic research. 

The tool is in development and the following is on the backlog: 
- Switch back-end DB for large data sets. ADB support.
- Customer documentation to extract data and ship to Oracle in a secure way

## Know Errors
- Error shown when a query results in an empty data frame when a filter is applied.

## Installation

Clone the repository:
```bash
git clone <repository-url>
cd healthcheck-forensic
```

Set up a Python virtual environment and install dependencies:
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `requirements.txt` file contains dependencies for DuckDB, pandas, OCI SDK, and other required libraries.

### OCI Configuration Files

The tool now supports split OCI configuration:

- **`~/.oci/config`**: Contains only the DEFAULT domain configuration
- **`qt_config`**: Contains additional tenancy configurations

The tool automatically combines these files when selecting tenancies. This separation allows you to keep your main OCI config clean while managing multiple tenancies in a separate file.

## Usage

### Running the Tool

To start the tool, use:
```bash
python healthcheck_forensic_tool.py
```
### Interactive Mode

The tool supports an interactive mode for running SQL queries dynamically. Available commands include:

#### Basic Commands
- `show tables`: Lists all loaded tables
- `describe <table_name>`: Displays columns and data types for a given table
- `history`: Shows command history
- `help [command]`: Shows help for commands
- `exit` or `quit`: Exits the application

#### Data Management
- `set tenancy`: Switch between different OCI tenancies
- `set queries [directory]`: Load queries from YAML files for batch execution
- `run queries`: Execute all loaded queries in sequence

#### Data Fetching
- `audit_events fetch <DD-MM-YYYY> <days>`: Fetch <days> of audit events prior to specified date. 
- `audit_events fetch`: Interactive loader for existing audit data
- `audit_events delete`: Delete audit events files and tables
- `cloudguard fetch <DD-MM-YYYY> <days>`: Fetch <days> of cloud guard problems prior to specified date. 
- `cloudguard fetch`: Interactive loader for existing Cloud Guard data
- `cloudguard delete`: Delete Cloud Guard files and tables

#### Filtering and Analysis
- `filter age <column> <older|younger> <days>`: Filter results by date age
- `filter compartment <subcommand>`: Analyze compartment structures
  - `root`: Show root compartment
  - `depth`: Show maximum depth
  - `tree_view`: Display compartment tree
  - `path_to <compartment>`: Show path to specific compartment

### Command-line Switches

| Switch            | Description                                       |
|------------------|---------------------------------------------------|
| `--config-file`  | Path to the configuration file (`config.yaml`).  |
| `--interactive`  | Enable interactive SQL mode. <Default>              |

Example usage:
```bash
python healthcheck_forensic_tool.py
```

## Configuration Options (`config.yaml`)

| Setting                    | Description |
|----------------------------|-------------|
| `oci_config_file`          | Path to the main OCI config file (default: `~/.oci/config`) |
| `tqt_config_file`          | Path to the additional tenancies config file (default: `config/qt_config`) |
| `csv_dir`                  | Directory for CSV files |
| `prefix`                   | Filename prefix for filtering CSVs |
| `resource_argument`        | Resource argument for showoci (a: all, i: identity, n: network, c: compute, etc.) |
| `delimiter`                | Delimiter used in CSV files |
| `case_insensitive_headers` | Convert column headers to lowercase |
| `log_level`                | Logging level (`INFO`, `DEBUG`, `ERROR`) |
| `interactive`              | Enable interactive mode |
| `audit_worker_count`       | Number of parallel workers for audit/Cloud Guard fetching (default: 10) |
| `audit_worker_window`      | Hours per batch for parallel fetching (default: 1) |

### Example `config.yaml`
```yaml
# OCI Configuration
oci_config_file: "~/.oci/config"      # Main OCI config (DEFAULT domain)
tqt_config_file: "qt_config"   # Additional tenancies

# Data Management
csv_dir: "data"
prefix: "oci"
resource_argument: "a"

# Output Settings
output_format: "DataFrame"
log_level: "INFO"
delimiter: ","
case_insensitive_headers: true

# Interactive Mode
interactive: true

# Parallel Fetching Configuration
audit_worker_count: 10
audit_worker_window: 1
```

## Predefined Queries

Queries can be defined in YAML files for batch execution. Example `queries.yaml`:
```yaml
queries:
  - description: "List all users with API access"
    sql: "SELECT display_name, can_use_api_keys FROM identity_domains_users WHERE can_use_api_keys = 1"
  - description: "Show compute instances by compartment"
    sql: "SELECT server_name, compartment_name, status FROM compute WHERE status = 'STOPPED'"
    filter: "age last_modified older 30"
    sql: "sql: "SELECT server_name, compartment_name, status FROM compute WHERE compartment_name = '<YOUR COMPARTMENT_NAME>'"
```

## Example Usage Scenarios

### Getting Started
```bash
# Start the tool
python healthcheck_forensic_tool.py

# Select tenancy and load data
# Tool will prompt for tenancy selection from combined configs

# Basic exploration
CMD> show tables
CMD> describe identity_domains_users
CMD> SELECT COUNT(*) FROM compute;
```

### Data Fetching
```bash
# Fetch 2 days of audit events ending June 15, 2025
CMD> audit_events fetch 15-06-2025 2

# Fetch 30 days of Cloud Guard problems ending January 1, 2025
CMD> cloudguard fetch 01-01-2025 30

# Load existing audit data interactively
CMD> audit_events fetch
```

### Advanced Analysis
```bash
# Filter API keys older than 90 days
CMD> SELECT display_name, api_keys FROM identity_domains_users;
CMD> filter age api_keys older 90

# Analyze compartment structure
CMD> SELECT path FROM identity_compartments;
CMD> filter compartment tree_view
CMD> filter compartment path_to my-compartment
```

### Batch Operations
```bash
# Load and run predefined queries
CMD> set queries < Select a query file using the query file browser >
CMD> run queries

# Switch between tenancies
CMD> set tenancy
```

## Data Organization

The tool organizes data in the following structure:
```
data/
├── tenancy1/
│   ├── tenancy1_20241215_143022/
│   │   ├── oci_compute.csv
│   │   ├── oci_identity_domains_users.csv
│   │   ├── audit_events_15-06-2025_7.json
│   │   └── cloudguard_problems_15062025_7.json
│   └── tenancy1_20241214_091545/
└── tenancy2/
    └── tenancy2_20241215_100530/
```

## Logging

Logging is configured via the `log_level` setting in `config.yaml`. The tool provides detailed logging for:
- Configuration loading and validation
- CSV file loading and table creation
- Query execution and results
- Data fetching operations with progress tracking
- Error handling and troubleshooting information

## Troubleshooting

### Common Issues

**OCI Configuration Problems**
- Ensure both `~/.oci/config` and `config/qt_config` exist and are readable
- Verify that tenancy profiles are properly configured with required keys
- Check that API keys and permissions are correctly set up

**CSV Loading Issues**
- Ensure CSV files are properly formatted with consistent delimiters
- Column names in queries should match those in the loaded data (case-sensitive by default)
- Check that the specified prefix matches your CSV file naming convention

**Data Fetching Problems**
- Verify OCI permissions for audit events and Cloud Guard APIs
- Check network connectivity and OCI service availability
- Ensure the date range doesn't exceed OCI's retention periods (365 days for audit events)

**Query Execution**
- Use DuckDB-compatible SQL syntax
- Table names are derived from CSV filenames (minus prefix and extension)
- Check available tables with `show tables` and column structure with `describe <table>`

### Getting Help

For detailed command help:
```bash
CMD> help                        # Show all commands
CMD> help audit_events fetch     # Show audit_events fetch options
CMD> help filter age             # Show filter age options
```

## Advanced Features

### Parallel Data Fetching
The tool supports parallel fetching for large datasets:
- Configurable worker count and time windows
- Progress tracking with detailed summaries
- Automatic retry handling for failed intervals
- Clean temporary file management

### Smart Configuration Management
- Automatic detection and combination of split OCI configs
- Interactive tenancy selection with metadata display
- Temporary file creation for showoci integration
- Graceful handling of missing or invalid configurations

### Comprehensive Filtering
- Date-based filtering with flexible column support
- Compartment hierarchy analysis and visualization
- Support for complex nested data structures
- Chainable filter operations on query results

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.