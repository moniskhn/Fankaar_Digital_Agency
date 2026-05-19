"""
Fankaar Digital — SQLite Database Setup with SQLAlchemy
All table models: Agent, Client, Campaign, Task, Message, Report,
RegionalProfile, ActivityLog, ScheduledPost
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# ── Engine & Session ─────────────────────────────────────────────

# Ensure data directory exists
os_imported = True


def _ensure_data_dir():
    import os
    db_dir = os.path.dirname(settings.database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


_ensure_data_dir()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.is_development,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Helper: generate UUID ────────────────────────────────────────

def generate_uuid() -> str:
    return str(uuid.uuid4())


# ── SQLAlchemy Models ────────────────────────────────────────────

class AgentModel(Base):
    """Agent/Employee definition."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # e.g., "sandor"
    name = Column(String, nullable=False)  # e.g., "Sandor"
    full_name = Column(String, nullable=False)  # e.g., "Sandor Clegane"
    role = Column(String, nullable=False)  # e.g., "Sales"
    title = Column(String, nullable=False)  # e.g., "Chief Sales Officer"
    description = Column(Text, nullable=False)
    personality = Column(Text, nullable=False)
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    reports_to = Column(String, default="jon")
    avatar = Column(String, default="👤")
    status = Column(String, default="active")  # active, busy, offline
    current_task = Column(String, nullable=True)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientModel(Base):
    """Client information."""
    __tablename__ = "clients"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    region = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    target_audience = Column(Text, default="")
    brand_voice = Column(Text, default="")
    goals = Column(JSON, default=list)
    budget_range = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    notes = Column(Text, default="")
    status = Column(String, default="active")  # active, inactive, prospect
    # ── Billing fields ──
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    package_id = Column(String, default="")  # starter, growth, enterprise
    subscription_status = Column(String, default="inactive")  # active, trialing, past_due, canceled, canceling, inactive, pending
    subscription_current_period_start = Column(DateTime, nullable=True)
    subscription_current_period_end = Column(DateTime, nullable=True)
    assigned_agents = Column(JSON, default=list)  # [agent_id, ...]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignModel(Base):
    """Campaign data."""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="brief")  # brief, strategy, creation, review, approval, live, reporting, completed
    region = Column(String, nullable=False)
    channels = Column(JSON, default=list)  # ["instagram", "tiktok", "email"]
    objectives = Column(JSON, default=list)
    timeline = Column(JSON, default=dict)  # {phase: datetime}
    assigned_agents = Column(JSON, default=list)  # [agent_id, ...]
    deliverables = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    brief_summary = Column(Text, default="")
    budget = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskModel(Base):
    """Task tracking."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    assigned_to = Column(String, ForeignKey("agents.id"), nullable=False)
    assigned_by = Column(String, ForeignKey("agents.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="pending")  # pending, in_progress, review, completed, blocked
    priority = Column(String, default="medium")  # low, medium, high, urgent
    due_date = Column(DateTime, nullable=True)
    dependencies = Column(JSON, default=list)  # [task_id, ...]
    deliverable = Column(Text, nullable=True)
    deliverable_type = Column(String, nullable=True)  # text, image, code, document
    notes = Column(JSON, default=list)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageModel(Base):
    """Inter-agent and agent-owner messages."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    from_agent = Column(String, nullable=False)  # agent_id or "owner"
    to_agent = Column(String, nullable=False)  # agent_id or "owner" or "broadcast"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String, default="chat")  # chat, task, report, alert, decision
    extra_metadata = Column(JSON, default=dict)
    read = Column(Integer, default=0)  # 0 = unread, 1 = read
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportModel(Base):
    """Daily CEO reports."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(String, nullable=False)  # ISO date string YYYY-MM-DD
    summary = Column(Text, nullable=False)
    agent_updates = Column(JSON, default=list)
    campaigns_status = Column(JSON, default=list)
    decisions_made = Column(JSON, default=list)
    issues_flags = Column(JSON, default=list)
    tomorrow_priorities = Column(JSON, default=list)
    owner_attention_required = Column(JSON, default=list)
    sentiment = Column(String, default="neutral")  # positive, neutral, concern
    sent_via_whatsapp = Column(Integer, default=0)  # 0 = no, 1 = yes
    whatsapp_message_sid = Column(String, nullable=True)
    owner_replies = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class RegionalProfileModel(Base):
    """Regional intelligence cache."""
    __tablename__ = "regional_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    region = Column(String, nullable=False, unique=True)
    culture_notes = Column(Text, default="")
    language_primary = Column(String, default="")
    languages_secondary = Column(JSON, default=list)
    social_platforms = Column(JSON, default=list)
    best_posting_times = Column(JSON, default=dict)
    ctas_by_culture = Column(JSON, default=list)
    audience_personas = Column(JSON, default=list)
    content_themes = Column(JSON, default=list)
    taboos = Column(JSON, default=list)
    local_trends = Column(JSON, default=list)
    competitor_landscape = Column(Text, default="")
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class ActivityLogModel(Base):
    """Audit trail of all system actions."""
    __tablename__ = "activity_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    actor = Column(String, nullable=False)  # agent_id or "system" or "owner"
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)  # agent, client, campaign, task, report, etc.
    target_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ScheduledPostModel(Base):
    """Content calendar scheduled posts."""
    __tablename__ = "scheduled_posts"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    platform = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # image, video, carousel, story, text
    content_text = Column(Text, default="")
    media_urls = Column(JSON, default=list)
    scheduled_time = Column(DateTime, nullable=False)
    timezone = Column(String, default="UTC")
    status = Column(String, default="scheduled")  # scheduled, published, failed, cancelled
    posted_at = Column(DateTime, nullable=True)
    engagement_estimate = Column(Float, default=0.0)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContentApprovalModel(Base):
    """Creative asset approval workflow."""
    __tablename__ = "content_approvals"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    asset_type = Column(String, nullable=False)  # reel, poster, caption, ad, story
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    media_url = Column(String, nullable=True)
    content_text = Column(Text, default="")
    status = Column(String, default="pending_review")
    client_feedback = Column(Text, default="")
    revision_count = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════
# Enhanced Memory Models & Contact Submissions

class AgentEpisodeModel(Base):
    """Episodic memory: events, experiences, actions with timestamps and emotions."""
    __tablename__ = "agent_episodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    client_id = Column(String, nullable=True, index=True)
    campaign_id = Column(String, nullable=True, index=True)
    importance = Column(Integer, default=5)
    emotions = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    summary = Column(Text, nullable=True)


class AgentFactModel(Base):
    """Semantic memory: learned facts, knowledge, insights with confidence scores."""
    __tablename__ = "agent_facts"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String, default="general", index=True)
    client_id = Column(String, nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    source = Column(String, default="task")
    timestamp = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)


class AgentPatternModel(Base):
    """Procedural memory: successful patterns, workflows, templates."""
    __tablename__ = "agent_patterns"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    pattern_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    context = Column(String, nullable=False, index=True)
    success_rating = Column(Float, default=0.5)
    usage_count = Column(Integer, default=0)
    client_type = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AgentClientMemoryModel(Base):
    """Client-specific memory: everything about each client relationship."""
    __tablename__ = "agent_client_memories"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    campaign_id = Column(String, nullable=True)


class ContactSubmissionModel(Base):
    """Public contact form submissions."""
    __tablename__ = "contact_submissions"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    company = Column(String, default="")
    message = Column(Text, nullable=False)
    budget_range = Column(String, default="")
    service_interest = Column(String, default="")
    status = Column(String, default="new")  # new, contacted, qualified, converted, archived
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Database Initialization ──────────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI routes to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── JSON Serialization Helpers ───────────────────────────────────

def serialize_json(data: Any) -> str:
    """Serialize data to JSON string."""
    return json.dumps(data, default=str)


def deserialize_json(json_str: str) -> Any:
    """Deserialize JSON string to Python object."""
    return json.loads(json_str) if json_str else {}
