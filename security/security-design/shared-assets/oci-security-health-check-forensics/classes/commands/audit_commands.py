"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

audit_commands.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from .base_command import Command
from datetime import datetime, timedelta
import os
import json
import glob
import questionary
import pandas as pd
from tqdm import tqdm
from ..audit_fetcher import AuditFetcher

class AuditEventsFetchCommand(Command):
    description = """Fetches OCI audit events or loads existing data.

USAGE:
  audit_events fetch <reference_date> <window_days>    # Fetch new data
  audit_events fetch                                   # Load existing data

FETCH NEW DATA:
  audit_events fetch 15-06-2025 7
    → Fetches audit events from June 8-15, 2025 (7 days ending on June 15)
  
  audit_events fetch 01-01-2025 30  
    → Fetches audit events from December 2-31, 2024 (30 days ending on Jan 1)

LOAD EXISTING DATA:
  audit_events fetch
    → Shows interactive file selector with details:
      - Event count and file size
      - Date range and creation time
      - Target DuckDB table name
    → Loads selected file into DuckDB for querying

WHAT FETCH DOES:
  ✓ Splits time window into parallel worker batches
  ✓ Fetches all audit events using OCI Audit API
  ✓ Shows clean progress bar with summary report
  ✓ Creates: audit_events_<date>_<days>.json  
  ✓ Loads into DuckDB table: audit_events_<date><days>
  ✓ Provides retry instructions for failed periods

CONFIGURATION:
  audit_worker_count: 10    # Parallel workers (config.yaml)
  audit_worker_window: 1    # Hours per batch (config.yaml)

NOTE: OCI audit logs have a 365-day retention period. The window cannot extend
beyond this limit from the current date."""

    def execute(self, args):
        parts = args.split()
        snapshot_dir = self.ctx.query_executor.current_snapshot_dir
        if not snapshot_dir:
            print("Error: No active tenancy snapshot. Use 'set tenancy' first.")
            return

        # Mode 2: Interactive load of existing audit_events JSON files
        if len(parts) == 0:
            self._interactive_load_existing_data(snapshot_dir)
            return

        # Mode 1: Fetch new audit events data
        if len(parts) != 2:
            print("Usage: audit_events fetch <reference_date> <window_days>")
            print("   or: audit_events fetch  (interactive mode)")
            return

        self._fetch_new_data(parts, snapshot_dir)

    def _interactive_load_existing_data(self, snapshot_dir):
        """Interactive mode to load existing audit events JSON files"""
        pattern = os.path.join(snapshot_dir, "audit_events_*_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No audit events JSON files found in {snapshot_dir}")
            print("Use 'audit_events fetch <date> <days>' to fetch new data first.")
            return

        # Analyze files and create rich choices
        file_choices = []
        for file_path in sorted(files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(file_path)
            file_info = self._analyze_file(file_path)
            
            choice_text = f"{filename}\n" \
                         f"  → {file_info['event_count']} events, {file_info['file_size']}, " \
                         f"Created: {file_info['created']}\n" \
                         f"  → Date range: {file_info['date_range']}\n" \
                         f"  → Will load as table: {file_info['table_name']}"
            
            file_choices.append({
                'name': choice_text,
                'value': {
                    'path': file_path,
                    'filename': filename,
                    'table_name': file_info['table_name']
                }
            })

        print("\n" + "=" * 80)
        print("LOAD EXISTING AUDIT EVENTS DATA")
        print("=" * 80)
        
        selected = questionary.select(
            "Select an audit events JSON file to load into DuckDB:",
            choices=file_choices
        ).ask()

        if not selected:
            print("No file selected.")
            return

        # Load the selected file
        json_file = selected['path']
        table_name = selected['table_name']
        filename = selected['filename']
        
        print(f"\nLoading {filename}...")
        self._load_to_duckdb(json_file, table_name)
        print(f"✓ Successfully loaded audit events into table: {table_name}")
        print(f"✓ Use: SELECT event_name, event_time, source_name, resource_name, user_name FROM {table_name} ORDER BY event_time DESC LIMIT 10;")

    def _analyze_file(self, file_path):
        """Analyze an audit events JSON file to extract metadata"""
        filename = os.path.basename(file_path)
        
        # Get file stats
        stat = os.stat(file_path)
        file_size = self._format_file_size(stat.st_size)
        created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Extract date and window from filename
        # Format: audit_events_DD-MM-YYYY_DAYS.json
        try:
            parts = filename.replace('audit_events_', '').replace('.json', '').split('_')
            date_part = parts[0]  # DD-MM-YYYY
            days_part = parts[1]  # DAYS
            
            # Parse date
            end_date = datetime.strptime(date_part, "%d-%m-%Y")
            start_date = end_date - pd.Timedelta(days=int(days_part))
            
            date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')} ({days_part} days)"
        except:
            date_range = "Unknown date range"
        
        # Count events in JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                event_count = len(data) if isinstance(data, list) else 0
        except:
            event_count = "Unknown"
        
        # Generate table name
        table_name = filename.replace('audit_events_', '').replace('.json', '').replace('-', '')
        
        return {
            'event_count': event_count,
            'file_size': file_size,
            'created': created,
            'date_range': date_range,
            'table_name': f"audit_events_{table_name}"
        }

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 1)
        return f"{s} {size_names[i]}"

    def _fetch_new_data(self, parts, snapshot_dir):
        """Fetch new audit events data from OCI API"""
        reference_date, window = parts
        
        # Validate reference_date
        try:
            ref_date = datetime.strptime(reference_date, "%d-%m-%Y")
            retention_days = 365  # OCI audit log retention period
            if (datetime.now() - ref_date).days > retention_days:
                print(f"Error: reference_date must be within the last {retention_days} days")
                return
        except ValueError:
            print("Error: reference_date must be in format DD-MM-YYYY")
            return
            
        # Validate window
        try:
            window = int(window)
            if window < 1 or window > retention_days:
                print(f"Error: window must be between 1 and {retention_days} days")
                return
            
            # Check if the window extends beyond retention period
            start_date = ref_date - timedelta(days=window)
            if (datetime.now() - start_date).days > retention_days:
                print(f"Error: The specified window extends beyond the {retention_days}-day audit log retention period")
                return
        except ValueError:
            print("Error: window must be an integer")
            return

        # Get configuration
        worker_count = self.ctx.config_manager.get_setting("audit_worker_count") or 10
        worker_window = self.ctx.config_manager.get_setting("audit_worker_window") or 1

        # Initialize fetcher
        try:
            # Create a quiet fetcher that doesn't print verbose messages during progress
            fetcher = AuditFetcher(
                reference_date=reference_date,
                window=window,
                workers=worker_count,
                worker_window=worker_window,
                profile_name=self.ctx.config_manager.get_setting("oci_profile") or "DEFAULT",
                verbose=False  # Suppress all verbose output including interval generation
            )

            # Use snapshot_dir for temporary batch files
            original_cwd = os.getcwd()
            os.chdir(snapshot_dir)
            try:
                total_intervals = len(fetcher.intervals)
                
                # Show clean progress without cluttered output
                print(f"\nStarting parallel audit fetch with {worker_count} workers...")
                print(f"Target: {total_intervals} intervals, {reference_date} ({window} days)")
                
                with tqdm(total=total_intervals, desc="Fetching audit events", 
                         bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
                    def progress_callback(idx):
                        pbar.update(1)
                    
                    output_filename = f"audit_events_{reference_date}_{window}.json"
                    output_path = os.path.join(snapshot_dir, output_filename)
                    
                    # Fetch data with clean progress bar (no verbose output)
                    json_file, failed_timeframes = fetcher.run(output_path, progress_callback)

                # Now show the summary report that was collected during fetching
                self._print_fetch_summary(fetcher, json_file, failed_timeframes)

                # Load into DuckDB if we got some data
                if json_file and os.path.exists(json_file):
                    table_name = f"audit_events_{reference_date.replace('-', '')}_{window}"
                    self._load_to_duckdb(json_file, table_name)
                    fetcher.cleanup()
                    print(f"✓ Successfully loaded audit events into table: {table_name}")
                    print(f"✓ Use: SELECT event_name, event_time, source_name FROM {table_name} ORDER BY event_time DESC LIMIT 10;")
                else:
                    print("❌ No data was successfully fetched")
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"Error fetching audit events: {e}")

    def _print_fetch_summary(self, fetcher, json_file, failed_timeframes):
        """Print a clean summary report after fetching is complete"""
        print("\n" + "=" * 80)
        print("AUDIT EVENTS FETCH SUMMARY REPORT")
        print("=" * 80)
        
        # Show successful batches from fetcher's status messages
        if hasattr(fetcher, 'status_messages'):
            success_count = len([msg for msg in fetcher.status_messages if "✓" in msg])
            print(f"✓ Successful intervals: {success_count}")
            
            # Show a few examples of successful fetches
            success_messages = [msg for msg in fetcher.status_messages if "✓" in msg]
            if success_messages:
                print("✓ Sample successful intervals:")
                for msg in success_messages[:3]:  # Show first 3
                    print(f"  {msg}")
                if len(success_messages) > 3:
                    print(f"  ... and {len(success_messages) - 3} more successful intervals")
        
        if json_file and os.path.exists(json_file):
            # Get final file stats
            stat = os.stat(json_file)
            file_size = self._format_file_size(stat.st_size)
            print(f"✓ Consolidated file: {os.path.basename(json_file)} ({file_size})")
            
            # Count total events
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    total_events = len(data) if isinstance(data, list) else 0
                    print(f"✓ Total events collected: {total_events:,}")
                    
                    if data and total_events > 0:
                        first_event = data[0].get('eventTime', data[0].get('event_time', 'Unknown'))
                        last_event = data[-1].get('eventTime', data[-1].get('event_time', 'Unknown'))
                        print(f"✓ Event time range: {first_event} to {last_event}")
            except:
                print("✓ Consolidated file created (event count unavailable)")
        
        # Handle failed timeframes
        if failed_timeframes:
            print(f"\n❌ Failed intervals: {len(failed_timeframes)}")
            print("You can retry failed timeframes using the fetcher's retry method")
        
        print("=" * 80)

    def _load_to_duckdb(self, json_file, table_name):
        """Load JSON file into DuckDB with flattening"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                print("Warning: JSON file contains no data")
                return

            # Check if table already exists
            existing_tables = self.ctx.query_executor.show_tables()
            if table_name in existing_tables:
                overwrite = questionary.confirm(
                    f"Table '{table_name}' already exists. Overwrite?"
                ).ask()
                if not overwrite:
                    print("Load cancelled.")
                    return
                # Drop existing table
                self.ctx.query_executor.conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            # Flatten nested JSON
            flattened = []
            for event in data:
                flat_event = {}
                self._flatten_dict(event, flat_event)
                flattened.append(flat_event)

            df = pd.DataFrame(flattened)
            
            # Register and create table
            self.ctx.query_executor.conn.register(table_name, df)
            self.ctx.query_executor.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
            print(f"Created table '{table_name}' with {len(df)} rows and {len(df.columns)} columns")
            
        except Exception as e:
            print(f"Error loading audit events into DuckDB: {e}")

    def _flatten_dict(self, d, flat_dict, prefix=''):
        """Recursively flatten nested dictionaries and handle lists"""
        for k, v in d.items():
            key = f"{prefix}{k}" if prefix else k
            key = key.replace(' ', '_').replace('-', '_').replace('.', '_')
            
            if isinstance(v, dict):
                self._flatten_dict(v, flat_dict, f"{key}_")
            elif isinstance(v, list):
                flat_dict[key] = json.dumps(v) if v else None
            else:
                flat_dict[key] = v


class AuditEventsDeleteCommand(Command):
    description = """Delete audit events JSON files and their corresponding DuckDB tables.

USAGE:
  audit_events delete

FUNCTIONALITY:
  ✓ Shows interactive list of all audit events files in current snapshot
  ✓ Displays file details: size, event count, date range, creation time
  ✓ Allows single or multiple file selection
  ✓ Confirms deletion with detailed summary
  ✓ Removes corresponding DuckDB tables if they exist
  ✓ Shows cleanup summary with freed disk space

EXAMPLE OUTPUT:
  Select audit events files to delete:
  
  [✓] audit_events_15-06-2025_7.json
      → 1,243 events, 2.1 MB, June 8-15 2025, Table: audit_events_15062025_7
  
  [ ] audit_events_01-01-2025_30.json  
      → 5,678 events, 8.7 MB, Dec 2-Jan 1 2025, Table: audit_events_01012025_30

SAFETY FEATURES:
  ✓ Confirmation prompt before deletion
  ✓ Shows exactly what will be deleted
  ✓ Option to cancel at any time
  ✓ Graceful handling of missing tables"""

    def execute(self, args):
        snapshot_dir = self.ctx.query_executor.current_snapshot_dir
        if not snapshot_dir:
            print("Error: No active tenancy snapshot. Use 'set tenancy' first.")
            return

        pattern = os.path.join(snapshot_dir, "audit_events_*_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No audit events JSON files found in {snapshot_dir}")
            return

        # Analyze files and create choices
        file_choices = []
        for file_path in sorted(files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(file_path)
            file_info = self._analyze_file(file_path)
            
            choice_text = f"{filename}\n" \
                         f"  → {file_info['event_count']} events, {file_info['file_size']}, " \
                         f"{file_info['date_range']}\n" \
                         f"  → Table: {file_info['table_name']}, Created: {file_info['created']}"
            
            file_choices.append({
                'name': choice_text,
                'value': {
                    'path': file_path,
                    'filename': filename,
                    'table_name': file_info['table_name'],
                    'size_bytes': file_info['size_bytes']
                }
            })

        print("\n" + "=" * 80)
        print("DELETE AUDIT EVENTS DATA")
        print("=" * 80)
        
        # Multiple selection
        selected_files = questionary.checkbox(
            "Select audit events files to delete:",
            choices=file_choices
        ).ask()

        if not selected_files:
            print("No files selected for deletion.")
            return

        # Show deletion summary
        total_size = sum(f['size_bytes'] for f in selected_files)
        total_files = len(selected_files)
        
        print(f"\n{'='*60}")
        print("DELETION SUMMARY")
        print(f"{'='*60}")
        print(f"Files to delete: {total_files}")
        print(f"Total disk space to free: {self._format_file_size(total_size)}")
        print("\nFiles and tables to be removed:")
        
        for file_info in selected_files:
            print(f"  📄 {file_info['filename']}")
            print(f"     🗃️  {file_info['table_name']} (if exists)")
        
        # Final confirmation
        confirm = questionary.confirm(
            f"\n❗ Are you sure you want to delete {total_files} file(s) and their tables?"
        ).ask()
        
        if not confirm:
            print("Deletion cancelled.")
            return

        # Perform deletion
        deleted_files = 0
        deleted_tables = 0
        freed_space = 0
        
        existing_tables = self.ctx.query_executor.show_tables()
        
        for file_info in selected_files:
            try:
                # Delete JSON file
                os.remove(file_info['path'])
                deleted_files += 1
                freed_space += file_info['size_bytes']
                print(f"✓ Deleted file: {file_info['filename']}")
                
                # Delete DuckDB table if it exists
                table_name = file_info['table_name']
                if table_name in existing_tables:
                    self.ctx.query_executor.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    deleted_tables += 1
                    print(f"✓ Deleted table: {table_name}")
                
            except Exception as e:
                print(f"❌ Error deleting {file_info['filename']}: {e}")

        # Final summary
        print(f"\n{'='*60}")
        print("DELETION COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Files deleted: {deleted_files}")
        print(f"✓ Tables deleted: {deleted_tables}")
        print(f"✓ Disk space freed: {self._format_file_size(freed_space)}")

    def _analyze_file(self, file_path):
        """Analyze an audit events JSON file to extract metadata"""
        filename = os.path.basename(file_path)
        
        # Get file stats
        stat = os.stat(file_path)
        file_size = self._format_file_size(stat.st_size)
        created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Extract date and window from filename
        try:
            parts = filename.replace('audit_events_', '').replace('.json', '').split('_')
            date_part = parts[0]
            days_part = parts[1]
            
            end_date = datetime.strptime(date_part, "%d-%m-%Y")
            start_date = end_date - pd.Timedelta(days=int(days_part))
            
            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d %Y')}"
        except:
            date_range = "Unknown"
        
        # Count events in JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                event_count = len(data) if isinstance(data, list) else 0
        except:
            event_count = "Unknown"
        
        # Generate table name
        table_name = filename.replace('audit_events_', '').replace('.json', '').replace('-', '')
        
        return {
            'event_count': event_count,
            'file_size': file_size,
            'size_bytes': stat.st_size,
            'created': created,
            'date_range': date_range,
            'table_name': f"audit_events_{table_name}"
        }

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 1)
        return f"{s} {size_names[i]}"


# Remove the old FetchAuditEventsCommand class (keeping it for backward compatibility if needed)
class FetchAuditEventsCommand(Command):
    """Deprecated: Use 'audit_events fetch' instead"""
    description = """⚠️  DEPRECATED: Use 'audit_events fetch' instead.

This command is kept for backward compatibility but will be removed in future versions.
Please use the new audit_events commands:
- audit_events fetch <date> <days>  # Fetch new data
- audit_events fetch               # Load existing data  
- audit_events delete              # Delete files"""

    def execute(self, args):
        print("⚠️  DEPRECATED: 'fetch audit_events' is deprecated.")
        print("Please use the new commands:")
        print("  - audit_events fetch <date> <days>  # Fetch new data")
        print("  - audit_events fetch               # Load existing data")
        print("  - audit_events delete              # Delete files")
        print()
        
        # For now, redirect to the new fetch command
        fetch_cmd = AuditEventsFetchCommand(self.ctx)
        fetch_cmd.execute(args)