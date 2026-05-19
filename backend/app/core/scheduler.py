"""
Fankaar Digital -- APScheduler Integration
Schedules daily CEO report, runtime worker loop, health checks,
and campaign phase advancement with proper error handling and retry logic.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.post_publisher import post_publisher
from app.services.google_drive_memory import sync_agent_to_drive, restore_agent_from_drive
from app.core.config import settings


logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None
_runtime_ref = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


class RuntimeScheduler:
    """
    Wraps APScheduler with Fankaar Digital-specific job definitions.
    Handles daily CEO reports, periodic runtime ticks, health checks,
    and campaign maintenance tasks.
    """

    def __init__(self, runtime: Any):
        self.runtime = runtime
        self.scheduler = get_scheduler()
        self._running = False

    def start(self) -> None:
        """Start the scheduler and register all jobs."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._register_jobs()
        self.scheduler.start()
        self._running = True
        logger.info("APScheduler started with all jobs registered")

    def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        if not self._running:
            return

        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("APScheduler shut down")

    def _register_jobs(self) -> None:
        """Register all scheduled jobs."""

        # ── Daily CEO Report ───────────────────────────────────────
        report_hour, report_minute = map(
            int, settings.daily_report_time.split(":")
        )
        self.scheduler.add_job(
            func=self._run_daily_report,
            trigger=CronTrigger(
                hour=report_hour,
                minute=report_minute,
                timezone=settings.daily_report_timezone,
            ),
            id="daily_ceo_report",
            name="Generate and send daily CEO report",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        logger.info(
            f"Scheduled daily CEO report at {settings.daily_report_time} "
            f"({settings.daily_report_timezone})"
        )

        # ── Periodic Runtime Worker Tick ────────────────────────────
        self.scheduler.add_job(
            func=self._runtime_tick,
            trigger=IntervalTrigger(minutes=2),
            id="runtime_tick",
            name="Trigger runtime task processing",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        logger.info("Scheduled runtime tick every 2 minutes")

        # ── Campaign Phase Check ───────────────────────────────────
        self.scheduler.add_job(
            func=self._check_campaign_phases,
            trigger=IntervalTrigger(minutes=10),
            id="campaign_phase_check",
            name="Check campaign phase advancement",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=600,
        )
        logger.info("Scheduled campaign phase check every 10 minutes")

        # ── Blocker Detection ──────────────────────────────────────
        self.scheduler.add_job(
            func=self._detect_blockers,
            trigger=IntervalTrigger(minutes=15),
            id="blocker_detection",
            name="Detect and escalate blocked tasks",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=900,
        )
        logger.info("Scheduled blocker detection every 15 minutes")

        # ── Post Publisher ──────────────────────────────────────────
        self.scheduler.add_job(
            func=self._publish_posts,
            trigger=IntervalTrigger(minutes=1),
            id="post_publisher",
            name="Check and publish due scheduled posts",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=60,
        )
        logger.info("Scheduled post publisher every 1 minute")

        # ── Google Drive Memory Sync ────────────────────────────────
        self.scheduler.add_job(
            func=self._sync_memory_to_drive,
            trigger=IntervalTrigger(hours=1),
            id="drive_memory_sync",
            name="Sync agent memory to Google Drive",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        logger.info("Scheduled Google Drive memory sync every 1 hour")

        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(minutes=5),
            id="health_check",
            name="Runtime health check and logging",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        logger.info("Scheduled health check every 5 minutes")

        # ── Stale Task Cleanup ─────────────────────────────────────
        self.scheduler.add_job(
            func=self._cleanup_stale_tasks,
            trigger=IntervalTrigger(hours=1),
            id="stale_task_cleanup",
            name="Clean up stale in-progress tasks",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        logger.info("Scheduled stale task cleanup every hour")

    # ── Job Handlers ───────────────────────────────────────────────

    async def _run_daily_report(self) -> None:
        """Generate and send the daily CEO report."""
        try:
            from app.agents.jon_ceo import JonCEO
            from app.services.whatsapp import WhatsAppService

            logger.info("Running scheduled daily CEO report")
            ceo = JonCEO()
            report = await ceo.generate_daily_report()

            # Send via WhatsApp if configured
            if settings.has_twilio_configured:
                success = await ceo.send_daily_report_via_whatsapp(report)
                if success:
                    logger.info("Daily report sent via WhatsApp")
                else:
                    logger.warning("Failed to send daily report via WhatsApp")
            else:
                logger.info("WhatsApp not configured -- report generated but not sent")

        except Exception as e:
            logger.error(f"Daily report job failed: {e}", exc_info=True)

    async def _runtime_tick(self) -> None:
        """Trigger the runtime to process pending tasks."""
        try:
            if self.runtime and self.runtime._running:
                logger.debug("Scheduler: triggering runtime task processing")
                # The runtime's worker loop already handles this,
                # but we can force a processing cycle if needed
                # by briefly clearing and setting the shutdown event
                # or calling process directly. For now, the worker loop
                # runs independently; this job serves as a heartbeat.
                status = await self.runtime.get_runtime_status()
                logger.debug(
                    f"Runtime heartbeat: {status['pending_queue_length']} pending, "
                    f"{status['tasks_processed']} processed today"
                )
        except Exception as e:
            logger.error(f"Runtime tick job failed: {e}", exc_info=True)

    async def _check_campaign_phases(self) -> None:
        """Check all campaigns for phase advancement opportunities."""
        try:
            from app.core.database import CampaignModel, SessionLocal, TaskModel

            db = SessionLocal()
            try:
                campaigns = db.query(CampaignModel).all()
                for campaign in campaigns:
                    if campaign.status in ("approval", "live", "completed"):
                        continue

                    tasks = (
                        db.query(TaskModel)
                        .filter(TaskModel.campaign_id == campaign.id)
                        .all()
                    )

                    if not tasks:
                        continue

                    active = [
                        t for t in tasks
                        if t.status in ("pending", "in_progress", "blocked")
                    ]

                    if not active:
                        # All tasks done -- try to advance
                        if self.runtime:
                            await self.runtime._advance_campaign_phase(campaign.id)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Campaign phase check failed: {e}", exc_info=True)

    async def _detect_blockers(self) -> None:
        """Detect and escalate blocked tasks."""
        try:
            if self.runtime and self.runtime._running:
                await self.runtime._handle_blockers()
        except Exception as e:
            logger.error(f"Blocker detection failed: {e}", exc_info=True)

    async def _health_check(self) -> None:
        """Log runtime health status."""
        try:
            if self.runtime:
                status = await self.runtime.get_runtime_status()
                logger.info(
                    f"[Runtime Health] running={status['running']} "
                    f"pending={status['pending_queue_length']} "
                    f"blocked={status['blocked_tasks']} "
                    f"processed={status['tasks_processed']} "
                    f"failed={status['tasks_failed']} "
                    f"uptime={status['uptime']}"
                )
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)

    async def _publish_posts(self) -> None:
        """Check and publish due scheduled posts."""
        try:
            logger.info("Running scheduled post publisher")
            from app.services.post_publisher import post_publisher
            result = await post_publisher.run()
            if result["checked"] > 0:
                logger.info(
                    f"Post publisher: {result['published']} published, "
                    f"{result['failed']} failed out of {result['checked']} checked"
                )
        except Exception as e:
            logger.error(f"Post publisher job failed: {e}", exc_info=True)

    async def _sync_memory_to_drive(self) -> None:
        """Sync all agent memories to Google Drive."""
        try:
            from app.core.database import AgentModel, SessionLocal
            from app.core.enhanced_memory import EnhancedAgentMemory
            from app.services.google_drive_memory import sync_agent_to_drive

            db = SessionLocal()
            try:
                agents = db.query(AgentModel).all()
                synced = 0
                for agent in agents:
                    memory = EnhancedAgentMemory(agent.id)
                    if sync_agent_to_drive(agent.id, memory):
                        synced += 1
                logger.info(f"Drive sync complete: {synced}/{len(agents)} agents synced")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Drive memory sync failed: {e}", exc_info=True)

    async def _cleanup_stale_tasks(self) -> None:
        """Reset tasks stuck in 'in_progress' for too long."""
        try:
            from app.core.database import SessionLocal, TaskModel

            db = SessionLocal()
            try:
                stale_threshold = datetime.utcnow() - timedelta(hours=12)
                stale_tasks = (
                    db.query(TaskModel)
                    .filter(
                        TaskModel.status == "in_progress",
                        TaskModel.started_at < stale_threshold,
                    )
                    .all()
                )

                for task in stale_tasks:
                    logger.warning(
                        f"Cleaning up stale task {task.id} ({task.title}) "
                        f"-- resetting to pending"
                    )
                    task.status = "pending"
                    task.started_at = None
                    notes = list(task.notes or [])
                    notes.append({
                        "author": "system",
                        "content": (
                            "Auto-reset: task was in_progress for >12 hours"
                        ),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    task.notes = notes

                if stale_tasks:
                    db.commit()
                    logger.info(f"Cleaned up {len(stale_tasks)} stale tasks")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Stale task cleanup failed: {e}", exc_info=True)


# ── Module-level interface ───────────────────────────────────────

_runtime_scheduler: Optional[RuntimeScheduler] = None


def init_scheduler(runtime: Any) -> RuntimeScheduler:
    """
    Initialize and start the scheduler with the given runtime.
    Call this from the application lifespan startup.
    """
    global _runtime_scheduler
    _runtime_scheduler = RuntimeScheduler(runtime)
    _runtime_scheduler.start()
    return _runtime_scheduler


def shutdown_scheduler() -> None:
    """Shut down the scheduler. Call from application lifespan shutdown."""
    global _runtime_scheduler
    if _runtime_scheduler:
        _runtime_scheduler.shutdown()
        _runtime_scheduler = None


def get_runtime_scheduler() -> Optional[RuntimeScheduler]:
    """Get the current scheduler instance."""
    return _runtime_scheduler
