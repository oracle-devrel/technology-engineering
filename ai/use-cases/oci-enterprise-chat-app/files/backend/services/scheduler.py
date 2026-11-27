"""Persisted batch triggers and workflow schedules, restored on startup."""

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from services.schedule_utils import as_utc, cron_trigger

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, storage=None, batch_service=None, engine=None):
        self._scheduler = AsyncIOScheduler(timezone=UTC)
        self._storage = storage
        self._batch_service = batch_service
        self._engine = engine

    def _get_storage(self):
        if self._storage is None:
            from services.workflow_storage import WorkflowStorageService

            self._storage = WorkflowStorageService()
        return self._storage

    def _get_batch_service(self):
        if self._batch_service is None:
            from services.batch_service import BatchService

            self._batch_service = BatchService()
        return self._batch_service

    def start(self):
        if self._scheduler.running:
            return
        self._scheduler.start()
        for trigger in self._get_batch_service().list_triggers():
            try:
                if trigger.is_active:
                    self.register_trigger(trigger.id, trigger.schedule)
            except ValueError as exc:
                logger.error("Invalid batch schedule %s: %s", trigger.id, exc)
        for schedule in self._get_storage().list_schedules(active_only=True):
            try:
                self.register_workflow(schedule)
                self._get_storage().save_schedule(schedule)
            except ValueError as exc:
                logger.error("Invalid workflow schedule %s: %s", schedule.id, exc)

    def shutdown(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def register_trigger(self, trigger_id, cron_expression):
        trigger = cron_trigger(cron_expression)
        self._scheduler.add_job(
            self._execute_trigger,
            trigger=trigger,
            id=f"trigger_{trigger_id}",
            args=[trigger_id],
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        next_run = trigger.get_next_fire_time(None, datetime.now(UTC))
        self._get_batch_service().update_trigger(trigger_id, next_run=next_run)

    def unregister_trigger(self, trigger_id):
        self._remove(f"trigger_{trigger_id}")

    def _remove(self, job_id):
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

    async def _execute_trigger(self, trigger_id):
        try:
            batch = self._get_batch_service()
            trigger = batch.get_trigger(trigger_id)
            if trigger.is_active:
                batch.create_job(
                    connector_id=trigger.connector_id,
                    trigger_id=trigger_id,
                    parallelism=trigger.parallelism,
                )
                batch.update_trigger(
                    trigger_id,
                    last_run=datetime.now(UTC),
                    next_run=cron_trigger(trigger.schedule).get_next_fire_time(
                        None, datetime.now(UTC)
                    ),
                )
        except Exception:
            logger.exception("Batch trigger %s failed", trigger_id)

    def register_workflow(self, schedule):
        if not schedule.is_active:
            self.unschedule_workflow(schedule.id)
            schedule.next_run_at = None
            return
        if schedule.schedule_type == "recurring":
            trigger = cron_trigger(schedule.cron_expression or "")
        else:
            if not schedule.run_at or as_utc(schedule.run_at) <= datetime.now(UTC):
                raise ValueError("One-time schedule must be in the future")
            trigger = DateTrigger(run_date=as_utc(schedule.run_at), timezone=UTC)
        self._scheduler.add_job(
            self._execute_workflow_schedule,
            trigger=trigger,
            id=f"workflow_schedule_{schedule.id}",
            args=[schedule.id, schedule.workflow_id],
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        schedule.next_run_at = trigger.get_next_fire_time(None, datetime.now(UTC))

    def unschedule_workflow(self, schedule_id):
        self._remove(f"workflow_schedule_{schedule_id}")
        # Remove registrations written by the old workflow API.
        self._remove(f"trigger_workflow_{schedule_id}")

    async def _execute_workflow_schedule(self, schedule_id, workflow_id):
        try:
            from services.workflow_engine import WorkflowEngine

            storage = self._get_storage()
            workflow = storage.get_workflow(workflow_id)
            schedule = workflow.schedule
            if (
                not workflow.is_active
                or not schedule
                or schedule.id != schedule_id
                or not schedule.is_active
            ):
                return
            engine = self._engine or WorkflowEngine(storage=storage)
            await engine.execute(
                workflow, schedule.input_data or {}, interactive=False, triggered_by=schedule_id
            )
            # Reload so a concurrent disable/delete is not overwritten.
            workflow = storage.get_workflow(workflow_id)
            if not workflow.schedule or workflow.schedule.id != schedule_id:
                return
            schedule = workflow.schedule
            now = datetime.now(UTC)
            schedule.last_run_at = now
            schedule.updated_at = now
            if schedule.schedule_type == "one_time":
                schedule.is_active = False
                schedule.next_run_at = None
                self.unschedule_workflow(schedule.id)
            elif schedule.is_active:
                schedule.next_run_at = cron_trigger(schedule.cron_expression).get_next_fire_time(
                    None, now
                )
            storage.save_schedule(schedule)
        except Exception:
            logger.exception("Workflow schedule %s failed", schedule_id)


scheduler_service = SchedulerService()
