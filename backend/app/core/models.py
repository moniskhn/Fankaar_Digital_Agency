"""
Claude Mythos — Pydantic Models (Schemas)
All request/response models for the API.
"""

from datetime import date as date_type
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Common Base Models
# ═══════════════════════════════════════════════════════════════

class MythosBaseModel(BaseModel):
    """Base model with ORM mode for all schemas."""
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# Agent Models
# ═══════════════════════════════════════════════════════════════

class AgentSkill(BaseModel):
    name: str
    level: str = "expert"  # novice, intermediate, expert, master


class Agent(MythosBaseModel):
    id: str
    name: str
    full_name: str
    role: str
    title: str
    description: str
    personality: str
    skills: List[str] = []
    tools: List[str] = []
    reports_to: str = "jon"
    avatar: str = "👤"
    status: str = "active"
    current_task: Optional[str] = None
    system_prompt: str = ""


class AgentCreate(BaseModel):
    name: str
    full_name: str
    role: str
    title: str
    description: str
    personality: str = ""
    skills: List[str] = []
    tools: List[str] = []
    reports_to: str = "jon"
    avatar: str = "👤"
    system_prompt: str = ""


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    reports_to: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    current_task: Optional[str] = None


class AgentStatusUpdate(BaseModel):
    status: str  # active, busy, offline
    current_task: Optional[str] = None


class AgentActivity(BaseModel):
    id: str
    agent_id: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}
    timestamp: datetime


class AgentUpdateEntry(BaseModel):
    """A single agent's update for the daily report."""
    agent_id: str
    agent_name: str
    avatar: str
    status: str
    completed: List[str] = []
    in_progress: List[str] = []
    blocked: List[str] = []
    notes: str = ""


# ═══════════════════════════════════════════════════════════════
# Client Models
# ═══════════════════════════════════════════════════════════════

class Client(MythosBaseModel):
    id: str
    name: str
    industry: str
    region: str
    timezone: str = "UTC"
    target_audience: str = ""
    brand_voice: str = ""
    goals: List[str] = []
    budget_range: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: str = ""
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClientCreate(BaseModel):
    name: str
    industry: str
    region: str
    timezone: str = "UTC"
    target_audience: str = ""
    brand_voice: str = ""
    goals: List[str] = []
    budget_range: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: str = ""


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    goals: Optional[List[str]] = None
    budget_range: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Campaign Models
# ═══════════════════════════════════════════════════════════════

class Deliverable(BaseModel):
    id: str = ""
    name: str
    type: str  # image, video, copy, landing_page, email, ad
    status: str = "pending"  # pending, in_progress, review, approved, rejected
    content: str = ""
    assigned_to: str = ""
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Campaign(MythosBaseModel):
    id: str
    client_id: str
    name: str
    status: str = "brief"  # brief, strategy, creation, review, approval, live, reporting, completed
    region: str
    channels: List[str] = []
    objectives: List[str] = []
    timeline: Dict[str, Optional[datetime]] = {}
    assigned_agents: List[str] = []
    deliverables: List[Deliverable] = []
    metrics: Dict[str, float] = {}
    brief_summary: str = ""
    budget: float = 0.0
    spent: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CampaignCreate(BaseModel):
    client_id: str
    name: str
    region: str
    channels: List[str] = []
    objectives: List[str] = []
    brief_summary: str = ""
    budget: float = 0.0


class CampaignBrief(BaseModel):
    client_id: str
    name: str
    region: str
    channels: List[str]
    objectives: List[str]
    brief_summary: str
    budget: float = 0.0
    target_audience: str = ""
    brand_voice: str = ""
    competitors: List[str] = []
    key_messages: List[str] = []
    must_haves: List[str] = []
    avoid: List[str] = []
    timeline_preference: str = ""


class CampaignStatusEntry(BaseModel):
    campaign_id: str
    campaign_name: str
    status: str
    progress_pct: float = 0.0
    highlight: str = ""


class CampaignPhaseUpdate(BaseModel):
    new_phase: str


class CampaignMetricsUpdate(BaseModel):
    metrics: Dict[str, float]


# ═══════════════════════════════════════════════════════════════
# Task Models
# ═══════════════════════════════════════════════════════════════

class TaskNote(BaseModel):
    author: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Task(MythosBaseModel):
    id: str
    campaign_id: Optional[str] = None
    assigned_to: str
    assigned_by: str
    title: str
    description: str = ""
    status: str = "pending"  # pending, in_progress, review, completed, blocked
    priority: str = "medium"  # low, medium, high, urgent
    due_date: Optional[datetime] = None
    dependencies: List[str] = []
    deliverable: Optional[str] = None
    deliverable_type: Optional[str] = None
    notes: List[TaskNote] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    campaign_id: Optional[str] = None
    assigned_to: str
    assigned_by: str = "jon"
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None
    dependencies: List[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    deliverable: Optional[str] = None
    deliverable_type: Optional[str] = None


class TaskAssignment(BaseModel):
    task_id: str
    agent_id: str


# ═══════════════════════════════════════════════════════════════
# Message Models
# ═══════════════════════════════════════════════════════════════

class Message(MythosBaseModel):
    id: str
    from_agent: str
    to_agent: str
    content: str
    timestamp: datetime
    message_type: str = "chat"  # chat, task, report, alert, decision
    metadata: Dict[str, Any] = {}
    read: bool = False
    campaign_id: Optional[str] = None


class MessageCreate(BaseModel):
    from_agent: str
    to_agent: str
    content: str
    message_type: str = "chat"
    metadata: Dict[str, Any] = {}
    campaign_id: Optional[str] = None


class MessageSendRequest(BaseModel):
    to_agent: str
    content: str
    message_type: str = "chat"
    campaign_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Daily Report Models
# ═══════════════════════════════════════════════════════════════

class DailyReport(MythosBaseModel):
    id: str
    date: str  # ISO date YYYY-MM-DD
    summary: str
    agent_updates: List[AgentUpdateEntry] = []
    campaigns_status: List[CampaignStatusEntry] = []
    decisions_made: List[str] = []
    issues_flags: List[str] = []
    tomorrow_priorities: List[str] = []
    owner_attention_required: List[str] = []
    sentiment: str = "neutral"  # positive, neutral, concern
    sent_via_whatsapp: bool = False
    whatsapp_message_sid: Optional[str] = None
    owner_replies: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None


class DailyReportRequest(BaseModel):
    date: Optional[str] = None  # defaults to today


class OwnerReply(BaseModel):
    reply_text: str


# ═══════════════════════════════════════════════════════════════
# Regional Intelligence Models
# ═══════════════════════════════════════════════════════════════

class PlatformInsight(BaseModel):
    platform: str
    popularity: str  # high, medium, low
    user_demo: str
    content_formats: List[str]
    best_practices: List[str]
    avg_engagement: str


class CulturalCTA(BaseModel):
    text: str
    context: str
    effectiveness: str


class Persona(BaseModel):
    name: str
    age_range: str
    interests: List[str]
    pain_points: List[str]
    platforms: List[str]
    content_preferences: List[str]
    purchase_behavior: str


class RegionalProfile(MythosBaseModel):
    region: str
    culture_notes: str
    language_primary: str
    languages_secondary: List[str] = []
    social_platforms: List[PlatformInsight] = []
    best_posting_times: Dict[str, List[str]] = {}
    ctas_by_culture: List[CulturalCTA] = []
    audience_personas: List[Persona] = []
    content_themes: List[str] = []
    taboos: List[str] = []
    local_trends: List[str] = []
    competitor_landscape: str


class PostingTimeRequest(BaseModel):
    platform: str
    content_type: str = "general"


# ═══════════════════════════════════════════════════════════════
# Scheduled Post Models
# ═══════════════════════════════════════════════════════════════

class ScheduledPost(MythosBaseModel):
    id: str
    campaign_id: str
    platform: str
    content_type: str
    content_text: str = ""
    media_urls: List[str] = []
    scheduled_time: datetime
    timezone: str = "UTC"
    status: str = "scheduled"
    posted_at: Optional[datetime] = None
    engagement_estimate: float = 0.0
    metadata: Dict[str, Any] = {}


class ScheduledPostCreate(BaseModel):
    campaign_id: str
    platform: str
    content_type: str = "general"
    content_text: str = ""
    media_urls: List[str] = []
    scheduled_time: datetime
    timezone: str = "UTC"


# ═══════════════════════════════════════════════════════════════
# Dashboard Models
# ═══════════════════════════════════════════════════════════════

class DashboardStats(MythosBaseModel):
    total_agents: int = 23
    active_agents: int = 0
    busy_agents: int = 0
    offline_agents: int = 0
    total_campaigns: int = 0
    campaigns_by_status: Dict[str, int] = {}
    active_campaigns: int = 0
    total_clients: int = 0
    tasks_today: int = 0
    tasks_completed_today: int = 0
    pending_tasks: int = 0
    urgent_tasks: int = 0
    messages_today: int = 0
    last_report_date: Optional[str] = None
    report_sent: bool = False


class ActivityFeedItem(MythosBaseModel):
    id: str
    actor: str
    actor_avatar: str
    action: str
    target: str
    target_type: str
    timestamp: datetime
    details: Dict[str, Any] = {}


class WorkloadItem(BaseModel):
    agent_id: str
    agent_name: str
    agent_avatar: str
    role: str
    status: str
    tasks_assigned: int = 0
    tasks_in_progress: int = 0
    tasks_completed: int = 0
    current_task_title: Optional[str] = None
    utilization_pct: float = 0.0


# ═══════════════════════════════════════════════════════════════
# WhatsApp / Webhook Models
# ═══════════════════════════════════════════════════════════════

class WhatsAppIncoming(BaseModel):
    From: str
    To: str
    Body: str
    MessageSid: str = ""
    NumMedia: int = 0
    MediaUrl0: Optional[str] = None


class WhatsAppOutgoing(BaseModel):
    to_number: str
    body: str


class WhatsAppStatus(BaseModel):
    MessageSid: str
    MessageStatus: str
    To: str


# ═══════════════════════════════════════════════════════════════
# CEO / Owner Communication Models
# ═══════════════════════════════════════════════════════════════

class CEOMessageRequest(BaseModel):
    message: str


class CEOMessageResponse(BaseModel):
    response: str
    actions_taken: List[str] = []


class CEOInboxEntry(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    content: str
    timestamp: datetime
    message_type: str
    read: bool


# ═══════════════════════════════════════════════════════════════
# Content Calendar Models
# ═══════════════════════════════════════════════════════════════

class ContentCalendarRequest(BaseModel):
    campaign_id: str
    days: int = 30


class ContentCalendarResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    posts: List[ScheduledPost] = []
    total_posts: int = 0
    platforms: List[str] = []


# ═══════════════════════════════════════════════════════════════
# Campaign Engine Models
# ═══════════════════════════════════════════════════════════════

class CampaignWorkflowResult(BaseModel):
    campaign_id: str
    tasks_created: int
    agents_assigned: List[str]
    estimated_duration_days: int
    phases: List[str]


class CampaignReport(MythosBaseModel):
    campaign_id: str
    campaign_name: str
    status: str
    metrics_summary: Dict[str, float]
    agent_contributions: List[Dict[str, Any]]
    deliverables_status: List[Deliverable]
    roi_estimate: float
    recommendations: List[str]
    generated_at: datetime


# ═══════════════════════════════════════════════════════════════
# Health / System Models
# ═══════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    llm_provider: str
    llm_available: bool
    whatsapp_configured: bool
    database_connected: bool
    agent_count: int
    environment: str


class LLMTestResponse(BaseModel):
    provider: str
    model: str
    response: str
    latency_ms: float
    tokens_used: int


# ═══════════════════════════════════════════════════════════════
# Billing Models
# ═══════════════════════════════════════════════════════════════

class CheckoutSessionRequest(BaseModel):
    """Request to create a Stripe Checkout session."""
    client_id: str
    package_id: str  # starter, growth, enterprise
    billing_cycle: str = "monthly"  # monthly, annual
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Response with Stripe Checkout session details."""
    checkout_session_id: Optional[str] = None
    checkout_url: Optional[str] = None
    client_id: str
    package_id: str
    package_name: str
    billing_cycle: str
    trial_days: int = 0
    error: Optional[str] = None


class SubscriptionStatus(BaseModel):
    """Client subscription status."""
    client_id: str
    client_name: str
    status: str  # active, trialing, past_due, canceled, inactive
    package_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_status: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    trial_end: Optional[str] = None
    cancel_at_period_end: bool = False


class InvoiceRequest(BaseModel):
    """Request to create a one-off invoice."""
    client_id: str
    items: List[Dict[str, Any]]
    description: str = ""


class InvoiceResponse(BaseModel):
    """Invoice creation response."""
    status: str
    invoice_id: Optional[str] = None
    total: float = 0.0
    invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None


class RevenueMetrics(BaseModel):
    """Revenue dashboard metrics."""
    mrr: float
    arr: float
    active_subscriptions: int
    past_due: int
    canceled_last_30d: int
    trialing: int
    total_clients: int
    at_risk_clients: int
    churn_rate_pct: float
    avg_revenue_per_client: float
    package_breakdown: Dict[str, Any]
    projected_arr_with_expansion: float
    calculated_at: str


class BillingPortalRequest(BaseModel):
    """Request to create a billing portal session."""
    client_id: str
    return_url: str


class BillingPortalResponse(BaseModel):
    """Billing portal session response."""
    portal_session_id: Optional[str] = None
    portal_url: Optional[str] = None
    error: Optional[str] = None


class UsageTrackingEntry(BaseModel):
    """A single usage tracking entry."""
    id: str
    client_id: str
    agent_id: str
    task_type: str
    timestamp: str


# ═══════════════════════════════════════════════════════════════
# Onboarding Models
# ═══════════════════════════════════════════════════════════════

class OnboardingStepData(BaseModel):
    """Data for any onboarding step."""
    step_number: int
    data: Dict[str, Any]


class OnboardingProgress(BaseModel):
    """Current onboarding progress."""
    session_id: str
    current_step: int
    completed_steps: List[int]
    total_steps: int = 5
    status: str  # in_progress, completed, expired
    step_data_summary: Dict[str, List[str]]
    is_complete: bool
    created_at: str
    updated_at: str


class OnboardingCompleteResponse(BaseModel):
    """Response when onboarding is completed."""
    success: bool
    client_id: Optional[str] = None
    subscription_id: Optional[str] = None
    package_id: Optional[str] = None
    assigned_agents: List[Dict[str, Any]] = []
    agent_count: int = 0
    client_brief_summary: str = ""
    next_steps: List[str] = []
    error: Optional[str] = None


class ClientBrief(BaseModel):
    """Compiled client brief from onboarding data."""
    brief_id: str
    generated_at: str
    executive_summary: str
    company_profile: Dict[str, Any]
    marketing_goals: Dict[str, Any]
    market_profile: Dict[str, Any]
    brand_voice: Dict[str, Any]
    selected_package: Dict[str, Any]
    recommended_first_campaigns: List[Dict[str, str]]
    team_assigned: List[Dict[str, str]]


# ═══════════════════════════════════════════════════════════════
# Service Catalog Models
# ═══════════════════════════════════════════════════════════════

class ServiceItem(BaseModel):
    """A single service in the catalog."""
    service_id: str
    name: str
    agent: str
    agent_name: str
    category: str
    description: str
    deliverables: List[str]
    base_price: int
    tier: str


class PackageItem(BaseModel):
    """A subscription package."""
    id: str
    name: str
    tagline: str
    description: str
    price_monthly: int
    price_annual: int
    annual_discount_pct: int
    campaigns: int
    service_count: int
    agent_count: int
    features: List[str]
    not_included: List[str]
    ideal_for: List[str]


class QuoteRequest(BaseModel):
    """Request to generate a custom quote."""
    goals: List[str] = []
    industry: str = ""
    company_size: str = "small"  # startup, small, medium, enterprise
    annual_revenue: str = ""
    budget_range: str = ""
    needs_paid_ads: bool = False
    needs_landing_pages: bool = False
    needs_email: bool = False
    needs_video: bool = False
    needs_influencer: bool = False
    needs_pr: bool = False
    needs_growth: bool = False
    campaign_count: int = 1
    regions: List[str] = []
    timeline: str = "standard"  # urgent, standard, relaxed


class QuoteResponse(BaseModel):
    """Generated quote response."""
    quote_id: str
    generated_at: str
    recommended_package: Dict[str, Any]
    score_breakdown: Dict[str, int]
    recommendation_reasons: List[str]
    recommended_addons: List[Dict[str, Any]]
    pricing: Dict[str, Any]
    value_metrics: Dict[str, Any]
    alternative_packages: List[Dict[str, Any]]
    custom_package_available: bool
    note: str


class CustomPackageRequest(BaseModel):
    """Request to build a custom package."""
    service_ids: List[str]
    addon_selections: Dict[str, List[str]] = {}


# ═══════════════════════════════════════════════════════════════
# Public API Models
# ═══════════════════════════════════════════════════════════════

class ContactFormSubmission(BaseModel):
    """Public contact form submission."""
    name: str
    email: str
    company: str = ""
    message: str
    budget_range: str = ""
    service_interest: str = ""


class PublicAgentProfile(BaseModel):
    """Limited public profile for an agent."""
    id: str
    name: str
    full_name: str
    role: str
    title: str
    description: str
    avatar: str
    skills: List[str] = []
    category: str = ""
