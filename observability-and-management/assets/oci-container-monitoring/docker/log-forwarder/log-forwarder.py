#!/usr/bin/env python3
"""
OCI Log Forwarder Sidecar
Monitors log files and forwards them to OCI Logging service
Uses Resource Principal authentication for secure access
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import oci
from oci.loggingingestion import LoggingClient
from oci.loggingingestion.models import PutLogsDetails, LogEntryBatch, LogEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log-forwarder')

class LogForwarder:
    """Forwards logs from shared volume to OCI Logging"""

    def __init__(self):
        self.log_mount_path = os.getenv('LOG_MOUNT_PATH', '/logs')
        # Support both single file (backward compatibility) and multiple files
        single_log_file = os.getenv('LOG_FILE', '')
        if single_log_file:
            self.log_files = [single_log_file]
        else:
            # Monitor all container log files
            self.log_files = [
                'application.log',
                'cadvisor.log',
                'node-exporter.log',
                'mgmt-agent.log',
                'prometheus.log'
            ]

        self.log_ocid = os.getenv('LOG_OCID', '')
        self.log_header = os.getenv('LOG_HEADER', 'container-logs')
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.flush_interval = int(os.getenv('FLUSH_INTERVAL', '5'))

        # Track position for each log file separately
        self.log_positions = {log_file: 0 for log_file in self.log_files}
        self.buffer = []
        self.last_flush = time.time()

        # Initialize OCI client with Resource Principal
        try:
            signer = oci.auth.signers.get_resource_principals_signer()
            self.logging_client = LoggingClient(config={}, signer=signer)
            logger.info("✓ Initialized OCI Logging client with Resource Principal")
        except Exception as e:
            logger.error(f"✗ Failed to initialize OCI client: {e}")
            logger.info("Will continue monitoring logs but won't forward to OCI")
            self.logging_client = None

        logger.info(f"Log Forwarder Configuration:")
        logger.info(f"  Log Directory: {self.log_mount_path}")
        logger.info(f"  Monitoring {len(self.log_files)} log file(s):")
        for log_file in self.log_files:
            logger.info(f"    - {log_file}")
        logger.info(f"  Log OCID: {self.log_ocid[:50]}..." if self.log_ocid else "  Log OCID: Not configured")
        logger.info(f"  Batch Size: {self.batch_size}")
        logger.info(f"  Flush Interval: {self.flush_interval}s")

    def read_new_logs(self):
        """Read new log entries from all monitored log files"""
        all_logs = []

        for log_file in self.log_files:
            log_path = os.path.join(self.log_mount_path, log_file)

            try:
                if not os.path.exists(log_path):
                    continue

                with open(log_path, 'r') as f:
                    f.seek(self.log_positions[log_file])
                    lines = f.readlines()
                    self.log_positions[log_file] = f.tell()

                    # Tag each log entry with its source container
                    container_name = log_file.replace('.log', '')
                    tagged_logs = [
                        f"[{container_name}] {line.strip()}"
                        for line in lines if line.strip()
                    ]
                    all_logs.extend(tagged_logs)

            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
                continue

        return all_logs

    def create_log_entry(self, message):
        """Create an OCI LogEntry object"""
        return LogEntry(
            data=message,
            id=f"{int(time.time() * 1000)}",
            time=datetime.utcnow()
        )

    def flush_buffer(self):
        """Flush buffered logs to OCI Logging"""
        if not self.buffer or not self.logging_client or not self.log_ocid:
            self.buffer = []
            return

        try:
            log_entries = [self.create_log_entry(msg) for msg in self.buffer]

            log_entry_batch = LogEntryBatch(
                entries=log_entries,
                source=self.log_header,
                type="application",
                defaultlogentrytime=datetime.utcnow()
            )

            put_logs_details = PutLogsDetails(
                specversion="1.0",
                log_entry_batches=[log_entry_batch]
            )

            self.logging_client.put_logs(
                log_id=self.log_ocid,
                put_logs_details=put_logs_details
            )

            logger.info(f"✓ Forwarded {len(self.buffer)} log entries to OCI Logging")
            self.buffer = []
            self.last_flush = time.time()

        except Exception as e:
            logger.error(f"✗ Error forwarding logs: {e}")
            # Keep buffer for retry

    def process_logs(self):
        """Process new log entries"""
        new_logs = self.read_new_logs()

        if new_logs:
            logger.debug(f"Read {len(new_logs)} new log entries")
            self.buffer.extend(new_logs)

            # Flush if buffer is full or flush interval exceeded
            should_flush = (
                len(self.buffer) >= self.batch_size or
                (time.time() - self.last_flush) >= self.flush_interval
            )

            if should_flush:
                self.flush_buffer()

    def run(self):
        """Main loop"""
        logger.info("=" * 60)
        logger.info("OCI Log Forwarder Started")
        logger.info("=" * 60)
        logger.info(f"Monitoring {len(self.log_files)} log file(s) in {self.log_mount_path}")
        logger.info(f"Press Ctrl+C to stop")
        logger.info("=" * 60)

        try:
            while True:
                self.process_logs()
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nShutting down gracefully...")
            if self.buffer:
                logger.info("Flushing remaining logs...")
                self.flush_buffer()
            logger.info("Stopped.")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

class LogFileHandler(FileSystemEventHandler):
    """Watchdog event handler for log file changes"""

    def __init__(self, forwarder):
        self.forwarder = forwarder
        # Build set of monitored log paths for quick lookup
        self.monitored_paths = {
            os.path.join(forwarder.log_mount_path, log_file)
            for log_file in forwarder.log_files
        }

    def on_modified(self, event):
        if not event.is_directory and event.src_path in self.monitored_paths:
            self.forwarder.process_logs()

def main():
    """Main entry point"""
    forwarder = LogForwarder()

    # Start file watcher
    event_handler = LogFileHandler(forwarder)
    observer = Observer()
    observer.schedule(event_handler, forwarder.log_mount_path, recursive=False)
    observer.start()

    try:
        forwarder.run()
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
