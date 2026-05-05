"""
Claude Mythos -- Agent Worker Service
Wraps the AgentRuntime in a service layer with start/stop/restart,
status monitoring, and graceful shutdown handling.
"""

import asyncio
import logging
import signal
from typing import Any, Dict, List, Optional

from app.core.agent_runtime import AgentRuntime
from app.core.scheduler import (
    RuntimeScheduler,
    get_runtime_scheduler,
    init_scheduler,
    shutdown_scheduler,
)

logger = logging.getLogger(__name__)


class AgentWorkerService:
    """
    Service wrapper for the AgentRuntime.
    Provides lifecycle management, monitoring, and graceful shutdown.
    This is the primary interface for the rest of the application.
    """

    _instance: Optional["AgentWorkerService"] = None

    def __new__(cls) -> "AgentWorkerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._runtime: Optional[AgentRuntime] = None
        self._scheduler: Optional[RuntimeScheduler] = None
        self._running = False

    # ── Lifecycle ──────────────────────────────────────────────────

    async def start(self) -> None:
        """
        Start the agent worker service.
        Initializes the runtime and scheduler.
        """
        if self._running:
            logger.warning("AgentWorkerService is already running")
            return

        logger.info("Starting AgentWorkerService...")

        # Create and start the runtime
        self._runtime = AgentRuntime()
        await self._runtime.start()

        # Start the scheduler (bridges to APScheduler)
        self._scheduler = init_scheduler(self._runtime)

        self._running = True

        # Register signal handlers for graceful shutdown
        try:
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._signal_handler)
            logger.info("Signal handlers registered for graceful shutdown")
        except (NotImplementedError, ValueError):
            # Windows or already in signal handler context
            pass

        logger.info("AgentWorkerService started successfully")

    async def stop(self) -> None:
        """
        Gracefully stop the agent worker service.
        Stops the runtime and scheduler.
        """
        if not self._running:
            return

        logger.info("Stopping AgentWorkerService...")

        # Stop scheduler first
        shutdown_scheduler()
        self._scheduler = None

        # Stop runtime
        if self._runtime:
            await self._runtime.stop()
            self._runtime = None

        self._running = False
        logger.info("AgentWorkerService stopped")

    async def restart(self) -> None:
        """Restart the agent worker service."""
        logger.info("Restarting AgentWorkerService...")
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
        logger.info("AgentWorkerService restarted")

    # ── Status ─────────────────────────────────────────────────────

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive service status."""
        runtime_status = {}
        if self._runtime:
            try:
                runtime_status = await self._runtime.get_runtime_status()
            except Exception as e:
                runtime_status = {"error": str(e)}
        else:
            runtime_status = {"running": False, "error": "Runtime not initialized"}

        return {
            "service": "AgentWorkerService",
            "running": self._running,
            "runtime": runtime_status,
            "scheduler_running": self._scheduler is not None,
        }

    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._running

    # ── Task Operations ────────────────────────────────────────────

    async def execute_task_now(self, task_id: str) -> Dict[str, Any]:
        """Force immediate execution of a specific task."""
        if not self._runtime:
            return {"success": False, "error": "Runtime not running"}
        return await self._runtime.execute_task_now(task_id)

    async def retry_task(self, task_id: str) -> Dict[str, Any]:
        """Retry a failed or blocked task."""
        if not self._runtime:
            return {"success": False, "error": "Runtime not running"}
        return await self._runtime.retry_task(task_id)

    async def get_pending_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the pending task queue."""
        if not self._runtime:
            return []
        return await self._runtime.get_pending_queue(limit=limit)

    async def get_runtime_status(self) -> Dict[str, Any]:
        """Get runtime status directly."""
        if not self._runtime:
            return {"running": False, "error": "Runtime not running"}
        return await self._runtime.get_runtime_status()

    # ── Campaign Operations ────────────────────────────────────────

    async def advance_campaign_phase(self, campaign_id: str) -> Dict[str, Any]:
        """Manually trigger campaign phase advancement check."""
        if not self._runtime:
            return {"success": False, "error": "Runtime not running"}
        try:
            await self._runtime._advance_campaign_phase(campaign_id)
            return {
                "success": True,
                "campaign_id": campaign_id,
                "message": "Phase advancement check completed",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Internal ───────────────────────────────────────────────────

    def _signal_handler(self) -> None:
        """Handle OS signals for graceful shutdown."""
        logger.info("Shutdown signal received")
        asyncio.create_task(self.stop())

    def _get_runtime(self) -> Optional[AgentRuntime]:
        """Get the underlying runtime instance (for advanced use)."""
        return self._runtime


# ── Module-level convenience functions ───────────────────────────

_worker_service: Optional[AgentWorkerService] = None


def get_worker_service() -> AgentWorkerService:
    """Get or create the global worker service instance."""
    global _worker_service
    if _worker_service is None:
        _worker_service = AgentWorkerService()
    return _worker_service


async def start_worker_service() -> None:
    """Convenience function to start the worker service."""
    service = get_worker_service()
    await service.start()


async def stop_worker_service() -> None:
    """Convenience function to stop the worker service."""
    service = get_worker_service()
    await service.stop()
