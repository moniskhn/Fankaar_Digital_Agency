"""
Claude Mythos — Task Router & Orchestrator
Routes tasks to the right agent(s), creates campaign workflows,
handles inter-agent messaging, and tracks workloads.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import (
    CampaignModel,
    MessageModel,
    SessionLocal,
    TaskModel,
)
from app.core.models import CampaignWorkflowResult, TaskCreate


class TaskRouter:
    """
    Routes tasks to agents based on skills, workload, and availability.
    """

    # Skill → agent ID mapping
    SKILL_AGENTS: Dict[str, str] = {
        # Sales & Business Development
        "lead_qualification": "sandor",
        "closing": "sandor",
        "cold_outreach": "sandor",
        "negotiation": "cersei",
        "vendor_negotiation": "cersei",
        "deal_structuring": "cersei",
        "pricing": "tywin",

        # Creative
        "copywriting": "tyrion",
        "content_creation": "tyrion",
        "brand_voice": "tyrion",
        "script_writing": "tyrion",
        "headline_writing": "tyrion",
        "visual_design": "rhaegar",
        "brand_identity": "rhaegar",
        "creative_direction": "rhaegar",
        "art_direction": "rhaegar",

        # Social & Community
        "social_media": "missandei",
        "community_management": "missandei",
        "social_strategy": "missandei",
        "influencer_collaboration": "missandei",

        # Advertising
        "ad_copywriting": "bronn",
        "performance_advertising": "bronn",
        "campaign_management": "bronn",
        "roas_optimization": "bronn",
        "audience_targeting": "bronn",

        # SEO
        "seo": "sandoq",
        "keyword_research": "sandoq",
        "technical_seo": "sandoq",
        "content_optimization": "sandoq",
        "link_building": "sandoq",

        # Email
        "email_marketing": "margaery",
        "email_campaigns": "margaery",
        "automation_sequences": "margaery",
        "newsletter": "margaery",

        # Analytics
        "analytics": "samwell",
        "data_analysis": "samwell",
        "reporting": "petyr",
        "dashboard": "petyr",
        "attribution": "samwell",

        # CRO
        "cro": "greyworm",
        "landing_page": "greyworm",
        "ab_testing": "greyworm",
        "conversion_optimization": "greyworm",
        "funnel_design": "greyworm",

        # Development
        "web_development": "gendry",
        "integration": "gendry",
        "automation": "gendry",
        "technical_implementation": "gendry",

        # Strategy
        "strategy": "bran",
        "strategic_planning": "bran",
        "growth_strategy": "bran",
        "market_opportunity": "bran",

        # Research
        "research": "arya",
        "competitive_analysis": "arya",
        "market_research": "arya",
        "trend_analysis": "arya",

        # Operations
        "project_management": "brienne",
        "quality_assurance": "brienne",
        "deadline_tracking": "brienne",
        "workflow": "brienne",

        # Client Relations
        "client_communication": "davos",
        "client_relations": "davos",
        "presentation": "davos",
        "retention": "jorah",
        "upsell": "jorah",
        "loyalty": "jorah",

        # Support
        "customer_support": "podrick",
        "ticket_management": "podrick",
        "client_care": "podrick",

        # PR & Comms
        "pr": "sansa",
        "media_relations": "sansa",
        "crisis_management": "sansa",
        "press_release": "sansa",

        # Finance
        "finance": "tywin",
        "budget": "tywin",
        "invoicing": "tywin",
        "roi": "tywin",

        # Legal
        "legal": "stannis",
        "contracts": "stannis",
        "compliance": "stannis",
        "privacy": "stannis",

        # HR
        "hr": "olenna",
        "hiring": "olenna",
        "team_culture": "olenna",

        # Regional
        "regional": "arya",
        "localization": "missandei",
    }

    async def route_by_description(self, task_description: str) -> str:
        """
        Route a task to the best agent based on its description.
        Returns agent ID.
        """
        desc_lower = task_description.lower()

        # Direct skill keyword matching
        best_match = None
        best_score = 0

        for skill, agent_id in self.SKILL_AGENTS.items():
            # Check for exact skill name
            score = 0
            if skill in desc_lower:
                score += 10
            # Check for partial matches
            skill_words = skill.split("_")
            for word in skill_words:
                if len(word) > 3 and word in desc_lower:
                    score += 3

            if score > best_score:
                best_score = score
                best_match = agent_id

        # Role-based matching
        role_keywords = {
            "sales": "sandor", "sell": "sandor", "prospect": "sandor", "lead": "sandor",
            "design": "rhaegar", "visual": "rhaegar", "brand": "rhaegar", "creative": "rhaegar",
            "copy": "tyrion", "write": "tyrion", "content": "tyrion", "text": "tyrion",
            "social": "missandei", "instagram": "missandei", "tiktok": "missandei", "community": "missandei",
            "ad": "bronn", "advertising": "bronn", "ppc": "bronn", "google ads": "bronn", "facebook ads": "bronn",
            "seo": "sandoq", "search": "sandoq", "keyword": "sandoq", "ranking": "sandoq",
            "email": "margaery", "newsletter": "margaery", "sequence": "margaery",
            "data": "samwell", "analytics": "samwell", "report": "petyr", "dashboard": "petyr", "metric": "samwell",
            "landing": "greyworm", "conversion": "greyworm", "cro": "greyworm", "funnel": "greyworm",
            "website": "gendry", "code": "gendry", "technical": "gendry", "integration": "gendry", "api": "gendry",
            "strategy": "bran", "plan": "bran", "growth": "bran", "opportunity": "bran",
            "research": "arya", "competitor": "arya", "market": "arya", "intel": "arya",
            "project": "brienne", "deadline": "brienne", "quality": "brienne", "qa": "brienne",
            "client": "davos", "meeting": "davos", "presentation": "davos",
            "budget": "tywin", "invoice": "tywin", "finance": "tywin", "cost": "tywin",
            "contract": "stannis", "legal": "stannis", "compliance": "stannis", "privacy": "stannis",
            "pr": "sansa", "press": "sansa", "media": "sansa", "reputation": "sansa",
            "support": "podrick", "ticket": "podrick", "help": "podrick",
            "retention": "jorah", "upsell": "jorah",
            "hr": "olenna", "hiring": "olenna", "team": "olenna",
        }

        for keyword, agent_id in role_keywords.items():
            if keyword in desc_lower:
                # Combine scores if we already have a match
                if best_match == agent_id:
                    best_score += 5
                elif best_score < 15:
                    best_match = agent_id
                    best_score = 8

        if best_match:
            return best_match

        # Fallback: return Jon
        return "jon"

    async def route_by_skills(self, required_skills: List[str]) -> List[str]:
        """
        Find agents that collectively cover all required skills.
        Returns list of agent IDs.
        """
        matched_agents = set()
        covered_skills = set()

        for skill in required_skills:
            skill_lower = skill.lower().replace(" ", "_")
            if skill_lower in self.SKILL_AGENTS:
                agent_id = self.SKILL_AGENTS[skill_lower]
                matched_agents.add(agent_id)
                covered_skills.add(skill)

        if not matched_agents:
            matched_agents.add("jon")

        return list(matched_agents)

    async def get_agent_workload(self, agent_id: str) -> Dict[str, Any]:
        """Get current workload for an agent."""
        db = SessionLocal()
        try:
            total_tasks = db.query(TaskModel).filter(
                TaskModel.assigned_to == agent_id
            ).count()

            pending = db.query(TaskModel).filter(
                TaskModel.assigned_to == agent_id,
                TaskModel.status == "pending"
            ).count()

            in_progress = db.query(TaskModel).filter(
                TaskModel.assigned_to == agent_id,
                TaskModel.status == "in_progress"
            ).count()

            completed = db.query(TaskModel).filter(
                TaskModel.assigned_to == agent_id,
                TaskModel.status == "completed"
            ).count()

            blocked = db.query(TaskModel).filter(
                TaskModel.assigned_to == agent_id,
                TaskModel.status == "blocked"
            ).count()

            total = total_tasks if total_tasks > 0 else 1
            utilization = ((in_progress + blocked) / total) * 100

            return {
                "agent_id": agent_id,
                "total_tasks": total_tasks,
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed,
                "blocked": blocked,
                "utilization_pct": round(utilization, 1),
                "available": pending == 0 and in_progress < 3,
            }
        finally:
            db.close()


class CampaignWorkflowBuilder:
    """
    Builds complete campaign workflows with tasks for each phase.
    """

    async def create_campaign_workflow(
        self,
        brief: Dict[str, Any],
        client_id: str,
    ) -> CampaignWorkflowResult:
        """
        Create a full campaign workflow from a brief.
        Generates tasks for each phase and assigns agents.
        """
        campaign_id = str(uuid.uuid4())
        campaign_name = brief.get("name", "New Campaign")
        region = brief.get("region", "Global")
        channels = brief.get("channels", [])

        # Determine team based on channels
        if any(c in channels for c in ["instagram", "tiktok", "facebook", "social"]):
            team_type = "social_only"
        elif any(c in channels for c in ["google_ads", "ppc", "paid"]):
            team_type = "paid_only"
        elif any(c in channels for c in ["seo", "organic", "search"]):
            team_type = "seo_only"
        else:
            team_type = "full_service"

        from app.agents.registry import get_team_for_campaign
        agent_ids = get_team_for_campaign(team_type)

        # Create campaign in DB
        db = SessionLocal()
        try:
            campaign = CampaignModel(
                id=campaign_id,
                client_id=client_id,
                name=campaign_name,
                status="brief",
                region=region,
                channels=channels,
                objectives=brief.get("objectives", []),
                timeline={
                    "brief": datetime.utcnow().isoformat(),
                    "strategy": None,
                    "creation": None,
                    "review": None,
                    "approval": None,
                    "live": None,
                    "reporting": None,
                    "completed": None,
                },
                assigned_agents=agent_ids,
                deliverables=[],
                metrics={},
                brief_summary=brief.get("brief_summary", ""),
                budget=brief.get("budget", 0.0),
            )
            db.add(campaign)

            # Generate tasks for each phase
            tasks = self._generate_phase_tasks(
                campaign_id, campaign_name, region, channels, brief, agent_ids
            )

            for task_data in tasks:
                task = TaskModel(**task_data)
                db.add(task)

            db.commit()

            return CampaignWorkflowResult(
                campaign_id=campaign_id,
                tasks_created=len(tasks),
                agents_assigned=agent_ids,
                estimated_duration_days=self._estimate_duration(tasks),
                phases=["brief", "strategy", "creation", "review", "approval", "live", "reporting", "completed"],
            )
        finally:
            db.close()

    def _generate_phase_tasks(
        self,
        campaign_id: str,
        campaign_name: str,
        region: str,
        channels: List[str],
        brief: Dict[str, Any],
        agent_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate all tasks for a campaign across all phases."""
        tasks = []
        now = datetime.utcnow()

        # ── Phase 1: Strategy ──
        if "arya" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "arya",
                "assigned_by": "jon",
                "title": f"Market research for {campaign_name}",
                "description": f"Research {region} market, competitors, and audience for campaign. Channels: {', '.join(channels)}. Brief: {brief.get('brief_summary', '')[:200]}",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=3),
                "dependencies": [],
            })

        if "bran" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "bran",
                "assigned_by": "jon",
                "title": f"Strategic plan for {campaign_name}",
                "description": f"Develop campaign strategy including positioning, messaging framework, channel strategy, and KPIs for {region}.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=5),
                "dependencies": [t["id"] for t in tasks if t["assigned_to"] == "arya"],
            })

        # ── Phase 2: Creation ──
        if "tyrion" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "tyrion",
                "assigned_by": "jon",
                "title": f"Copy & content for {campaign_name}",
                "description": f"Write all campaign copy: headlines, body copy, CTAs, social captions, email subject lines. Region: {region}. Channels: {', '.join(channels)}.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=8),
                "dependencies": [t["id"] for t in tasks if t["assigned_to"] == "bran"],
            })

        if "rhaegar" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "rhaegar",
                "assigned_by": "jon",
                "title": f"Creative assets for {campaign_name}",
                "description": f"Design visual assets: social graphics, ad creatives, landing page design. Brand voice: {brief.get('brand_voice', 'Not specified')}. Region: {region}.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=10),
                "dependencies": [t["id"] for t in tasks if t["assigned_to"] == "bran"],
            })

        # Social content creation
        if "missandei" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "missandei",
                "assigned_by": "jon",
                "title": f"Social content calendar for {campaign_name}",
                "description": f"Create social media content plan and posts for {', '.join(channels)} targeting {region}.",
                "status": "pending",
                "priority": "medium",
                "due_date": now + timedelta(days=8),
                "dependencies": [t["id"] for t in tasks if t["assigned_to"] == "tyrion"],
            })

        # ── Phase 3: Technical Setup ──
        if "gendry" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "gendry",
                "assigned_by": "jon",
                "title": f"Technical setup for {campaign_name}",
                "description": f"Set up tracking, pixels, landing pages, integrations. Configure analytics for {', '.join(channels)}.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=7),
                "dependencies": [],
            })

        if "greyworm" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "greyworm",
                "assigned_by": "jon",
                "title": f"Landing page optimization for {campaign_name}",
                "description": f"Build and optimize conversion-focused landing pages. A/B test key elements.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=9),
                "dependencies": [t["id"] for t in tasks if t["assigned_to"] == "gendry"],
            })

        # ── Phase 4: Review ──
        if "brienne" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "brienne",
                "assigned_by": "jon",
                "title": f"QA review for {campaign_name}",
                "description": "Quality assurance review of all deliverables. Check against brief requirements, brand guidelines, and quality standards.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=12),
                "dependencies": [],
            })

        if "stannis" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "stannis",
                "assigned_by": "jon",
                "title": f"Legal & compliance review for {campaign_name}",
                "description": f"Review all campaign materials for legal compliance, IP clearance, and regulatory requirements in {region}.",
                "status": "pending",
                "priority": "medium",
                "due_date": now + timedelta(days=11),
                "dependencies": [],
            })

        # ── Phase 5: Launch ──
        if "bronn" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "bronn",
                "assigned_by": "jon",
                "title": f"Launch ad campaigns for {campaign_name}",
                "description": f"Set up and launch paid advertising across {', '.join(channels)}. Configure targeting, budgets, and bidding.",
                "status": "pending",
                "priority": "high",
                "due_date": now + timedelta(days=14),
                "dependencies": [],
            })

        if "sandoq" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "sandoq",
                "assigned_by": "jon",
                "title": f"SEO optimization for {campaign_name}",
                "description": f"Implement on-page SEO, schema markup, and content optimization for {region}.",
                "status": "pending",
                "priority": "medium",
                "due_date": now + timedelta(days=12),
                "dependencies": [],
            })

        if "margaery" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "margaery",
                "assigned_by": "jon",
                "title": f"Email campaign launch for {campaign_name}",
                "description": "Set up email sequences, automation triggers, and list segmentation.",
                "status": "pending",
                "priority": "medium",
                "due_date": now + timedelta(days=13),
                "dependencies": [],
            })

        # ── Phase 6: Reporting ──
        if "samwell" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "samwell",
                "assigned_by": "jon",
                "title": f"Performance tracking for {campaign_name}",
                "description": "Set up performance dashboards, KPI tracking, and reporting infrastructure.",
                "status": "pending",
                "priority": "medium",
                "due_date": now + timedelta(days=10),
                "dependencies": [],
            })

        if "petyr" in agent_ids:
            tasks.append({
                "id": str(uuid.uuid4()),
                "campaign_id": campaign_id,
                "assigned_to": "petyr",
                "assigned_by": "jon",
                "title": f"Reporting dashboard for {campaign_name}",
                "description": "Create campaign reporting dashboard with real-time metrics and automated alerts.",
                "status": "pending",
                "priority": "low",
                "due_date": now + timedelta(days=11),
                "dependencies": [],
            })

        # Set dependencies for review tasks
        creation_task_ids = [t["id"] for t in tasks if t["assigned_to"] in ["tyrion", "rhaegar", "missandei"]]
        for t in tasks:
            if t["assigned_to"] == "brienne" and not t["dependencies"]:
                t["dependencies"] = creation_task_ids
            if t["assigned_to"] == "stannis" and not t["dependencies"]:
                t["dependencies"] = creation_task_ids

        return tasks

    def _estimate_duration(self, tasks: List[Dict[str, Any]]) -> int:
        """Estimate campaign duration in days based on tasks."""
        if not tasks:
            return 14
        latest_due = max(
            (t.get("due_date") for t in tasks if t.get("due_date")),
            default=datetime.utcnow() + timedelta(days=14),
        )
        delta = latest_due - datetime.utcnow()
        return max(delta.days, 7)


class InterAgentMessaging:
    """Handles inter-agent messaging and broadcast."""

    @staticmethod
    async def send_message(
        from_agent: str,
        to_agent: str,
        content: str,
        message_type: str = "chat",
        campaign_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a message from one agent to another."""
        db = SessionLocal()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent=from_agent,
                to_agent=to_agent,
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

    @staticmethod
    async def broadcast(
        from_agent: str,
        content: str,
        message_type: str = "alert",
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Broadcast a message to all agents."""
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
    async def get_messages_for_agent(
        agent_id: str,
        limit: int = 50,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all messages for an agent (including broadcasts)."""
        db = SessionLocal()
        try:
            query = db.query(MessageModel).filter(
                (MessageModel.to_agent == agent_id)
                | (MessageModel.to_agent == "broadcast")
                | (MessageModel.from_agent == agent_id)
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
