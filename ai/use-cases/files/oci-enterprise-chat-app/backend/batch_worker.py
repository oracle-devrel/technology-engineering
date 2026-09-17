"""Durable local batch worker. Run with the same UPLOAD_DIR as the API.

Separate processes claim jobs with OS file locks. Interrupted runs are marked
failed on the next worker pass rather than silently redoing external writes.
"""

import asyncio
import fcntl
import logging
import os
from datetime import UTC, datetime

from dotenv import load_dotenv

load_dotenv()
from services.batch_service import BatchService  # noqa: E402

logger = logging.getLogger(__name__)


async def process_pending(batch):
    for job in reversed(batch.list_jobs()):
        if job.processing_mode != "batch" or job.status not in ("pending", "running"):
            continue
        with (batch.jobs_dir / f"{job.id}.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            try:
                current = batch.get_job(job.id)
                if current.status == "running":
                    batch.update_job(
                        job.id,
                        status="failed",
                        completed_at=datetime.now(UTC),
                        error_message="Worker interrupted during processing; inspect file results and run again",
                    )
                elif current.status == "pending":
                    await batch.execute_job(job.id, parallelism=current.parallelism)
            except Exception:
                logger.exception("Failed processing job %s", job.id)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


async def main():
    batch = BatchService()
    while True:
        await process_pending(batch)
        await asyncio.sleep(float(os.getenv("BATCH_POLL_SECONDS", "2")))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
