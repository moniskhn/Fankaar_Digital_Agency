"""
AgentRuntime -- Autonomous Worker Loop
Makes all 23 AI employees self-running. Continuously processes tasks,
generates deliverables via LLM, manages campaign phase transitions,
and handles inter-agent handoffs without human intervention.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.agents.jon_ceo import JonCEO
from app.agents.registry import get_agent, get_all_agents
from app.core.config import settings
from app.core.database import (
    ActivityLogModel,
    CampaignModel,
    ClientModel,
    MessageModel,
    RegionalProfileModel,
    ReportModel,
    SessionLocal,
    TaskModel,
)
from app.core.models import Deliverable
from app.core.orchestrator import CampaignWorkflowBuilder, InterAgentMessaging, TaskRouter

logger = logging.getLogger(__name__)

# ── Phase transition map ─────────────────────────────────────────

_PHASE_TRANSITIONS: Dict[str, str] = {
    "brief": "strategy",
    "strategy": "creation",
    "creation": "review",
    "review": "approval",
    "approval": "live",
    "live": "reporting",
    "reporting": "completed",
}

# ── Phase task templates for auto-generation ─────────────────────

_PHASE_TASKS_TEMPLATE: Dict[str, List[Dict[str, Any]]] = {
    "strategy": [
        {
            "agent_id": "arya",
            "title_template": "Market research for {campaign_name}",
            "desc_template": (
                "Research {region} market, competitors, and audience for campaign. "
                "Channels: {channels}. Brief: {brief_summary}"
            ),
            "priority": "high",
            "due_days": 3,
        },
        {
            "agent_id": "bran",
            "title_template": "Strategic plan for {campaign_name}",
            "desc_template": (
                "Develop comprehensive campaign strategy including positioning, "
                "messaging framework, channel strategy, KPIs, and growth plan for {region}. "
                "Build upon Arya's research findings."
            ),
            "priority": "high",
            "due_days": 5,
        },
    ],
    "creation": [
        {
            "agent_id": "tyrion",
            "title_template": "Copy and content for {campaign_name}",
            "desc_template": (
                "Write ALL campaign copy: primary headlines (at least 5 variants), "
                "body copy for each channel ({channels}), CTAs, social captions (10+), "
                "email subject lines (5+), ad headlines (8+). "
                "Region: {region}. Align with Bran's strategy."
            ),
            "priority": "high",
            "due_days": 5,
        },
        {
            "agent_id": "rhaegar",
            "title_template": "Creative direction for {campaign_name}",
            "desc_template": (
                "Create comprehensive creative direction: color palette with hex codes, "
                "typography recommendations, layout descriptions for each channel ({channels}), "
                "asset specifications, mood board description. "
                "Brand voice: {brand_voice}. Region: {region}."
            ),
            "priority": "high",
            "due_days": 5,
        },
        {
            "agent_id": "missandei",
            "title_template": "Social content calendar for {campaign_name}",
            "desc_template": (
                "Create detailed social media content plan for {channels} targeting {region}. "
                "Include 30 days of post topics, captions, hashtags, optimal posting times, "
                "and engagement strategy. Build on Tyrion's copy."
            ),
            "priority": "medium",
            "due_days": 4,
        },
        {
            "agent_id": "bronn",
            "title_template": "Ad campaign setup for {campaign_name}",
            "desc_template": (
                "Design paid advertising strategy: audience targeting specs, "
                "budget allocation across channels, bidding strategy, "
                "ad creative concepts, A/B test plan. Region: {region}."
            ),
            "priority": "high",
            "due_days": 4,
        },
        {
            "agent_id": "margaery",
            "title_template": "Email campaign sequence for {campaign_name}",
            "desc_template": (
                "Design email marketing sequence: welcome flow, nurture sequence (5+ emails), "
                "promotional emails, subject lines, automation triggers, segmentation strategy."
            ),
            "priority": "medium",
            "due_days": 4,
        },
        {
            "agent_id": "greyworm",
            "title_template": "Landing page and CRO plan for {campaign_name}",
            "desc_template": (
                "Design conversion-focused landing page: wireframe description, "
                "key sections, CRO recommendations, A/B test plan, "
                "form optimization, mobile considerations."
            ),
            "priority": "high",
            "due_days": 5,
        },
        {
            "agent_id": "gendry",
            "title_template": "Technical implementation for {campaign_name}",
            "desc_template": (
                "Technical setup plan: tracking implementation, pixel configuration, "
                "landing page tech stack, API integrations, analytics setup, "
                "automation workflows for {channels}."
            ),
            "priority": "high",
            "due_days": 5,
        },
        {
            "agent_id": "sandoq",
            "title_template": "SEO strategy for {campaign_name}",
            "desc_template": (
                "Comprehensive SEO plan: keyword research (50+ keywords), "
                "on-page optimization checklist, technical SEO audit items, "
                "content optimization strategy, schema markup recommendations. Region: {region}."
            ),
            "priority": "medium",
            "due_days": 4,
        },
    ],
    "review": [
        {
            "agent_id": "brienne",
            "title_template": "QA review for {campaign_name}",
            "desc_template": (
                "Quality assurance review of ALL deliverables. "
                "Check against brief requirements, brand guidelines, completeness, "
                "accuracy, and quality standards. Provide pass/fail for each deliverable "
                "with specific feedback."
            ),
            "priority": "high",
            "due_days": 2,
        },
        {
            "agent_id": "stannis",
            "title_template": "Legal and compliance review for {campaign_name}",
            "desc_template": (
                "Review all campaign materials for legal compliance, IP clearance, "
                "regulatory requirements in {region}, advertising standards, "
                "data privacy compliance, and risk assessment."
            ),
            "priority": "high",
            "due_days": 2,
        },
    ],
    "reporting": [
        {
            "agent_id": "samwell",
            "title_template": "Performance analysis for {campaign_name}",
            "desc_template": (
                "Comprehensive performance analysis: KPI tracking, metric analysis, "
                "trend identification, insights, anomalies, recommendations. "
                "Campaign channels: {channels}."
            ),
            "priority": "high",
            "due_days": 3,
        },
        {
            "agent_id": "petyr",
            "title_template": "Campaign report for {campaign_name}",
            "desc_template": (
                "Create final campaign report: executive summary, results vs objectives, "
                "ROI analysis, key learnings, recommendations for future campaigns, "
                "data visualizations description."
            ),
            "priority": "medium",
            "due_days": 3,
        },
        {
            "agent_id": "tywin",
            "title_template": "Financial review for {campaign_name}",
            "desc_template": (
                "Financial analysis: budget vs actual spend, ROI calculation, "
                "cost per acquisition by channel, profitability analysis, "
                "invoice reconciliation, financial recommendations."
            ),
            "priority": "medium",
            "due_days": 3,
        },
    ],
}

# ── Agent-specific deliverable type hints ────────────────────────

_AGENT_DELIVERABLE_TYPES: Dict[str, str] = {
    "tyrion": "text",
    "rhaegar": "document",
    "sandoq": "document",
    "arya": "document",
    "bran": "document",
    "missandei": "text",
    "bronn": "document",
    "samwell": "document",
    "margaery": "text",
    "greyworm": "document",
    "sandor": "text",
    "sansa": "text",
    "tywin": "document",
    "stannis": "document",
    "brienne": "document",
    "gendry": "document",
    "petyr": "document",
    "cersei": "document",
    "davos": "text",
    "jorah": "document",
    "olenna": "document",
    "podrick": "text",
    "jon": "text",
}

# ── Agent-specific execution context customizers ─────────────────

_AGENT_EXECUTION_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "tyrion": {
        "temperature": 0.8,
        "extra_context": (
            "\n\nWRITING REQUIREMENTS:\n"
            "- Provide at least 5 headline variants for each major piece\n"
            "- Write complete body copy, not outlines or summaries\n"
            "- Include specific CTAs tailored to the region and audience\n"
            "- Adapt tone for each channel (social, email, ads, landing page)\n"
            "- Include word counts and character counts where relevant\n"
            "- All copy must be ready to publish without further editing\n"
        ),
    },
    "rhaegar": {
        "temperature": 0.75,
        "extra_context": (
            "\n\nDESIGN REQUIREMENTS:\n"
            "- Specify exact hex color codes for the palette\n"
            "- Recommend specific font families with fallbacks\n"
            "- Describe layouts in enough detail for a designer to execute\n"
            "- Include image/illustration style direction\n"
            "- Specify sizes and formats for each channel\n"
            "- Provide a cohesive visual system, not one-off designs\n"
        ),
    },
    "sandoq": {
        "temperature": 0.5,
        "extra_context": (
            "\n\nSEO REQUIREMENTS:\n"
            "- Provide 50+ keywords organized by intent (informational, navigational, transactional)\n"
            "- Include search volume estimates and difficulty scores\n"
            "- List specific on-page optimization actions\n"
            "- Include technical SEO checklist items\n"
            "- Provide schema markup recommendations\n"
            "- Format as structured data where possible\n"
        ),
    },
    "arya": {
        "temperature": 0.6,
        "extra_context": (
            "\n\nRESEARCH REQUIREMENTS:\n"
            "- Cite specific data points and sources where possible\n"
            "- Include competitor analysis with specific names\n"
            "- Profile the target audience with demographics and psychographics\n"
            "- Identify market gaps and opportunities\n"
            "- Include regional/cultural considerations\n"
            "- Format findings for easy consumption by the strategy team\n"
        ),
    },
    "bran": {
        "temperature": 0.6,
        "extra_context": (
            "\n\nSTRATEGY REQUIREMENTS:\n"
            "- Include clear positioning statement\n"
            "- Define 3-5 specific, measurable KPIs\n"
            "- Provide channel strategy with budget allocation rationale\n"
            "- Include messaging framework (key messages, proof points, tone)\n"
            "- Identify risks and mitigation strategies\n"
            "- Make all recommendations actionable and specific\n"
        ),
    },
    "missandei": {
        "temperature": 0.75,
        "extra_context": (
            "\n\nSOCIAL MEDIA REQUIREMENTS:\n"
            "- Provide 30 days of specific post topics and captions\n"
            "- Include hashtag strategy (branded, community, trending)\n"
            "- Specify optimal posting times for each platform\n"
            "- Include engagement tactics (polls, questions, UGC prompts)\n"
            "- Plan for stories/reels and static posts\n"
            "- All captions should be ready to post\n"
        ),
    },
    "bronn": {
        "temperature": 0.7,
        "extra_context": (
            "\n\nADVERTISING REQUIREMENTS:\n"
            "- Provide at least 8 ad headline variants\n"
            "- Specify detailed audience targeting (demographics, interests, behaviors)\n"
            "- Include budget allocation across channels and campaigns\n"
            "- Design A/B testing framework\n"
            "- Specify bidding strategy and rationale\n"
            "- Include projected CPM, CPC, and CPA estimates\n"
        ),
    },
    "samwell": {
        "temperature": 0.4,
        "extra_context": (
            "\n\nANALYTICS REQUIREMENTS:\n"
            "- Use specific numbers and metrics throughout\n"
            "- Identify trends with supporting data\n"
            "- Flag any anomalies with potential explanations\n"
            "- Provide actionable recommendations prioritized by impact\n"
            "- Include benchmark comparisons where available\n"
            "- Structure for both executive summary and detailed review\n"
        ),
    },
    "margaery": {
        "temperature": 0.75,
        "extra_context": (
            "\n\nEMAIL REQUIREMENTS:\n"
            "- Write complete email copy for each email in the sequence\n"
            "- Provide 5+ subject line variants with A/B test plan\n"
            "- Include preview text for each email\n"
            "- Design automation triggers and flow logic\n"
            "- Specify segmentation strategy and personalization fields\n"
            "- Include timing and cadence recommendations\n"
        ),
    },
    "greyworm": {
        "temperature": 0.5,
        "extra_context": (
            "\n\nLANDING PAGE REQUIREMENTS:\n"
            "- Describe each section of the landing page in detail\n"
            "- Specify CTA placement, copy, and design\n"
            "- Include form fields and optimization strategy\n"
            "- Design A/B test plan with specific variants\n"
            "- Address mobile responsiveness considerations\n"
            "- Include page speed optimization recommendations\n"
        ),
    },
    "sandor": {
        "temperature": 0.7,
        "extra_context": (
            "\n\nSALES REQUIREMENTS:\n"
            "- Write complete sales scripts, not outlines\n"
            "- Include objection handling for common scenarios\n"
            "- Specify lead qualification criteria and scoring\n"
            "- Provide proposal template with pricing guidance\n"
            "- Include follow-up sequences\n"
            "- All materials should be ready for immediate use\n"
        ),
    },
    "sansa": {
        "temperature": 0.7,
        "extra_context": (
            "\n\nPR REQUIREMENTS:\n"
            "- Write complete press releases, not outlines\n"
            "- Include media kit descriptions\n"
            "- Provide crisis communication templates\n"
            "- Specify target media outlets and pitching strategy\n"
            "- Include key messaging framework\n"
            "- All materials should be publication-ready\n"
        ),
    },
    "tywin": {
        "temperature": 0.4,
        "extra_context": (
            "\n\nFINANCE REQUIREMENTS:\n"
            "- Show all calculations with clear methodology\n"
            "- Include conservative, expected, and optimistic scenarios\n"
            "- Provide month-by-month cash flow projections\n"
            "- Calculate ROI, ROAS, and margin for each channel\n"
            "- Include risk-adjusted recommendations\n"
            "- All numbers must be defensible and transparent\n"
        ),
    },
    "stannis": {
        "temperature": 0.4,
        "extra_context": (
            "\n\nLEGAL REQUIREMENTS:\n"
            "- Reference specific regulations by name\n"
            "- Provide checklist format for compliance tracking\n"
            "- Flag any high-risk items clearly\n"
            "- Include recommended contract clauses\n"
            "- Reference relevant case law or precedents where applicable\n"
            "- Be conservative - when in doubt, flag it\n"
        ),
    },
    "brienne": {
        "temperature": 0.5,
        "extra_context": (
            "\n\nOPERATIONS REQUIREMENTS:\n"
            "- Provide detailed project timelines with specific dates\n"
            "- Include QA checklists with pass/fail criteria\n"
            "- Specify resource allocation by person and task\n"
            "- Identify dependencies and critical path\n"
            "- Include risk mitigation plans\n"
            "- Set clear milestones and accountability\n"
        ),
    },
}



class AgentRuntime:
    """
    Autonomous background worker that continuously processes tasks,
    generates deliverables via LLM, manages campaign phase transitions,
    and handles inter-agent handoffs without human intervention.
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._db = SessionLocal
        self._task_router = TaskRouter()
        self._messaging = InterAgentMessaging()
        self._ceo: Optional[JonCEO] = None

        # Statistics
        self._stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "campaigns_advanced": 0,
            "blockers_resolved": 0,
            "messages_sent": 0,
            "started_at": None,
            "last_task_at": None,
            "errors": [],
        }

        # Runtime config
        self._min_interval = 120  # 2 minutes
        self._max_interval = 300  # 5 minutes
        self._blocker_threshold_hours = 24
        self._max_retries = 3

        logger.info("AgentRuntime initialized")

    # ── Lifecycle ──────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background loop (non-blocking)."""
        if self._running:
            logger.warning("AgentRuntime is already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._stats["started_at"] = datetime.utcnow().isoformat()

        # Initialize CEO reference
        try:
            self._ceo = JonCEO()
            logger.info("CEO (Jon) reference loaded")
        except Exception as e:
            logger.warning(f"CEO initialization failed (non-critical): {e}")

        self._task = asyncio.create_task(self._worker_loop())
        logger.info("AgentRuntime started")

    async def stop(self) -> None:
        """Graceful shutdown."""
        if not self._running:
            return

        logger.info("AgentRuntime stopping...")
        self._running = False
        self._shutdown_event.set()

        if self._task and not self._task.done():
            try:
                self._task.cancel()
                await asyncio.wait_for(self._task, timeout=10.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        logger.info("AgentRuntime stopped")

    # ── Main Worker Loop ───────────────────────────────────────────

    async def _worker_loop(self) -> None:
        """Main infinite loop with configurable interval and graceful shutdown."""
        logger.info("Worker loop started")

        while self._running and not self._shutdown_event.is_set():
            try:
                # Process pending tasks
                await self._process_pending_tasks()

                # Handle blockers (stuck tasks)
                await self._handle_blockers()

                # Process inter-agent messages
                await self._process_inter_agent_messages()

                # Check for standup time
                await self._run_standup_if_needed()

            except asyncio.CancelledError:
                logger.info("Worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                self._stats["errors"].append({
                    "time": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "context": "worker_loop",
                })
                # Keep only last 20 errors
                self._stats["errors"] = self._stats["errors"][-20:]

            # Wait with early-exit on shutdown
            try:
                wait_seconds = random.randint(self._min_interval, self._max_interval)
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=wait_seconds,
                )
            except asyncio.TimeoutError:
                pass  # Normal interval timeout, continue loop
            except asyncio.CancelledError:
                break

        logger.info("Worker loop ended")

    # ── Pending Task Processing ────────────────────────────────────

    async def _process_pending_tasks(self) -> None:
        """Fetch and process all pending tasks."""
        db = self._db()
        try:
            # Get pending tasks ordered by priority and due date
            pending = (
                db.query(TaskModel)
                .filter(TaskModel.status.in_(["pending", "in_progress"]))
                .order_by(TaskModel.due_date.asc())
                .limit(10)
                .all()
            )

            if not pending:
                return

            logger.info(f"Processing {len(pending)} pending tasks")

            for task in pending:
                if not self._running:
                    break

                # Check if dependencies are satisfied
                if not await self._dependencies_met(task, db):
                    logger.debug(f"Task {task.id} dependencies not met, skipping")
                    continue

                try:
                    result = await self._execute_task(task)
                    self._stats["tasks_processed"] += 1
                    self._stats["last_task_at"] = datetime.utcnow().isoformat()
                    logger.info(
                        f"Task {task.id} executed successfully ({len(result)} chars)"
                    )
                except Exception as e:
                    self._stats["tasks_failed"] += 1
                    logger.error(f"Task {task.id} execution failed: {e}", exc_info=True)
                    await self._handle_task_failure(task, str(e), db)

                # Brief yield between tasks
                await asyncio.sleep(0.5)

        finally:
            db.close()

    async def _dependencies_met(self, task: TaskModel, db) -> bool:
        """Check if all dependencies for a task are completed."""
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            dep = db.query(TaskModel).filter(TaskModel.id == dep_id).first()
            if not dep:
                continue
            if dep.status != "completed":
                return False
        return True

    # ── Core Task Execution ────────────────────────────────────────

    async def _execute_task(self, task: TaskModel) -> str:
        """
        The heart of the runtime:
        - Load the assigned agent from registry
        - Build full context (system prompt + task + campaign + regional intel)
        - Call agent.think() with the LLM to generate the actual deliverable
        - Parse and store the response
        - Mark task completed
        - Send completion messages to relevant agents
        """
        db = self._db()
        try:
            # 1. Load agent
            agent_config = get_agent(task.assigned_to)
            if not agent_config:
                raise ValueError(f"Agent {task.assigned_to} not found in registry")

            agent = BaseAgent(agent_config)

            # 2. Update task to in_progress
            task.status = "in_progress"
            if not task.started_at:
                task.started_at = datetime.utcnow()
            db.commit()

            # 3. Build full context
            context = await self._build_task_context(task, agent_config, db)

            # 4. Get agent-specific overrides
            overrides = _AGENT_EXECUTION_OVERRIDES.get(task.assigned_to, {})
            temperature = overrides.get("temperature", 0.7)
            extra_context = overrides.get("extra_context", "")

            if extra_context:
                context += extra_context

            # 5. Build the deliverable prompt
            deliverable_prompt = self._build_deliverable_prompt(task, agent_config)

            # 6. Call the LLM via the agent
            logger.info(
                f"Executing task {task.id} with agent {agent_config.id} "
                f"({agent_config.full_name}) via LLM"
            )

            result = await agent.think(
                task=deliverable_prompt,
                context=context,
                temperature=temperature,
            )

            if not result or not result.strip():
                raise ValueError("LLM returned empty response")

            # 7. Store deliverable
            deliverable_type = _AGENT_DELIVERABLE_TYPES.get(
                task.assigned_to, "text"
            )

            task.deliverable = result
            task.deliverable_type = deliverable_type
            task.status = "completed"
            task.completed_at = datetime.utcnow()

            # Also add to campaign deliverables
            if task.campaign_id:
                campaign = (
                    db.query(CampaignModel)
                    .filter(CampaignModel.id == task.campaign_id)
                    .first()
                )
                if campaign and campaign.deliverables is not None:
                    campaign_deliverables = list(campaign.deliverables)
                    campaign_deliverables.append({
                        "id": str(uuid.uuid4()),
                        "name": task.title,
                        "type": deliverable_type,
                        "status": "completed",
                        "content": result[:500],
                        "assigned_to": task.assigned_to,
                        "created_at": datetime.utcnow().isoformat(),
                        "completed_at": datetime.utcnow().isoformat(),
                    })
                    campaign.deliverables = campaign_deliverables

            db.commit()

            # 8. Log activity
            agent.memory.log_activity(
                action="task_completed",
                target_type="task",
                target_id=task.id,
                details={
                    "task_title": task.title,
                    "campaign_id": task.campaign_id,
                    "result_length": len(result),
                    "deliverable_type": deliverable_type,
                },
            )

            # 9. Send completion message
            await self._send_completion_messages(task, agent_config, result, db)

            # 10. Check if campaign phase should advance
            if task.campaign_id:
                await self._advance_campaign_phase(task.campaign_id)

            return result

        finally:
            db.close()

    # ── Context Building ───────────────────────────────────────────

    async def _build_task_context(
        self,
        task: TaskModel,
        agent_config,
        db,
    ) -> str:
        """Build comprehensive context for the LLM call."""
        parts = []

        # Agent identity
        parts.append(
            f"You are {agent_config.full_name}, {agent_config.title} at Claude Mythos."
        )

        # Campaign context
        campaign_name = "Unknown Campaign"
        client_name = "Unknown Client"
        region = "Unknown"
        channels: List[str] = []
        objectives: List[str] = []
        brand_voice = ""
        brief_summary = ""

        if task.campaign_id:
            campaign = (
                db.query(CampaignModel)
                .filter(CampaignModel.id == task.campaign_id)
                .first()
            )
            if campaign:
                campaign_name = campaign.name
                region = campaign.region
                channels = campaign.channels or []
                objectives = campaign.objectives or []
                brief_summary = campaign.brief_summary or ""

                client = (
                    db.query(ClientModel)
                    .filter(ClientModel.id == campaign.client_id)
                    .first()
                )
                if client:
                    client_name = client.name
                    brand_voice = client.brand_voice or ""

                parts.append(
                    f"\nCAMPAIGN CONTEXT:\n"
                    f"Name: {campaign_name}\n"
                    f"Client: {client_name}\n"
                    f"Region: {region}\n"
                    f"Channels: {', '.join(channels) if channels else 'TBD'}\n"
                    f"Objectives: {', '.join(objectives) if objectives else 'TBD'}\n"
                    f"Brand Voice: {brand_voice or 'Not specified'}\n"
                )

        # Regional intelligence
        regional_context = await self._get_regional_context(region, db)
        if regional_context:
            parts.append(f"\nREGIONAL CONTEXT:\n{regional_context}")

        # Dependencies (completed work to build on)
        dependency_context = await self._get_dependency_context(task, db)
        if dependency_context:
            parts.append(
                f"\nDEPENDENCIES (completed work you can build on):\n"
                f"{dependency_context}"
            )

        # Deliverable format instruction
        parts.append(
            "\nDELIVERABLE FORMAT:\n"
            "Provide your complete, professional deliverable. Be thorough and specific. "
            "This is real client work -- not a summary or outline. Full output. "
            "Do not hold back -- write everything needed for this to be production-ready."
        )

        return "\n".join(parts)

    async def _get_regional_context(self, region: str, db) -> str:
        """Get regional intelligence for a region."""
        try:
            profile = (
                db.query(RegionalProfileModel)
                .filter(RegionalProfileModel.region == region)
                .first()
            )
            if not profile:
                return ""

            lines = []
            if profile.culture_notes:
                lines.append(f"Culture: {profile.culture_notes[:300]}")
            if profile.language_primary:
                lines.append(f"Primary Language: {profile.language_primary}")
            if profile.local_trends:
                trends = profile.local_trends
                if isinstance(trends, list) and trends:
                    lines.append(
                        f"Local Trends: {', '.join(str(t) for t in trends[:5])}"
                    )
            if profile.content_themes:
                themes = profile.content_themes
                if isinstance(themes, list) and themes:
                    lines.append(
                        f"Content Themes: {', '.join(str(t) for t in themes[:5])}"
                    )
            if profile.taboos:
                taboos = profile.taboos
                if isinstance(taboos, list) and taboos:
                    lines.append(
                        f"Cultural Taboos: {', '.join(str(t) for t in taboos[:5])}"
                    )
            if profile.best_posting_times:
                times = profile.best_posting_times
                if isinstance(times, dict):
                    for platform, time_list in list(times.items())[:3]:
                        if isinstance(time_list, list):
                            lines.append(
                                f"{platform} best times: {', '.join(str(t) for t in time_list[:3])}"
                            )
            if profile.competitor_landscape:
                lines.append(f"Competitor Landscape: {profile.competitor_landscape[:300]}")

            return "\n".join(lines) if lines else ""
        except Exception as e:
            logger.warning(f"Failed to load regional context for {region}: {e}")
            return ""

    async def _get_dependency_context(self, task: TaskModel, db) -> str:
        """Get deliverables from completed dependency tasks."""
        if not task.dependencies:
            return ""

        lines = []
        for dep_id in task.dependencies:
            dep = db.query(TaskModel).filter(TaskModel.id == dep_id).first()
            if dep and dep.status == "completed" and dep.deliverable:
                agent_name = dep.assigned_to
                try:
                    from app.agents.registry import get_agent as _get_agent
                    dep_agent = _get_agent(dep.assigned_to)
                    if dep_agent:
                        agent_name = dep_agent.full_name
                except Exception:
                    pass

                lines.append(
                    f"--- From {agent_name} ({dep.title}) ---\n"
                    f"{dep.deliverable[:2000]}"
                )

        return "\n\n".join(lines) if lines else ""

    def _build_deliverable_prompt(self, task: TaskModel, agent_config) -> str:
        """Build the primary task prompt for the LLM."""
        parts = []

        parts.append(f"TASK: {task.title}")
        parts.append(f"\nDESCRIPTION: {task.description}")
        parts.append(f"PRIORITY: {task.priority}")

        if task.due_date:
            parts.append(f"DUE: {task.due_date.isoformat()}")

        parts.append(
            f"\nYou are {agent_config.full_name}, {agent_config.title}. "
            f"Produce your complete, professional deliverable now."
        )

        return "\n".join(parts)

    # ── Completion Messages ────────────────────────────────────────

    async def _send_completion_messages(
        self,
        task: TaskModel,
        agent_config,
        result: str,
        db,
    ) -> None:
        """Send inter-agent messages about task completion."""
        try:
            # Notify the task assigner
            if task.assigned_by and task.assigned_by != task.assigned_to:
                msg = (
                    f"Task completed by {agent_config.avatar} {agent_config.full_name}: "
                    f"'{task.title}' ({len(result)} chars of deliverable produced)"
                )
                await self._messaging.send_message(
                    from_agent=task.assigned_to,
                    to_agent=task.assigned_by,
                    content=msg,
                    message_type="task",
                    campaign_id=task.campaign_id,
                    metadata={
                        "task_id": task.id,
                        "status": "completed",
                        "deliverable_length": len(result),
                    },
                )
                self._stats["messages_sent"] += 1

            # Find next agents in the pipeline and notify them
            next_agents = self._find_next_agents_in_pipeline(task, db)
            for next_agent_id in next_agents:
                if next_agent_id == task.assigned_to:
                    continue
                try:
                    from app.agents.registry import get_agent as _get_agent
                    next_agent = _get_agent(next_agent_id)
                    if next_agent:
                        msg = (
                            f"{agent_config.avatar} {agent_config.full_name} has completed "
                            f"'{task.title}'. Your task dependencies are now satisfied -- "
                            f"you can begin your work on the campaign."
                        )
                        await self._messaging.send_message(
                            from_agent=task.assigned_to,
                            to_agent=next_agent_id,
                            content=msg,
                            message_type="task",
                            campaign_id=task.campaign_id,
                            metadata={
                                "completed_task_id": task.id,
                                "completed_by": task.assigned_to,
                            },
                        )
                        self._stats["messages_sent"] += 1
                except Exception:
                    pass

            # Broadcast significant completions
            if task.priority in ("high", "urgent"):
                try:
                    await self._messaging.broadcast(
                        from_agent=task.assigned_to,
                        content=(
                            f"{agent_config.avatar} {agent_config.full_name} completed "
                            f"a {task.priority}-priority task: '{task.title}'"
                        ),
                        message_type="alert",
                        metadata={
                            "task_id": task.id,
                            "campaign_id": task.campaign_id,
                            "priority": task.priority,
                        },
                    )
                    self._stats["messages_sent"] += 1
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to send completion messages: {e}")

    def _find_next_agents_in_pipeline(self, task: TaskModel, db) -> List[str]:
        """Find agents who have tasks depending on this task's completion."""
        next_agents = []
        try:
            dependent_tasks = (
                db.query(TaskModel)
                .filter(TaskModel.campaign_id == task.campaign_id)
                .all()
            )
            for t in dependent_tasks:
                deps = t.dependencies or []
                if isinstance(deps, list) and task.id in deps:
                    if t.assigned_to not in next_agents:
                        next_agents.append(t.assigned_to)
        except Exception:
            pass
        return next_agents


    # ── Campaign Phase Advancement ─────────────────────────────────

    async def _advance_campaign_phase(self, campaign_id: str) -> None:
        """Check if all tasks in the current phase are complete -- if so, advance."""
        db = self._db()
        try:
            campaign = (
                db.query(CampaignModel)
                .filter(CampaignModel.id == campaign_id)
                .first()
            )
            if not campaign:
                return

            current_phase = campaign.status

            # Get all tasks for this campaign
            tasks = (
                db.query(TaskModel)
                .filter(TaskModel.campaign_id == campaign_id)
                .all()
            )

            if not tasks:
                return

            # Check if all tasks are completed
            active_tasks = [
                t for t in tasks
                if t.status in ["pending", "in_progress", "blocked"]
            ]

            if active_tasks:
                # There are still active tasks -- don't advance
                return

            # All tasks complete -- check if we should advance
            next_phase = _PHASE_TRANSITIONS.get(current_phase)
            if not next_phase:
                return

            # Don't auto-advance past approval -- needs human
            if current_phase == "review":
                next_phase = "approval"
                # Notify owner via CEO
                if self._ceo:
                    try:
                        await self._messaging.send_message(
                            from_agent="jon",
                            to_agent="owner",
                            content=(
                                f"Campaign '{campaign.name}' has completed review phase. "
                                f"All deliverables are ready for your approval. "
                                f"Reply to approve and launch."
                            ),
                            message_type="alert",
                            campaign_id=campaign_id,
                        )
                        self._stats["messages_sent"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to notify owner: {e}")

            # Don't auto-advance out of approval -- needs explicit owner approval
            if current_phase == "approval":
                return

            # Don't auto-advance past live -- needs explicit transition
            if current_phase == "live":
                return

            # Advance the phase
            campaign.status = next_phase
            timeline = dict(campaign.timeline or {})
            timeline[next_phase] = datetime.utcnow().isoformat()
            campaign.timeline = timeline
            db.commit()

            self._stats["campaigns_advanced"] += 1
            logger.info(
                f"Campaign '{campaign.name}' advanced from {current_phase} "
                f"to {next_phase}"
            )

            # Auto-generate next phase tasks
            await self._generate_phase_tasks(campaign, next_phase, db)

            # Notify team
            try:
                await self._messaging.broadcast(
                    from_agent="jon",
                    content=(
                        f"Campaign '{campaign.name}' has advanced to "
                        f"{next_phase.upper()} phase. New tasks have been auto-generated."
                    ),
                    message_type="alert",
                    metadata={
                        "campaign_id": campaign_id,
                        "old_phase": current_phase,
                        "new_phase": next_phase,
                    },
                )
                self._stats["messages_sent"] += 1
            except Exception:
                pass

        finally:
            db.close()

    async def _generate_phase_tasks(
        self,
        campaign: CampaignModel,
        phase: str,
        db,
    ) -> None:
        """Auto-generate tasks for a campaign phase."""
        templates = _PHASE_TASKS_TEMPLATE.get(phase, [])
        if not templates:
            return

        now = datetime.utcnow()
        channels = campaign.channels or []
        region = campaign.region or "Global"
        brief_summary = (campaign.brief_summary or "")[:200]

        # Get client info for brand voice
        brand_voice = ""
        client = (
            db.query(ClientModel)
            .filter(ClientModel.id == campaign.client_id)
            .first()
        )
        if client:
            brand_voice = client.brand_voice or ""

        # Get assigned agents for this campaign
        assigned_agents = campaign.assigned_agents or []

        created_count = 0
        for template in templates:
            agent_id = template["agent_id"]

            # Only create task if agent is on the campaign team
            if agent_id not in assigned_agents:
                continue

            # Check if task already exists for this agent + campaign + phase
            existing = (
                db.query(TaskModel)
                .filter(
                    TaskModel.campaign_id == campaign.id,
                    TaskModel.assigned_to == agent_id,
                )
                .all()
            )
            title_check = template["title_template"].format(
                campaign_name=campaign.name
            )
            if any(e.title == title_check for e in existing):
                continue

            title = template["title_template"].format(campaign_name=campaign.name)
            description = template["desc_template"].format(
                campaign_name=campaign.name,
                region=region,
                channels=", ".join(channels),
                brief_summary=brief_summary,
                brand_voice=brand_voice,
            )

            task = TaskModel(
                id=str(uuid.uuid4()),
                campaign_id=campaign.id,
                assigned_to=agent_id,
                assigned_by="jon",
                title=title,
                description=description,
                status="pending",
                priority=template.get("priority", "medium"),
                due_date=now + timedelta(days=template.get("due_days", 3)),
                dependencies=[],
            )
            db.add(task)
            created_count += 1

        if created_count > 0:
            db.commit()
            logger.info(
                f"Generated {created_count} tasks for campaign '{campaign.name}' "
                f"phase '{phase}'"
            )

    # ── Blocker Handling ───────────────────────────────────────────

    async def _handle_blockers(self) -> None:
        """Detect tasks stuck > threshold hours and reassign or escalate."""
        db = self._db()
        try:
            threshold = datetime.utcnow() - timedelta(
                hours=self._blocker_threshold_hours
            )

            stuck_tasks = (
                db.query(TaskModel)
                .filter(
                    TaskModel.status.in_(["in_progress", "blocked"]),
                    TaskModel.started_at < threshold,
                )
                .all()
            )

            for task in stuck_tasks:
                try:
                    # Count retries from notes
                    notes = task.notes or []
                    retry_count = sum(
                        1 for n in notes
                        if isinstance(n, dict) and "retry" in str(n.get("content", ""))
                    )

                    if retry_count < self._max_retries:
                        # Reset to pending for retry
                        task.status = "pending"
                        task.started_at = None
                        new_note = {
                            "author": "system",
                            "content": (
                                f"retry {retry_count + 1}/{self._max_retries}: "
                                f"Task reset after being stuck for "
                                f"{self._blocker_threshold_hours}h"
                            ),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        notes = list(notes)
                        notes.append(new_note)
                        task.notes = notes
                        db.commit()

                        self._stats["tasks_retried"] += 1
                        logger.info(
                            f"Task {task.id} reset for retry ({retry_count + 1})"
                        )
                    else:
                        # Escalate to CEO
                        task.status = "blocked"
                        db.commit()

                        await self._escalate_to_ceo(task)
                        self._stats["blockers_resolved"] += 1

                except Exception as e:
                    logger.error(
                        f"Error handling blocker for task {task.id}: {e}"
                    )

        finally:
            db.close()

    async def _escalate_to_ceo(self, task: TaskModel) -> None:
        """Escalate a blocked task to the CEO (Jon)."""
        try:
            msg = (
                f"ESCALATION: Task '{task.title}' (assigned to {task.assigned_to}) "
                f"has been blocked after {self._max_retries} retries. "
                f"Task ID: {task.id}. Campaign: {task.campaign_id}. "
                f"Please reassign or resolve."
            )

            await self._messaging.send_message(
                from_agent="system",
                to_agent="jon",
                content=msg,
                message_type="alert",
                campaign_id=task.campaign_id,
                metadata={"task_id": task.id, "escalation": True},
            )
            self._stats["messages_sent"] += 1

            # Also notify via CEO if available
            if self._ceo:
                try:
                    await self._ceo.communicate(
                        to="owner",
                        message=msg,
                        message_type="alert",
                        campaign_id=task.campaign_id,
                    )
                except Exception:
                    pass

            logger.warning(f"Task {task.id} escalated to CEO")
        except Exception as e:
            logger.error(f"Failed to escalate task {task.id}: {e}")

    # ── Standup ────────────────────────────────────────────────────

    async def _run_standup_if_needed(self) -> None:
        """Trigger CEO standup at configured time."""
        try:
            now = datetime.utcnow()
            report_time_str = settings.daily_report_time  # e.g. "09:00"
            report_hour, report_minute = map(int, report_time_str.split(":"))

            # Simple check: if it's within the report minute window
            if now.hour == report_hour and now.minute == report_minute:
                # Check if we already ran standup today
                db = self._db()
                try:
                    today_str = now.strftime("%Y-%m-%d")
                    existing = (
                        db.query(ReportModel)
                        .filter(ReportModel.date == today_str)
                        .first()
                    )
                    if not existing and self._ceo:
                        logger.info("Triggering daily standup")
                        await self._ceo.run_daily_standup()
                finally:
                    db.close()
        except Exception as e:
            logger.warning(f"Standup check failed: {e}")

    # ── Inter-Agent Message Processing ─────────────────────────────

    async def _process_inter_agent_messages(self) -> None:
        """Process pending inter-agent messages and collaboration requests."""
        try:
            messages = await self._messaging.get_messages_for_agent(
                "system", limit=20
            )
            for msg in messages:
                if msg.get("message_type") == "collaboration_request":
                    await self._handle_collaboration_request(msg)
        except Exception as e:
            logger.warning(f"Inter-agent message processing failed: {e}")

    async def _handle_collaboration_request(self, message: Dict[str, Any]) -> None:
        """Handle a collaboration request between agents."""
        try:
            metadata = message.get("metadata", {})
            requesting_agent = message.get("from_agent")
            target_agent = metadata.get("target_agent")
            task_description = metadata.get("task_description", "")

            if not target_agent or not task_description:
                return

            # Create a new task for the target agent
            db = self._db()
            try:
                task = TaskModel(
                    id=str(uuid.uuid4()),
                    campaign_id=metadata.get("campaign_id"),
                    assigned_to=target_agent,
                    assigned_by=requesting_agent,
                    title=f"Collaboration: {task_description[:80]}",
                    description=task_description,
                    status="pending",
                    priority=metadata.get("priority", "medium"),
                )
                db.add(task)
                db.commit()

                # Notify target agent
                await self._messaging.send_message(
                    from_agent=requesting_agent,
                    to_agent=target_agent,
                    content=(
                        f"Collaboration request: {task_description}\n"
                        f"A new task has been created for you."
                    ),
                    message_type="task",
                    campaign_id=metadata.get("campaign_id"),
                    metadata={"task_id": task.id},
                )
                self._stats["messages_sent"] += 1
            finally:
                db.close()

        except Exception as e:
            logger.warning(f"Failed to handle collaboration request: {e}")

    # ── Task Failure Handling ──────────────────────────────────────

    async def _handle_task_failure(
        self,
        task: TaskModel,
        error: str,
        db,
    ) -> None:
        """Handle a failed task execution."""
        try:
            # Count failures
            notes = list(task.notes or [])
            failure_count = sum(
                1 for n in notes
                if isinstance(n, dict)
                and "failure" in str(n.get("content", ""))
            )

            notes.append({
                "author": "system",
                "content": f"failure {failure_count + 1}: {error[:200]}",
                "timestamp": datetime.utcnow().isoformat(),
            })
            task.notes = notes

            if failure_count + 1 >= self._max_retries:
                task.status = "blocked"
                await self._escalate_to_ceo(task)
            else:
                task.status = "pending"
                task.started_at = None

            db.commit()
        except Exception as e:
            logger.error(f"Error in failure handler: {e}")

    # ── Public API ─────────────────────────────────────────────────

    async def execute_task_now(self, task_id: str) -> Dict[str, Any]:
        """Force immediate execution of a specific task (for API)."""
        db = self._db()
        try:
            task = (
                db.query(TaskModel).filter(TaskModel.id == task_id).first()
            )
            if not task:
                return {"success": False, "error": f"Task {task_id} not found"}

            if task.status == "completed":
                return {
                    "success": False,
                    "error": "Task already completed",
                    "deliverable_length": len(task.deliverable) if task.deliverable else 0,
                }

            result = await self._execute_task(task)
            return {
                "success": True,
                "task_id": task_id,
                "result_length": len(result),
                "status": "completed",
                "agent": task.assigned_to,
            }
        except Exception as e:
            logger.error(f"Force execution of task {task_id} failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    async def get_runtime_status(self) -> Dict[str, Any]:
        """Return runtime stats (tasks processed, queue length, uptime)."""
        db = self._db()
        try:
            pending_count = (
                db.query(TaskModel)
                .filter(TaskModel.status.in_(["pending", "in_progress"]))
                .count()
            )

            blocked_count = (
                db.query(TaskModel)
                .filter(TaskModel.status == "blocked")
                .count()
            )

            completed_today = (
                db.query(TaskModel)
                .filter(
                    TaskModel.status == "completed",
                    TaskModel.completed_at
                    >= datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                )
                .count()
            )

            uptime = "N/A"
            if self._stats["started_at"]:
                started = datetime.fromisoformat(self._stats["started_at"])
                delta = datetime.utcnow() - started
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime = f"{hours}h {minutes}m {seconds}s"

            return {
                "running": self._running,
                "tasks_processed": self._stats["tasks_processed"],
                "tasks_failed": self._stats["tasks_failed"],
                "tasks_retried": self._stats["tasks_retried"],
                "campaigns_advanced": self._stats["campaigns_advanced"],
                "blockers_resolved": self._stats["blockers_resolved"],
                "messages_sent": self._stats["messages_sent"],
                "pending_queue_length": pending_count,
                "blocked_tasks": blocked_count,
                "completed_today": completed_today,
                "uptime": uptime,
                "started_at": self._stats["started_at"],
                "last_task_at": self._stats["last_task_at"],
                "recent_errors": self._stats["errors"][-5:],
            }
        finally:
            db.close()

    async def retry_task(self, task_id: str) -> Dict[str, Any]:
        """Retry a failed/blocked task."""
        db = self._db()
        try:
            task = (
                db.query(TaskModel).filter(TaskModel.id == task_id).first()
            )
            if not task:
                return {"success": False, "error": f"Task {task_id} not found"}

            if task.status not in ("blocked", "failed"):
                return {
                    "success": False,
                    "error": f"Task status is {task.status}, not retryable",
                }

            task.status = "pending"
            task.started_at = None

            notes = list(task.notes or [])
            notes.append({
                "author": "system",
                "content": "Manually retried via runtime API",
                "timestamp": datetime.utcnow().isoformat(),
            })
            task.notes = notes

            db.commit()

            # Execute immediately
            return await self.execute_task_now(task_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    async def get_pending_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        """View pending task queue."""
        db = self._db()
        try:
            tasks = (
                db.query(TaskModel)
                .filter(
                    TaskModel.status.in_(
                        ["pending", "in_progress", "blocked"]
                    )
                )
                .order_by(TaskModel.created_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for t in tasks:
                agent_name = t.assigned_to
                try:
                    from app.agents.registry import get_agent as _get_agent
                    agent = _get_agent(t.assigned_to)
                    if agent:
                        agent_name = agent.full_name
                except Exception:
                    pass

                result.append({
                    "id": t.id,
                    "title": t.title,
                    "assigned_to": t.assigned_to,
                    "assigned_to_name": agent_name,
                    "status": t.status,
                    "priority": t.priority,
                    "campaign_id": t.campaign_id,
                    "created_at": (
                        t.created_at.isoformat() if t.created_at else None
                    ),
                    "started_at": (
                        t.started_at.isoformat() if t.started_at else None
                    ),
                    "due_date": (
                        t.due_date.isoformat() if t.due_date else None
                    ),
                    "dependencies": t.dependencies or [],
                    "has_deliverable": bool(t.deliverable),
                })

            return result
        finally:
            db.close()
