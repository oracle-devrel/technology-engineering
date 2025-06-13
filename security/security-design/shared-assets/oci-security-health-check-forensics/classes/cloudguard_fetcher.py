"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

cloudguard_fetcher.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import oci
import json
import os
import glob
from datetime import datetime, timedelta, timezone
from oci.util import to_dict
from oci.pagination import list_call_get_all_results
from concurrent.futures import ThreadPoolExecutor, as_completed

class CloudGuardFetcher:
    """
    Fetch OCI Cloud Guard problems in parallel batches and consolidate into a single JSON file.
    The window is completely prior to the reference_date (end date).
    """
    
    def __init__(
        self,
        reference_date: str,
        window: int,
        workers: int,
        worker_window: int,
        profile_name: str = "DEFAULT",
        config_file: str = None
    ):
        # Initialize status tracking
        self.status_messages = []
        self.verbose = True  # Set to False to suppress interval generation messages
        
        # Parse reference date (this becomes the END date)
        try:
            self.reference_date = datetime.strptime(reference_date, "%d-%m-%Y").replace(tzinfo=timezone.utc)
        except ValueError as ve:
            raise ValueError(f"Invalid reference_date format: {ve}")

        self.window = window
        self.workers = workers
        self.worker_window = worker_window

        # Calculate start and end times (window days BEFORE reference_date)
        self.end_time = self.reference_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.start_time = (self.reference_date - timedelta(days=window)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self._log(f"Search window: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} to {self.end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self._log(f"Window duration: {window} days prior to {self.reference_date.strftime('%Y-%m-%d')}")

        # Load OCI config
        if config_file:
            cfg_loc = os.path.expanduser(config_file)
            self.config = oci.config.from_file(file_location=cfg_loc, profile_name=profile_name)
        else:
            self.config = oci.config.from_file(profile_name=profile_name)
        self.compartment_id = self.config.get("tenancy")
        self.client = oci.cloud_guard.CloudGuardClient(
            self.config,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
        )

        # Prepare batch intervals
        self.intervals = self._generate_intervals()

    def _log(self, message, level="INFO"):
        """Store messages for later display instead of immediate printing"""
        self.status_messages.append(f"[{level}] {message}")
        
    def _print_summary_report(self):
        """Print collected status messages as a summary report"""
        if not self.status_messages:
            return
            
        print("\n" + "=" * 80)
        print("CLOUD GUARD FETCH SUMMARY REPORT")
        print("=" * 80)
        for msg in self.status_messages:
            print(msg)
        print("=" * 80)

    def _generate_intervals(self):
        """Generate time intervals for parallel processing."""
        intervals = []
        current = self.start_time
        delta = timedelta(hours=self.worker_window)
        
        if self.verbose:
            self._log(f"Generating intervals with {self.worker_window}-hour chunks...")
        
        while current < self.end_time:
            next_end = min(current + delta, self.end_time)
            intervals.append((current, next_end))
            if self.verbose:
                self._log(f"  Interval: {current.strftime('%Y-%m-%d %H:%M')} to {next_end.strftime('%Y-%m-%d %H:%M')}")
            current = next_end
            
        self._log(f"Total intervals: {len(intervals)}")
        return intervals

    def _fetch_and_write(self, start: datetime, end: datetime) -> tuple:
        """
        Fetch problems for a single time window and write to a temp JSON file.

        Uses the correct parameters `time_last_detected_greater_than_or_equal_to` and
        `time_last_detected_less_than_or_equal_to` as per the Python SDK.
        
        Returns:
            tuple: (success: bool, result: str, timeframe_string: str)
        """
        timeframe_string = f"{start.strftime('%d-%m-%Y %H:%M')},{end.strftime('%d-%m-%Y %H:%M')}"
        
        try:
            # Only log fetch attempts, not every individual fetch
            response = list_call_get_all_results(
                self.client.list_problems,
                compartment_id=self.compartment_id,
                time_last_detected_greater_than_or_equal_to=start,
                time_last_detected_less_than_or_equal_to=end
            )
            problems = response.data
            dicts = [to_dict(p) for p in problems]
            
            fname = f"cloudguard_problems_{start.strftime('%Y-%m-%dT%H-%M')}_to_{end.strftime('%Y-%m-%dT%H-%M')}.json"
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(dicts, f, indent=2)
                
            # Store detailed results for summary
            self._log(f"✓ {start.strftime('%Y-%m-%d %H:%M')}-{end.strftime('%H:%M')}: {len(dicts)} problems → {fname}")
            return (True, fname, timeframe_string)
            
        except Exception as e:
            error_msg = f"Error fetching Cloud Guard problems {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}: {e}"
            self._log(error_msg, "ERROR")
            return (False, error_msg, timeframe_string)

    def run(self, output_file: str, progress_callback=None) -> tuple:
        """
        Execute the fetching process and consolidate results.
        
        Args:
            output_file: Path for the final consolidated JSON file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            tuple: (output_file_path: str, failed_timeframes: list)
        """
        # Clear messages and start fresh
        self.status_messages = []
        self._log(f"Starting parallel fetch with {self.workers} workers")
        self._log(f"Target output file: {output_file}")
        
        temp_files = []
        failed_timeframes = []
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_idx = {
                executor.submit(self._fetch_and_write, s, e): idx
                for idx, (s, e) in enumerate(self.intervals)
            }
            
            completed = 0
            total = len(self.intervals)
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                success, result, timeframe_string = future.result()
                
                if success:
                    temp_files.append(result)
                else:
                    failed_timeframes.append(timeframe_string)
                    self._log(f"  FAILED: {timeframe_string} - {result}", "ERROR")
                    
                completed += 1
                
                if progress_callback:
                    progress_callback(idx)

        # Consolidate all temp files
        self._log(f"Consolidating {len(temp_files)} temporary files...")
        all_items = []
        
        for tf in temp_files:
            try:
                with open(tf, 'r', encoding='utf-8') as f:
                    batch_items = json.load(f)
                    all_items.extend(batch_items)
                    # Removed the detailed log per file to clean up output
            except Exception as e:
                self._log(f"Error reading temp file {tf}: {e}", "ERROR")

        # Sort by last detected time (chronological order)
        self._log(f"Sorting {len(all_items)} total problems by detection time...")
        all_items.sort(key=lambda ev: ev.get('timeLastDetected', ev.get('time_last_detected', '')))

        # Write consolidated file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_items, f, indent=2)
            self._log(f"✓ Consolidated file written: {output_file}")
            self._log(f"✓ Total problems found: {len(all_items)}")
            
            # Show date range of actual data
            if all_items:
                first_detection = all_items[0].get('timeLastDetected', 'Unknown')
                last_detection = all_items[-1].get('timeLastDetected', 'Unknown')
                self._log(f"✓ Detection time range: {first_detection} to {last_detection}")
            
            # Show summary report after progress bar completes
            self._print_summary_report()
            
            # Report failed timeframes after summary
            if failed_timeframes:
                print(f"\n{'='*60}")
                print(f"   {len(failed_timeframes)} TIMEFRAMES FAILED")
                print(f"{'='*60}")
                print("Copy and paste these timeframes to retry failed intervals:")
                print("\nFAILED_TIMEFRAMES = [")
                for tf in failed_timeframes:
                    print(f'    "{tf}",')
                print("]")
                print(f"{'='*60}")
            
            return (output_file, failed_timeframes)
        except Exception as e:
            self._log(f"Error writing consolidated file: {e}", "ERROR")
            self._print_summary_report()
            return ("", failed_timeframes)

    def cleanup(self) -> None:
        """Remove temporary files created during processing."""
        temp_pattern = "cloudguard_problems_*_to_*.json"
        temp_files = glob.glob(temp_pattern)
        
        if temp_files:
            self._log(f"Cleaning up {len(temp_files)} temporary files...")
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                    self._log(f"  → Removed {tmp}")
                except Exception as e:
                    self._log(f"  → Failed to remove {tmp}: {e}", "ERROR")
        else:
            self._log("No temporary files to clean up.")

    def retry_failed_timeframes(self, failed_timeframes: list, output_file: str = None) -> tuple:
        """
        Retry fetching for specific failed timeframes.
        
        Args:
            failed_timeframes: List of timeframe strings in format "DD-MM-YYYY HH:MM,DD-MM-YYYY HH:MM"
            output_file: Optional output file for retry results
            
        Returns:
            tuple: (success_count: int, still_failed: list)
        """
        print(f"\n{'='*60}")
        print(f"  RETRYING {len(failed_timeframes)} FAILED TIMEFRAMES")
        print(f"{'='*60}")
        
        retry_intervals = []
        invalid_timeframes = []
        
        # Parse timeframe strings back to datetime objects
        for tf_string in failed_timeframes:
            try:
                start_str, end_str = tf_string.split(',')
                start_dt = datetime.strptime(start_str, "%d-%m-%Y %H:%M").replace(tzinfo=timezone.utc)
                end_dt = datetime.strptime(end_str, "%d-%m-%Y %H:%M").replace(tzinfo=timezone.utc)
                retry_intervals.append((start_dt, end_dt))
                print(f"    Queued: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"    Invalid timeframe format '{tf_string}': {e}")
                invalid_timeframes.append(tf_string)
        
        if not retry_intervals:
            print("No valid timeframes to retry.")
            return (0, invalid_timeframes)
        
        # Execute retries
        temp_files = []
        still_failed = []
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_timeframe = {
                executor.submit(self._fetch_and_write, start, end): (start, end)
                for start, end in retry_intervals
            }
            
            for future in as_completed(future_to_timeframe):
                start, end = future_to_timeframe[future]
                success, result, timeframe_string = future.result()
                
                if success:
                    temp_files.append(result)
                    print(f"    SUCCESS: {timeframe_string}")
                else:
                    still_failed.append(timeframe_string)
                    print(f"    STILL FAILED: {timeframe_string}")
        
        # Consolidate retry results if requested
        if output_file and temp_files:
            print(f"\nConsolidating {len(temp_files)} retry results...")
            all_items = []
            
            for tf in temp_files:
                try:
                    with open(tf, 'r', encoding='utf-8') as f:
                        batch_items = json.load(f)
                        all_items.extend(batch_items)
                except Exception as e:
                    print(f"Error reading retry temp file {tf}: {e}")
            
            # Sort and write
            all_items.sort(key=lambda ev: ev.get('timeLastDetected', ev.get('time_last_detected', '')))
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_items, f, indent=2)
                print(f"✓ Retry results written to: {output_file}")
                print(f"✓ Total retry problems found: {len(all_items)}")
            except Exception as e:
                print(f"Error writing retry file: {e}")
        
        # Report final status
        success_count = len(retry_intervals) - len(still_failed)
        still_failed.extend(invalid_timeframes)  # Include invalid formats
        
        print(f"\n{'='*60}")
        print(f"  RETRY SUMMARY")
        print(f"{'='*60}")
        print(f"  Successful retries: {success_count}")
        print(f"  Still failed: {len(still_failed)}")
        
        if still_failed:
            print("\nTimeframes still failing:")
            print("STILL_FAILED_TIMEFRAMES = [")
            for tf in still_failed:
                print(f'    "{tf}",')
            print("]")
        
        return (success_count, still_failed)

    def get_date_range_info(self) -> dict:
        """Return information about the calculated date range."""
        return {
            "reference_date": self.reference_date.strftime('%Y-%m-%d'),
            "window_days": self.window,
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "end_time": self.end_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "total_hours": (self.end_time - self.start_time).total_seconds() / 3600,
            "worker_window_hours": self.worker_window,
            "number_of_intervals": len(self.intervals)
        }