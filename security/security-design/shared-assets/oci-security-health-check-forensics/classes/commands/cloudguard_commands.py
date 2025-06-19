"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

cloudguard_commands.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from .base_command import Command
from datetime import datetime
import os
import glob
import json
import questionary
import pandas as pd
from tqdm import tqdm
from ..cloudguard_fetcher import CloudGuardFetcher

class CloudGuardFetchCommand(Command):
    description = """Fetches OCI Cloud Guard problems or loads existing data.

USAGE:
  cloudguard fetch <reference_date> <window_days>    # Fetch new data
  cloudguard fetch                                   # Load existing data

FETCH NEW DATA:
  cloudguard fetch 15-06-2025 7
    → Fetches Cloud Guard problems from June 8-15, 2025 (7 days ending on June 15)
  
  cloudguard fetch 01-01-2025 30  
    → Fetches Cloud Guard problems from December 2-31, 2024 (30 days ending on Jan 1)

LOAD EXISTING DATA:
  cloudguard fetch
    → Shows interactive file selector with details:
      - Problem count and file size
      - Date range and creation time
      - Target DuckDB table name
    → Loads selected file into DuckDB for querying

WHAT FETCH DOES:
  ✓ Splits time window into parallel worker batches
  ✓ Fetches all Cloud Guard problems using OCI API
  ✓ Shows clean progress bar with summary report
  ✓ Creates: cloudguard_problems_<date>_<days>.json  
  ✓ Loads into DuckDB table: cloudguard_problems_<date><days>
  ✓ Provides retry instructions for failed periods

CONFIGURATION:
  audit_worker_count: 5     # Parallel workers (config.yaml)
  audit_worker_window: 1    # Hours per batch (config.yaml)"""

    def execute(self, args):
        parts = args.split()
        snapshot_dir = self.ctx.query_executor.current_snapshot_dir
        if not snapshot_dir:
            print("Error: No active tenancy snapshot. Use 'set tenancy' first.")
            return

        # Mode 2: Interactive load of existing cloudguard JSON files
        if len(parts) == 0:
            self._interactive_load_existing_data(snapshot_dir)
            return

        # Mode 1: Fetch new Cloud Guard data
        if len(parts) != 2:
            print("Usage: cloudguard fetch <reference_date> <window_days>")
            print("   or: cloudguard fetch  (interactive mode)")
            return

        self._fetch_new_data(parts, snapshot_dir)

    def _interactive_load_existing_data(self, snapshot_dir):
        """Interactive mode to load existing Cloud Guard JSON files"""
        pattern = os.path.join(snapshot_dir, "cloudguard_problems_*_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No Cloud Guard JSON files found in {snapshot_dir}")
            print("Use 'cloudguard fetch <date> <days>' to fetch new data first.")
            return

        # Analyze files and create rich choices
        file_choices = []
        for file_path in sorted(files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(file_path)
            file_info = self._analyze_file(file_path)
            
            choice_text = f"{filename}\n" \
                         f"  → {file_info['problem_count']} problems, {file_info['file_size']}, " \
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
        print("LOAD EXISTING CLOUD GUARD DATA")
        print("=" * 80)
        
        selected = questionary.select(
            "Select a Cloud Guard JSON file to load into DuckDB:",
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
        print(f"✓ Successfully loaded Cloud Guard data into table: {table_name}")
        print(f"✓ Use: select resource_name, detector_rule_id, risk_level, labels, time_first_detected, time_last_detected, lifecycle_state, lifecycle_detail, detector_id from  {table_name} where risk_level = 'HIGH' ORDER BY resource_name")

    def _analyze_file(self, file_path):
        """Analyze a Cloud Guard JSON file to extract metadata"""
        filename = os.path.basename(file_path)
        
        # Get file stats
        stat = os.stat(file_path)
        file_size = self._format_file_size(stat.st_size)
        created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Extract date and window from filename
        # Format: cloudguard_problems_DDMMYYYY_DAYS.json
        try:
            parts = filename.replace('cloudguard_problems_', '').replace('.json', '').split('_')
            date_part = parts[0]  # DDMMYYYY
            days_part = parts[1]  # DAYS
            
            # Parse date
            day = date_part[:2]
            month = date_part[2:4]
            year = date_part[4:8]
            end_date = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
            start_date = end_date - pd.Timedelta(days=int(days_part))
            
            date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')} ({days_part} days)"
        except:
            date_range = "Unknown date range"
        
        # Count problems in JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                problem_count = len(data) if isinstance(data, list) else 0
        except:
            problem_count = "Unknown"
        
        # Generate table name
        table_name = filename.replace('cloudguard_problems_', '').replace('.json', '').replace('-', '_')
        
        return {
            'problem_count': problem_count,
            'file_size': file_size,
            'created': created,
            'date_range': date_range,
            'table_name': f"cloudguard_problems_{table_name}"
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
        """Fetch new Cloud Guard data from OCI API"""
        reference_date, window = parts
        
        # Validate reference_date
        try:
            ref_date = datetime.strptime(reference_date, "%d-%m-%Y")
            retention_days = 365
            if (datetime.now() - ref_date).days > retention_days:
                print(f"Warning: reference_date is more than {retention_days} days ago. Data may not be available.")
        except ValueError:
            print("Error: reference_date must be in format DD-MM-YYYY")
            return
            
        # Validate window
        try:
            window = int(window)
            if window < 1:
                print("Error: window must be a positive integer")
                return
        except ValueError:
            print("Error: window must be an integer")
            return

        # Get configuration
        worker_count = self.ctx.config_manager.get_setting("audit_worker_count") or 5
        worker_window = self.ctx.config_manager.get_setting("audit_worker_window") or 1

        # Initialize fetcher
        try:
            fetcher = CloudGuardFetcher(
                reference_date=reference_date,
                window=window,
                workers=worker_count,
                worker_window=worker_window,
                profile_name=self.ctx.config_manager.get_setting("oci_profile") or "DEFAULT"
            )

            # Use snapshot_dir for temporary batch files
            original_cwd = os.getcwd()
            os.chdir(snapshot_dir)
            try:
                total_intervals = len(fetcher.intervals)
                with tqdm(total=total_intervals, desc="Fetching Cloud Guard problems") as pbar:
                    def progress_callback(idx):
                        pbar.update(1)
                    
                    output_filename = f"cloudguard_problems_{reference_date.replace('-', '')}_{window}.json"
                    output_path = os.path.join(snapshot_dir, output_filename)
                    
                    # Fetch data with clean progress bar
                    json_file, failed_timeframes = fetcher.run(output_path, progress_callback)

                # Handle failed timeframes
                if failed_timeframes:
                    print(f"\n⚠️  Warning: {len(failed_timeframes)} timeframes failed during fetch")
                    print("You can retry failed timeframes using:")
                    print("FAILED_TIMEFRAMES = [")
                    for tf in failed_timeframes[:3]:
                        print(f'    "{tf}",')
                    if len(failed_timeframes) > 3:
                        print(f"    # ... and {len(failed_timeframes) - 3} more")
                    print("]")

                # Load into DuckDB if we got some data
                if json_file and os.path.exists(json_file):
                    table_name = f"cloudguard_problems_{reference_date.replace('-', '')}_{window}"
                    self._load_to_duckdb(json_file, table_name)
                    fetcher.cleanup()
                    print(f"✓ Successfully loaded Cloud Guard problems into table: {table_name}")
                    print(f"✓ Use: SELECT * FROM {table_name} LIMIT 10;")
                else:
                    print("❌ No data was successfully fetched")
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"Error fetching Cloud Guard problems: {e}")

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
            for item in data:
                flat_item = {}
                self._flatten_dict(item, flat_item)
                flattened.append(flat_item)

            df = pd.DataFrame(flattened)
            
            # Register and create table
            self.ctx.query_executor.conn.register(table_name, df)
            self.ctx.query_executor.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
            print(f"Created table '{table_name}' with {len(df)} rows and {len(df.columns)} columns")
            
        except Exception as e:
            print(f"Error loading Cloud Guard data into DuckDB: {e}")

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


class CloudGuardDeleteCommand(Command):
    description = """Delete Cloud Guard JSON files and their corresponding DuckDB tables.

USAGE:
  cloudguard delete

FUNCTIONALITY:
  ✓ Shows interactive list of all Cloud Guard files in current snapshot
  ✓ Displays file details: size, problem count, date range, creation time
  ✓ Allows single or multiple file selection
  ✓ Confirms deletion with detailed summary
  ✓ Removes corresponding DuckDB tables if they exist
  ✓ Shows cleanup summary with freed disk space

EXAMPLE OUTPUT:
  Select Cloud Guard files to delete:
  
  [✓] cloudguard_problems_15062025_7.json
      → 67 problems, 145 KB, June 8-15 2025, Table: cloudguard_problems_15062025_7
  
  [ ] cloudguard_problems_01012025_30.json  
      → 234 problems, 892 KB, Dec 2-Jan 1 2025, Table: cloudguard_problems_01012025_30

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

        pattern = os.path.join(snapshot_dir, "cloudguard_problems_*_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No Cloud Guard JSON files found in {snapshot_dir}")
            return

        # Analyze files and create choices
        file_choices = []
        for file_path in sorted(files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(file_path)
            file_info = self._analyze_file(file_path)
            
            choice_text = f"{filename}\n" \
                         f"  → {file_info['problem_count']} problems, {file_info['file_size']}, " \
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
        print("DELETE CLOUD GUARD DATA")
        print("=" * 80)
        
        # Multiple selection
        selected_files = questionary.checkbox(
            "Select Cloud Guard files to delete:",
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
        """Analyze a Cloud Guard JSON file to extract metadata"""
        filename = os.path.basename(file_path)
        
        # Get file stats
        stat = os.stat(file_path)
        file_size = self._format_file_size(stat.st_size)
        created = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Extract date and window from filename
        try:
            parts = filename.replace('cloudguard_problems_', '').replace('.json', '').split('_')
            date_part = parts[0]
            days_part = parts[1]
            
            day = date_part[:2]
            month = date_part[2:4]
            year = date_part[4:8]
            end_date = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
            start_date = end_date - pd.Timedelta(days=int(days_part))
            
            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d %Y')}"
        except:
            date_range = "Unknown"
        
        # Count problems in JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                problem_count = len(data) if isinstance(data, list) else 0
        except:
            problem_count = "Unknown"
        
        # Generate table name
        table_name = filename.replace('cloudguard_problems_', '').replace('.json', '').replace('-', '_')
        
        return {
            'problem_count': problem_count,
            'file_size': file_size,
            'size_bytes': stat.st_size,
            'created': created,
            'date_range': date_range,
            'table_name': f"cloudguard_problems_{table_name}"
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