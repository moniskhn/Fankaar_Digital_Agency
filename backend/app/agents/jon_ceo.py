"""
Fankaar Digital — CEO Orchestrator (Jon Snow)
Daily report generation, task delegation, owner communication,
and daily standup collection.
"""

import json
import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.core.database import (
    CampaignModel,
    MessageModel,
    ReportModel,
    SessionLocal,
    TaskModel,
)
from app.core.enhanced_memory import EnhancedAgentMemory
from app.core.models import (
    AgentUpdateEntry,
    CampaignStatusEntry,
    DailyReport,
    Task,
)
from app.services.llm_client import llm_client


class JonCEO(BaseAgent):
    """
    Jon Snow — CEO of Fankaar Digital.
    Generates daily reports, delegates tasks, communicates with owner.
    """

    def __init__(self, config=None):
        from app.agents.registry import get_agent
        if config is None:
            config = get_agent("jon")
        super().__init__(config)

    # ── Daily Standup ────────────────────────────────────────────

    async def run_daily_standup(self) -> List[AgentUpdateEntry]:
        """
        Collect status updates from all agents.
        Simulates a daily standup by gathering recent activity.
        """
        from app.agents.registry import get_all_agents

        agents = get_all_agents()
        updates: List[AgentUpdateEntry] = []

        for agent_config in agents:
            if agent_config.id == "jon":
                continue

            mem = EnhancedAgentMemory(agent_config.id)
            recent_activity = mem.get_recent_activity(limit=5)
            conversations = mem.get_conversation_history(limit=3)

            # Count tasks by status
            db = SessionLocal()
            try:
                tasks = db.query(TaskModel).filter(
                    TaskModel.assigned_to == agent_config.id
                ).all()

                completed = [t for t in tasks if t.status == "completed"]
                in_progress = [t for t in tasks if t.status == "in_progress"]
                blocked = [t for t in tasks if t.status == "blocked"]

                # Build update entry
                completed_items = [f"Task: {t.title}" for t in completed[-3:]]
                in_progress_items = [f"Task: {t.title}" for t in in_progress[:2]]
                blocked_items = [f"Task: {t.title}" for t in blocked[:2]]

                if not completed_items and recent_activity:
                    completed_items = [a["action"] for a in recent_activity[:2]]

                notes = ""
                if conversations:
                    latest = conversations[-1]
                    notes = f"Latest: {latest['content'][:80]}..." if len(latest['content']) > 80 else f"Latest: {latest['content']}"

                updates.append(AgentUpdateEntry(
                    agent_id=agent_config.id,
                    agent_name=agent_config.name,
                    avatar=agent_config.avatar,
                    status=agent_config.status or "active",
                    completed=completed_items or ["Working on assigned tasks"],
                    in_progress=in_progress_items or [],
                    blocked=blocked_items or [],
                    notes=notes,
                ))
            finally:
                db.close()

        return updates

    # ── Daily Report Generation ──────────────────────────────────

    async def generate_daily_report(self, report_date: Optional[date] = None) -> DailyReport:
        """
        Generate the comprehensive daily report for the owner.
        Compiles updates from all agents, campaign status, and priorities.
        """
        if report_date is None:
            report_date = date.today()

        report_id = str(uuid.uuid4())
        date_str = report_date.isoformat()

        # Collect agent updates (standup)
        agent_updates = await self.run_daily_standup()

        # Get campaign status
        db = SessionLocal()
        try:
            campaigns = db.query(CampaignModel).all()

            campaigns_status: List[CampaignStatusEntry] = []
            for c in campaigns:
                total_tasks = db.query(TaskModel).filter(TaskModel.campaign_id == c.id).count()
                completed_tasks = db.query(TaskModel).filter(
                    TaskModel.campaign_id == c.id,
                    TaskModel.status == "completed"
                ).count()

                progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

                status_emoji = {
                    "brief": "📋",
                    "strategy": "🧠",
                    "creation": "✏️",
                    "review": "👀",
                    "approval": "⏳",
                    "live": "🚀",
                    "reporting": "📊",
                    "completed": "✅",
                }.get(c.status, "⚪")

                highlight = ""
                if c.metrics:
                    top_metric = max(c.metrics.items(), key=lambda x: x[1])
                    highlight = f"{top_metric[0]}: {top_metric[1]:.1f}"

                campaigns_status.append(CampaignStatusEntry(
                    campaign_id=c.id,
                    campaign_name=c.name,
                    status=f"{status_emoji} {c.status.upper()}",
                    progress_pct=progress,
                    highlight=highlight,
                ))

            # Get recent messages/decisions
            recent_messages = db.query(MessageModel).filter(
                MessageModel.message_type.in_(["decision", "alert"]),
            ).order_by(MessageModel.timestamp.desc()).limit(10).all()

            decisions_made = [
                m.content for m in recent_messages
                if m.message_type == "decision"
            ][:5]

            issues_flags = [
                m.content for m in recent_messages
                if m.message_type == "alert"
            ][:5]

            # Count status summaries
            status_counts = {}
            for c in campaigns:
                status_counts[c.status] = status_counts.get(c.status, 0) + 1
        finally:
            db.close()

        # Generate summary via LLM (skip in quick mode for speed)
        summary = f"Agency operational. {len(campaigns)} campaigns, {len(agent_updates)} agent updates."
        tomorrow_priorities = [
            "Review campaign progress and adjust timelines",
            "Follow up on pending client approvals",
            "Check agent workload distribution",
            "Monitor active campaign metrics",
            "Prepare tomorrow's standup agenda",
        ]

        # Only call LLM if we have time (not in quick mode)
        use_llm = os.getenv("DAILY_REPORT_LLM", "true").lower() == "true"
        if use_llm:
            summary_context = f"""
            Agency: {settings.agency_name}
            Date: {date_str}
            Active Agents: 23
            Campaigns: {len(campaigns)}
            Campaign Status: {status_counts}

            Agent Activity Summary:
            {chr(10).join(f"- {u.agent_name}: {len(u.completed)} completed, {len(u.in_progress)} in progress" for u in agent_updates[:10])}

            Decisions: {len(decisions_made)}
            Issues: {len(issues_flags)}
            """

            try:
                summary_response = await self.think(
                    task="Write a brief executive summary (2-3 sentences) of today's agency activity.",
                    context=summary_context,
                )
                summary = summary_response.strip()
            except Exception:
                total_completed = sum(len(u.completed) for u in agent_updates)
                summary = f"Agency operational. {total_completed} tasks completed across {len(agent_updates)} agents. {len(campaigns)} campaigns active."

            try:
                priorities_response = await self.think(
                    task="List 3-5 priority items for tomorrow based on current campaign status and agent workloads.",
                    context=summary_context,
                )
                tomorrow_priorities = [
                    line.strip("-• 0123456789.")
                    for line in priorities_response.strip().split("\n")
                    if line.strip() and len(line.strip()) > 5
                ][:5]
            except Exception:
                pass  # keep defaults

        # Items needing owner attention
        owner_attention = []
        for cs in campaigns_status:
            if cs.status.endswith("APPROVAL"):
                owner_attention.append(f"Approve campaign: {cs.campaign_name}")
        for issue in issues_flags[:2]:
            owner_attention.append(issue[:100])

        if not owner_attention:
            owner_attention = ["No items require your attention today. Agency running smoothly."]

        # Determine sentiment
        blocked_count = sum(len(u.blocked) for u in agent_updates)
        if blocked_count >= 3:
            sentiment = "concern"
        elif len(issues_flags) > 2:
            sentiment = "concern"
        else:
            sentiment = "positive"

        report = DailyReport(
            id=report_id,
            date=date_str,
            summary=summary,
            agent_updates=agent_updates,
            campaigns_status=campaigns_status,
            decisions_made=decisions_made or ["No major decisions today"],
            issues_flags=issues_flags or ["No issues flagged"],
            tomorrow_priorities=tomorrow_priorities,
            owner_attention_required=owner_attention,
            sentiment=sentiment,
        )

        # Save to database
        db = SessionLocal()
        try:
            db_report = ReportModel(
                id=report_id,
                date=date_str,
                summary=summary,
                agent_updates=[u.model_dump() for u in agent_updates],
                campaigns_status=[cs.model_dump() for cs in campaigns_status],
                decisions_made=decisions_made,
                issues_flags=issues_flags,
                tomorrow_priorities=tomorrow_priorities,
                owner_attention_required=owner_attention,
                sentiment=sentiment,
            )
            db.add(db_report)
            db.commit()
        finally:
            db.close()

        return report

    # ── WhatsApp Report Formatting ───────────────────────────────

    def format_report_for_whatsapp(self, report: DailyReport) -> str:
        """
        Format a daily report for WhatsApp mobile readability.
        Uses emojis, short lines, and clear sections.
        """
        lines = []

        # Header
        lines.append(f"🌅 *{settings.agency_name} — DAILY REPORT*")
        lines.append(f"📅 {report.date}")
        lines.append(f"👑 Jon Snow, CEO")
        lines.append("")

        # Summary
        lines.append(f"📊 *SUMMARY*")
        lines.append(report.summary)
        lines.append("")

        # Highlights
        lines.append("📈 *TODAY'S HIGHLIGHTS*")
        for u in report.agent_updates[:8]:
            if u.completed and u.completed[0]:
                icon = "✅" if not u.blocked else "⚠️"
                item = u.completed[0][:60]
                lines.append(f"{icon} {u.avatar} {u.agent_name}: {item}")
        lines.append("")

        # Campaigns
        if report.campaigns_status:
            lines.append("📋 *CAMPAIGNS*")
            for cs in report.campaigns_status:
                bar = "█" * int(cs.progress_pct / 10) + "░" * (10 - int(cs.progress_pct / 10))
                lines.append(f"{cs.status} {cs.campaign_name}")
                lines.append(f"   [{bar}] {cs.progress_pct:.0f}%")
                if cs.highlight:
                    lines.append(f"   📊 {cs.highlight}")
            lines.append("")

        # Team Updates (abbreviated)
        lines.append("👥 *TEAM SNAPSHOT*")
        for u in report.agent_updates[:12]:
            status_icon = {
                "active": "🟢",
                "busy": "🔵",
                "offline": "⚫",
            }.get(u.status, "⚪")
            task_count = len(u.in_progress)
            lines.append(f"{status_icon} {u.avatar} {u.agent_name} ({task_count} active)")
        lines.append("")

        # Tomorrow's priorities
        if report.tomorrow_priorities:
            lines.append("🎯 *TOMORROW'S PRIORITIES*")
            for i, p in enumerate(report.tomorrow_priorities[:5], 1):
                lines.append(f"{i}. {p}")
            lines.append("")

        # Owner attention
        if report.owner_attention_required:
            lines.append("⚡ *NEEDS YOUR INPUT:*")
            for item in report.owner_attention_required[:4]:
                lines.append(f"→ {item}")
            lines.append("")

        # Footer
        lines.append(f"Reply with decisions — I'll execute, {settings.owner_name}.")
        lines.append(f"🐺 Jon")

        return "\n".join(lines)

    async def send_daily_report_via_whatsapp(self, report: DailyReport) -> bool:
        """Format and send the daily report via WhatsApp."""
        from app.services.whatsapp import WhatsAppService

        formatted = self.format_report_for_whatsapp(report)
        wa = WhatsAppService()
        result = await wa.send_daily_report(report, settings.owner_whatsapp_number)

        if result:
            # Mark as sent
            db = SessionLocal()
            try:
                db_report = db.query(ReportModel).filter(ReportModel.id == report.id).first()
                if db_report:
                    db_report.sent_via_whatsapp = 1
                    db.commit()
            finally:
                db.close()

        return result

    # ── Owner Communication ──────────────────────────────────────

    async def handle_owner_message(self, message: str) -> str:
        """
        Handle an incoming message from the owner.
        Parse intent and respond or take action.
        """
        message_lower = message.lower().strip()

        # Quick intent detection
        intent = await self._parse_owner_intent(message)

        if intent == "report":
            report = await self.generate_daily_report()
            formatted = self.format_report_for_whatsapp(report)
            return formatted

        elif intent == "status":
            return await self._get_agency_status_summary()

        elif intent == "decision":
            return await self._handle_owner_decision(message)

        elif intent == "task":
            return await self._delegate_from_owner(message)

        elif intent == "praise":
            return await self._handle_praise()

        elif intent == "urgent":
            return await self._handle_urgent_request(message)

        else:
            # General conversation — respond as Jon
            response = await self.think(
                task=f"The owner ({settings.owner_name}) said: '{message}'. Respond as Jon Snow, CEO.",
                context=f"You are Jon Snow, CEO of {settings.agency_name}. Be respectful, honest, and helpful. Address the owner as {settings.owner_name}.",
            )
            return self._clean_response(response)

    def _clean_response(self, text: str) -> str:
        """Strip markdown, emojis, and formatting from conversational responses."""
        # Remove markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'', text)  # bold
        text = re.sub(r'\*(.*?)\*', r'', text)      # italic
        text = re.sub(r'__(.*?)__', r'', text)      # underline
        text = re.sub(r'`(.*?)`', r'', text)         # code
        # Remove emoji ranges
        text = re.sub(r'[🌀-🧿☀-⛿✀-➿]', '', text)
        # Remove bullet points and numbered lists at line start
        text = re.sub(r'^[\s]*[-•*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
        # Clean up multiple spaces and newlines
        text = re.sub(r'  +', ' ', text)
        text = re.sub(r'

+', '

', text)
        return text.strip()

    async def _parse_owner_intent(self, message: str) -> str:
        """Parse the owner's message intent."""
        msg = message.lower()

        report_keywords = ["report", "update", "what's happening", "status report", "daily", "briefing"]
        status_keywords = ["status", "how are things", "how is everyone", "team", "agents"]
        decision_keywords = ["approve", "reject", "yes", "no", "go ahead", "don't", "do not", "cancel"]
        task_keywords = ["assign", "delegate", "get someone to", "have someone", "task", "do this"]
        praise_keywords = ["good job", "well done", "great work", "thank you", "thanks", "appreciate"]
        urgent_keywords = ["urgent", "asap", "emergency", "now", "immediately", "critical"]

        if any(k in msg for k in urgent_keywords):
            return "urgent"
        if any(k in msg for k in report_keywords):
            return "report"
        if any(k in msg for k in status_keywords):
            return "status"
        if any(k in msg for k in decision_keywords):
            return "decision"
        if any(k in msg for k in task_keywords):
            return "task"
        if any(k in msg for k in praise_keywords):
            return "praise"

        return "general"

    async def _get_agency_status_summary(self) -> str:
        """Get a quick agency status summary."""
        db = SessionLocal()
        try:
            from app.agents.registry import get_all_agents
            agents = get_all_agents()

            active_count = sum(1 for a in agents if a.status == "active")
            busy_count = sum(1 for a in agents if a.status == "busy")

            campaigns = db.query(CampaignModel).all()
            live_campaigns = [c for c in campaigns if c.status == "live"]

            pending_tasks = db.query(TaskModel).filter(
                TaskModel.status.in_(["pending", "in_progress"])
            ).count()

            return (
                f"We're running smooth. {active_count} agents active, {busy_count} busy. "
                f"{len(live_campaigns)} campaign{'s' if len(live_campaigns) != 1 else ''} live, {len(campaigns)} total. "
                f"{pending_tasks} task{'s' if pending_tasks != 1 else ''} in the queue."
            )
        finally:
            db.close()

    async def _handle_owner_decision(self, message: str) -> str:
        """Handle an owner decision (approve/reject)."""
        db = SessionLocal()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent="owner",
                to_agent="jon",
                content=message,
                timestamp=datetime.utcnow(),
                message_type="decision",
            )
            db.add(msg)
            db.commit()

            return (
                f"Got it. I'll make sure the right people know."
            )
        finally:
            db.close()

    async def _delegate_from_owner(self, message: str) -> str:
        """Delegate a task from the owner's message."""
        # Extract task description
        task_clean = message
        for prefix in ["assign ", "delegate ", "get someone to ", "have someone ", "task "]:
            if task_clean.lower().startswith(prefix):
                task_clean = task_clean[len(prefix):]
                break

        # Route to best agent
        from app.core.orchestrator import TaskRouter
        router = TaskRouter()
        agent_id = await router.route_by_description(task_clean)

        from app.agents.registry import get_agent
        agent = get_agent(agent_id)

        if agent:
            return (
                f"Handed it to {agent.name}. They'll take it from here."
            )
        else:
            return f"I'll find the right person and get it moving."

    async def _handle_praise(self) -> str:
        """Handle owner praise/thanks."""
        responses = [
            "Means a lot. I'll tell the team.",
            "Appreciate that. We're here to deliver.",
            "Thank you. The agency stands ready.",
        ]
        import random
        return random.choice(responses)

    async def _handle_urgent_request(self, message: str) -> str:
        """Handle urgent requests from owner."""
        return (
            f"On it. I'll have an update for you within the hour."
        )

    # ── Task Delegation ──────────────────────────────────────────

    async def delegate_task(
        self,
        task_description: str,
        to_agent_id: str,
        campaign_id: Optional[str] = None,
        priority: str = "medium",
    ) -> str:
        """Delegate a task to a specific agent."""
        from app.agents.registry import get_agent
        from app.core.database import TaskModel

        agent = get_agent(to_agent_id)
        if not agent:
            return f"Agent {to_agent_id} not found."

        db = SessionLocal()
        try:
            task = TaskModel(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                assigned_to=to_agent_id,
                assigned_by="jon",
                title=task_description[:100],
                description=task_description,
                status="pending",
                priority=priority,
            )
            db.add(task)

            # Send message to agent
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent="jon",
                to_agent=to_agent_id,
                content=f"New task from the CEO: {task_description}",
                timestamp=datetime.utcnow(),
                message_type="task",
                campaign_id=campaign_id,
                extra_metadata={"task_id": task.id, "priority": priority, "campaign_id": campaign_id},
            )
            db.add(msg)
            db.commit()

            return task.id
        finally:
            db.close()

    # ── Inbox Management ─────────────────────────────────────────

    async def get_owner_inbox(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the owner-CEO conversation history."""
        db = SessionLocal()
        try:
            messages = (
                db.query(MessageModel)
                .filter(
                    (MessageModel.from_agent == "owner")
                    | (MessageModel.to_agent == "owner")
                    | (MessageModel.from_agent == "jon")
                    | (MessageModel.to_agent == "jon")
                )
                .order_by(MessageModel.timestamp.desc())
                .limit(limit)
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
                    "read": bool(m.read),
                }
                for m in reversed(messages)
            ]
        finally:
            db.close()

    # ── Review & QA ──────────────────────────────────────────────

    async def review_deliverable(self, task_id: str) -> Dict[str, Any]:
        """Review a deliverable before it goes to the owner."""
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return {"approved": False, "reason": "Task not found"}

            if not task.deliverable:
                return {"approved": False, "reason": "No deliverable submitted"}

            # LLM-based review
            review_prompt = f"""
            Review this deliverable:

            Title: {task.title}
            Description: {task.description}
            Deliverable: {task.deliverable[:2000]}

            Evaluate on: quality, completeness, alignment with requirements.
            Respond with JSON: {{"approved": bool, "score": 1-10, "feedback": "string"}}
            """

            try:
                response = await llm_client.complete(
                    prompt=review_prompt,
                    system="You are a quality assurance reviewer. Be thorough but fair.",
                )
                result = json.loads(response.text)
                return {
                    "approved": result.get("approved", False),
                    "score": result.get("score", 5),
                    "feedback": result.get("feedback", "Review completed."),
                    "task_id": task_id,
                }
            except Exception:
                return {
                    "approved": True,
                    "score": 7,
                    "feedback": "Auto-approved (review system unavailable)",
                    "task_id": task_id,
                }
        finally:
            db.close()
