"""
Claude Mythos — Agent Memory System
SQLite-based persistent memory for agents: conversation history,
state management, and context storage.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import (
    ActivityLogModel,
    MessageModel,
    SessionLocal,
)


class AgentMemory:
    """
    Persistent memory store for a single agent.
    Handles conversation history, state, and context.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def _get_db(self) -> Session:
        return SessionLocal()

    # ── Conversation History ─────────────────────────────────────

    def add_message(
        self,
        content: str,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        message_type: str = "chat",
        extra_metadata: Optional[Dict[str, Any]] = None,
        campaign_id: Optional[str] = None,
    ) -> str:
        """Store a message in the agent's conversation history."""
        db = self._get_db()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent=from_agent or self.agent_id,
                to_agent=to_agent or self.agent_id,
                content=content,
                timestamp=datetime.utcnow(),
                message_type=message_type,
                extra_metadata=extra_metadata or {},
                campaign_id=campaign_id,
            )
            db.add(msg)
            db.commit()
            return msg.id
        finally:
            db.close()

    def get_conversation_history(
        self,
        with_agent: Optional[str] = None,
        limit: int = 50,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for this agent.

        Args:
            with_agent: Filter to conversations with a specific agent
            limit: Max number of messages
            message_type: Filter by message type
        """
        db = self._get_db()
        try:
            query = db.query(MessageModel).filter(
                (MessageModel.from_agent == self.agent_id)
                | (MessageModel.to_agent == self.agent_id)
                | (MessageModel.to_agent == "broadcast")
            )

            if with_agent:
                query = query.filter(
                    (MessageModel.from_agent == with_agent)
                    | (MessageModel.to_agent == with_agent)
                )

            if message_type:
                query = query.filter(MessageModel.message_type == message_type)

            messages = query.order_by(MessageModel.timestamp.desc()).limit(limit).all()

            return [
                {
                    "id": m.id,
                    "from_agent": m.from_agent,
                    "to_agent": m.to_agent,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "message_type": m.message_type,
                    "extra_metadata": m.extra_metadata,
                    "campaign_id": m.campaign_id,
                    "read": bool(m.read),
                }
                for m in reversed(messages)
            ]
        finally:
            db.close()

    def get_recent_context(self, limit: int = 10) -> str:
        """Get recent conversation context formatted for LLM prompt injection."""
        history = self.get_conversation_history(limit=limit)
        if not history:
            return "No previous context."

        lines = []
        for msg in history:
            sender = msg["from_agent"]
            content = msg["content"][:200]  # Truncate long messages
            lines.append(f"{sender}: {content}")

        return "\n".join(lines)

    # ── State Management ─────────────────────────────────────────

    def set_state(self, key: str, value: Any) -> None:
        """Store a state value for this agent."""
        db = self._get_db()
        try:
            # Store as a system message with metadata
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent="system",
                to_agent=self.agent_id,
                content=f"STATE:{key}={json.dumps(value)}",
                timestamp=datetime.utcnow(),
                message_type="system",
                extra_metadata={"state_key": key, "state_value": value},
            )
            db.add(msg)
            db.commit()
        finally:
            db.close()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a state value for this agent."""
        db = self._get_db()
        try:
            msg = (
                db.query(MessageModel)
                .filter(
                    MessageModel.to_agent == self.agent_id,
                    MessageModel.message_type == "system",
                    MessageModel.content.like(f"STATE:{key}=%"),
                )
                .order_by(MessageModel.timestamp.desc())
                .first()
            )

            if msg and msg.extra_metadata:
                return msg.extra_metadata.get("state_value", default)
            return default
        finally:
            db.close()

    # ── Activity Logging ─────────────────────────────────────────

    def log_activity(
        self,
        action: str,
        target_type: str = "general",
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log an activity for this agent."""
        db = self._get_db()
        try:
            log = ActivityLogModel(
                id=str(uuid.uuid4()),
                actor=self.agent_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details or {},
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
            return log.id
        finally:
            db.close()

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity log entries for this agent."""
        db = self._get_db()
        try:
            logs = (
                db.query(ActivityLogModel)
                .filter(ActivityLogModel.actor == self.agent_id)
                .order_by(ActivityLogModel.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": l.id,
                    "action": l.action,
                    "target_type": l.target_type,
                    "target_id": l.target_id,
                    "details": l.details,
                    "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                }
                for l in logs
            ]
        finally:
            db.close()

    # ── Memory Search ────────────────────────────────────────────

    def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search agent's memory for relevant entries."""
        db = self._get_db()
        try:
            messages = (
                db.query(MessageModel)
                .filter(
                    (MessageModel.from_agent == self.agent_id)
                    | (MessageModel.to_agent == self.agent_id),
                    MessageModel.content.ilike(f"%{query}%"),
                )
                .order_by(MessageModel.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "from_agent": m.from_agent,
                    "to_agent": m.to_agent,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "message_type": m.message_type,
                }
                for m in messages
            ]
        finally:
            db.close()

    # ── Memory Clearing ──────────────────────────────────────────

    def clear_conversation_history(self, older_than_days: Optional[int] = None) -> int:
        """Clear conversation history, optionally only entries older than N days."""
        db = self._get_db()
        try:
            query = db.query(MessageModel).filter(
                (MessageModel.from_agent == self.agent_id)
                | (MessageModel.to_agent == self.agent_id)
            )

            if older_than_days:
                cutoff = datetime.utcnow() - timedelta(days=older_than_days)
                query = query.filter(MessageModel.timestamp < cutoff)

            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()


class SharedMemory:
    """Shared memory space for inter-agent communication and broadcasts."""

    @staticmethod
    def broadcast(
        from_agent: str,
        content: str,
        message_type: str = "alert",
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a broadcast message to all agents."""
        db = SessionLocal()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent=from_agent,
                to_agent="broadcast",
                content=content,
                timestamp=datetime.utcnow(),
                message_type=message_type,
                extra_metadata=extra_metadata or {},
            )
            db.add(msg)
            db.commit()
            return msg.id
        finally:
            db.close()

    @staticmethod
    def get_broadcasts(since: Optional[datetime] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent broadcast messages."""
        db = SessionLocal()
        try:
            query = db.query(MessageModel).filter(MessageModel.to_agent == "broadcast")

            if since:
                query = query.filter(MessageModel.timestamp > since)

            messages = query.order_by(MessageModel.timestamp.desc()).limit(limit).all()

            return [
                {
                    "id": m.id,
                    "from_agent": m.from_agent,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "message_type": m.message_type,
                    "extra_metadata": m.extra_metadata,
                }
                for m in reversed(messages)
            ]
        finally:
            db.close()

    @staticmethod
    def get_unread_messages(agent_id: str) -> List[Dict[str, Any]]:
        """Get all unread messages for an agent."""
        db = SessionLocal()
        try:
            messages = (
                db.query(MessageModel)
                .filter(
                    (MessageModel.to_agent == agent_id)
                    | (MessageModel.to_agent == "broadcast"),
                    MessageModel.read == 0,
                    MessageModel.from_agent != agent_id,
                )
                .order_by(MessageModel.timestamp.desc())
                .all()
            )

            return [
                {
                    "id": m.id,
                    "from_agent": m.from_agent,
                    "to_agent": m.to_agent,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "message_type": m.message_type,
                    "extra_metadata": m.extra_metadata,
                    "campaign_id": m.campaign_id,
                }
                for m in messages
            ]
        finally:
            db.close()

    @staticmethod
    def mark_as_read(message_id: str) -> bool:
        """Mark a message as read."""
        db = SessionLocal()
        try:
            msg = db.query(MessageModel).filter(MessageModel.id == message_id).first()
            if msg:
                msg.read = 1
                db.commit()
                return True
            return False
        finally:
            db.close()
