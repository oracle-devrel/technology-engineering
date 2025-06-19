"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

audit_fetcher.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import glob
import json
import logging
import os
import time

from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import oci
from oci.util import to_dict

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AuditFetcher:
    """
    Fetch OCI Audit logs in parallel batches and consolidate into a single JSON file.
    The window is completely prior to the reference_date (end date).

    Attributes:
        reference_date (datetime): End date for retrieval window (UTC).
        window (int): Total window size in days prior to reference_date.
        workers (int): Number of parallel worker threads.
        worker_window (int): Hours per batch.
        config (dict): OCI config loaded from file.
        compartment_id (str): Tenancy OCID from config.
        audit_client (AuditClient): OCI Audit client.
        intervals (List[Tuple[datetime, datetime]]): List of (start, end) batches.
        verbose (bool): Whether to print detailed progress messages.
        status_messages (List[str]): Collected status messages for summary.
    """
    def __init__(
        self,
        reference_date: str,
        window: int,
        workers: int,
        worker_window: int,
        profile_name: str = "DEFAULT",
        config_file: str = None,
        verbose: bool = True
    ):
        # Parse reference date (this becomes the END date)
        try:
            self.reference_date = datetime.strptime(reference_date, "%d-%m-%Y").replace(tzinfo=timezone.utc)
        except ValueError as ve:
            raise ValueError(f"Invalid reference_date format: {ve}")

        self.window = window
        self.workers = workers
        self.worker_window = worker_window
        self.verbose = verbose  # Set from parameter instead of defaulting to True
        self.status_messages = []  # Store messages for later summary

        # Calculate start and end times (window days BEFORE reference_date)
        self.end_time = self.reference_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.start_time = (self.reference_date - timedelta(days=window)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self._log(f"Audit search window: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} to {self.end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self._log(f"Window duration: {window} days prior to {self.reference_date.strftime('%Y-%m-%d')}")

        # Load OCI configuration
        if config_file:
            cfg_location = os.path.expanduser(config_file)
            self.config = oci.config.from_file(file_location=cfg_location, profile_name=profile_name)
        else:
            self.config = oci.config.from_file(profile_name=profile_name)

        self.compartment_id = self.config.get("tenancy")
        self.audit_client = oci.audit.AuditClient(
            self.config,
            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
        )

        # Prepare batch intervals
        self.intervals = self._generate_intervals()

    def _log(self, message, level="INFO"):
        """Store messages for later display instead of immediate printing when in quiet mode"""
        self.status_messages.append(f"[{level}] {message}")
        
        # Only print immediately if in verbose mode
        if self.verbose:
            if level == "ERROR":
                print(f"ERROR: {message}")
            else:
                print(message)

    def _generate_intervals(self) -> List[Tuple[datetime, datetime]]:
        """Generate a list of (start, end) datetime tuples for each worker batch."""
        intervals: List[Tuple[datetime, datetime]] = []
        current = self.start_time
        delta = timedelta(hours=self.worker_window)
        
        if self.verbose:
            self._log(f"Generating audit intervals with {self.worker_window}-hour chunks...")
        
        while current < self.end_time:
            next_end = min(current + delta, self.end_time)
            intervals.append((current, next_end))
            if self.verbose:
                self._log(f"  Interval: {current.strftime('%Y-%m-%d %H:%M')} to {next_end.strftime('%Y-%m-%d %H:%M')}")
            current = next_end
            
        self._log(f"Total audit intervals: {len(intervals)}")
        return intervals

    def _fetch_and_write_events(self, start: datetime, end: datetime) -> Tuple[bool, str, str]:
        """
        Fetch audit events for a single time window and write to a temp JSON file.

        Returns:
            tuple: (success: bool, result: str, timeframe_string: str)
        """
        timeframe_string = f"{start.strftime('%d-%m-%Y %H:%M')},{end.strftime('%d-%m-%Y %H:%M')}"
        
        try:
            # Only log fetch attempts in verbose mode
            if self.verbose:
                self._log(f"Fetching audit events from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
            
            # Use OCI pagination helper to get all events in this interval
            response = oci.pagination.list_call_get_all_results(
                self.audit_client.list_events,
                compartment_id=self.compartment_id,
                start_time=start,
                end_time=end
            )
            events = response.data
            logger.info(f"Fetched {len(events)} events from {start} to {end}")

            # Convert to serializable dicts
            dicts = [to_dict(ev) for ev in events]

            # Write to temporary file
            filename = f"audit_events_{start.strftime('%Y-%m-%dT%H-%M')}_to_{end.strftime('%Y-%m-%dT%H-%M')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dicts, f, indent=2)
                
            # Store detailed results for summary (always store, regardless of verbose mode)
            result_msg = f"✓ {start.strftime('%Y-%m-%d %H:%M')}-{end.strftime('%H:%M')}: {len(dicts)} events → {filename}"
            self.status_messages.append(result_msg)
            
            # Only print immediately if verbose
            if self.verbose:
                print(f"  → Found {len(dicts)} audit events, saved to {filename}")
                
            return (True, filename, timeframe_string)

        except Exception as e:
            error_msg = f"Error fetching audit events {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}: {e}"
            logger.error(error_msg)
            self.status_messages.append(f"{error_msg}")
            
            if self.verbose:
                print(error_msg)
            return (False, error_msg, timeframe_string)

    def run(self, output_file: str, progress_callback=None) -> Tuple[str, List[str]]:
        """
        Execute the fetcher across all intervals and consolidate into a single JSON file.

        Args:
            output_file (str): Path to final consolidated JSON file.
            progress_callback (callable): Optional function called with each completed batch index.

        Returns:
            tuple: (output_file_path: str, failed_timeframes: list)
        """
        if self.verbose:
            print(f"\nStarting parallel audit fetch with {self.workers} workers...")
            print(f"Target output file: {output_file}")
        
        temp_files: List[str] = []
        failed_timeframes: List[str] = []

        # Parallel fetching
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_idx = {
                executor.submit(self._fetch_and_write_events, s, e): idx
                for idx, (s, e) in enumerate(self.intervals)
            }
            
            completed = 0
            total = len(self.intervals)
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    success, result, timeframe_string = future.result()
                    
                    if success:
                        temp_files.append(result)
                    else:
                        failed_timeframes.append(timeframe_string)
                        # Store failure in status messages
                        self.status_messages.append(f"FAILED AUDIT TIMEFRAME: {timeframe_string}")
                        
                        # Only print immediately if verbose
                        if self.verbose:
                            print(f"FAILED AUDIT TIMEFRAME: {timeframe_string}")
                            print(f"Error: {result}")
                        
                    completed += 1
                    
                    # Only show progress in verbose mode (progress bar handles this in quiet mode)
                    if self.verbose:
                        print(f"Progress: {completed}/{total} audit intervals completed")
                    
                    if progress_callback:
                        progress_callback(idx)
                        
                except Exception as e:
                    logger.error(f"Audit batch {idx} exception: {e}")
                    if self.verbose:
                        print(f"EXCEPTION in audit batch {idx}: {e}")

        # Consolidate
        self._log(f"Consolidating {len(temp_files)} audit temporary files...")
        all_events = []
        
        for tf in temp_files:
            try:
                with open(tf, 'r', encoding='utf-8') as f:
                    batch_events = json.load(f)
                    all_events.extend(batch_events)
                    if self.verbose:
                        self._log(f"  → Added {len(batch_events)} audit events from {tf}")
            except Exception as e:
                logger.error(f"Error reading audit temp file {tf}: {e}")
                self._log(f"Error reading audit temp file {tf}: {e}", "ERROR")

        # Sort by event_time if present
        self._log(f"Sorting {len(all_events)} total audit events by event time...")
        all_events.sort(key=lambda ev: ev.get('eventTime', ev.get('event_time', '')))

        # Write final file
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, indent=2)
            logger.info(f"Consolidated {len(all_events)} events to {output_file}")
            
            self._log(f"✓ Consolidated audit file written: {output_file}")
            self._log(f"✓ Total audit events found: {len(all_events)}")
            
            # Show date range of actual data
            if all_events:
                first_event = all_events[0].get('eventTime', all_events[0].get('event_time', 'Unknown'))
                last_event = all_events[-1].get('eventTime', all_events[-1].get('event_time', 'Unknown'))
                self._log(f"✓ Event time range: {first_event} to {last_event}")
            
            return (output_file, failed_timeframes)
        except Exception as e:
            logger.error(f"Error writing consolidated audit file: {e}")
            self._log(f"Error writing consolidated audit file: {e}", "ERROR")
            return ("", failed_timeframes)

    def retry_failed_timeframes(self, failed_timeframes: List[str], output_file: str = None) -> Tuple[int, List[str]]:
        """
        Retry fetching for specific failed timeframes.
        
        Args:
            failed_timeframes: List of timeframe strings in format "DD-MM-YYYY HH:MM,DD-MM-YYYY HH:MM"
            output_file: Optional output file for retry results
            
        Returns:
            tuple: (success_count: int, still_failed: list)
        """
        print(f"\n{'='*60}")
        print(f"RETRYING {len(failed_timeframes)} FAILED AUDIT TIMEFRAMES")
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
                print(f"    Queued audit retry: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"    Invalid audit timeframe format '{tf_string}': {e}")
                invalid_timeframes.append(tf_string)
        
        if not retry_intervals:
            print("No valid audit timeframes to retry.")
            return (0, invalid_timeframes)
        
        # Execute retries
        temp_files = []
        still_failed = []
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_timeframe = {
                executor.submit(self._fetch_and_write_events, start, end): (start, end)
                for start, end in retry_intervals
            }
            
            for future in as_completed(future_to_timeframe):
                start, end = future_to_timeframe[future]
                success, result, timeframe_string = future.result()
                
                if success:
                    temp_files.append(result)
                    print(f"    AUDIT SUCCESS: {timeframe_string}")
                else:
                    still_failed.append(timeframe_string)
                    print(f"    AUDIT STILL FAILED: {timeframe_string}")
        
        # Consolidate retry results if requested
        if output_file and temp_files:
            print(f"\nConsolidating {len(temp_files)} audit retry results...")
            all_events = []
            
            for tf in temp_files:
                try:
                    with open(tf, 'r', encoding='utf-8') as f:
                        batch_events = json.load(f)
                        all_events.extend(batch_events)
                except Exception as e:
                    print(f"Error reading audit retry temp file {tf}: {e}")
            
            # Sort and write
            all_events.sort(key=lambda ev: ev.get('eventTime', ev.get('event_time', '')))
            
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_events, f, indent=2)
                print(f"✓ Audit retry results written to: {output_file}")
                print(f"✓ Total retry audit events found: {len(all_events)}")
            except Exception as e:
                print(f"Error writing audit retry file: {e}")
        
        # Report final status
        success_count = len(retry_intervals) - len(still_failed)
        still_failed.extend(invalid_timeframes)  # Include invalid formats
        
        print(f"\n{'='*60}")
        print(f"  AUDIT RETRY SUMMARY")
        print(f"{'='*60}")
        print(f"  Successful audit retries: {success_count}")
        print(f"  Still failed audit: {len(still_failed)}")
        
        if still_failed:
            print("\nAudit timeframes still failing:")
            print("STILL_FAILED_AUDIT_TIMEFRAMES = [")
            for tf in still_failed:
                print(f'    "{tf}",')
            print("]")
        
        return (success_count, still_failed)

    def cleanup(self) -> None:
        """Remove all temporary batch files matching the audit events pattern."""
        pattern = "audit_events_*_to_*.json"
        temp_files = glob.glob(pattern)
        
        if temp_files:
            self._log(f"Cleaning up {len(temp_files)} audit temporary files...")
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                    logger.debug(f"Removed audit temp file {tmp}")
                    if self.verbose:
                        self._log(f"  → Removed {tmp}")
                except Exception as e:
                    logger.error(f"Failed to remove audit temp file {tmp}: {e}")
                    self._log(f"  → Failed to remove {tmp}: {e}", "ERROR")
        else:
            self._log("No audit temporary files to clean up.")

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