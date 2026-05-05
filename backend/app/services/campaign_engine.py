"""
Claude Mythos — Campaign Engine
End-to-end campaign lifecycle management.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import (
    CampaignModel,
    Deliverable,
    SessionLocal,
    TaskModel,
)
from app.core.models import (
    Campaign,
    CampaignBrief,
    CampaignPhaseUpdate,
    CampaignReport,
    CampaignStatusEntry,
    CampaignWorkflowResult,
    Task,
)
from app.core.orchestrator import CampaignWorkflowBuilder


class CampaignEngine:
    """
    Manages the full campaign lifecycle from brief to completion.
    """

    PHASES = ["brief", "strategy", "creation", "review", "approval", "live", "reporting", "completed"]

    async def create_campaign(self, brief: CampaignBrief) -> Campaign:
        """
        Create a new campaign from a brief.
        """
        campaign_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Build workflow
        workflow_builder = CampaignWorkflowBuilder()
        brief_dict = brief.model_dump()
        brief_dict["name"] = brief_dict.get("name", "New Campaign")

        workflow_result = await workflow_builder.create_campaign_workflow(
            brief=brief_dict,
            client_id=brief.client_id,
        )

        # Get created campaign from DB
        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(
                CampaignModel.id == workflow_result.campaign_id
            ).first()

            if campaign:
                return Campaign(
                    id=campaign.id,
                    client_id=campaign.client_id,
                    name=campaign.name,
                    status=campaign.status,
                    region=campaign.region,
                    channels=campaign.channels or [],
                    objectives=campaign.objectives or [],
                    timeline=campaign.timeline or {},
                    assigned_agents=campaign.assigned_agents or [],
                    deliverables=[],
                    metrics=campaign.metrics or {},
                    brief_summary=campaign.brief_summary or "",
                    budget=campaign.budget or 0.0,
                    spent=campaign.spent or 0.0,
                    created_at=campaign.created_at,
                    updated_at=campaign.updated_at,
                )

            # Fallback: create manually
            return Campaign(
                id=workflow_result.campaign_id,
                client_id=brief.client_id,
                name=brief.name,
                status="brief",
                region=brief.region,
                channels=brief.channels,
                objectives=brief.objectives,
                timeline={"brief": now.isoformat()},
                assigned_agents=workflow_result.agents_assigned,
                deliverables=[],
                metrics={},
                brief_summary=brief.brief_summary,
                budget=brief.budget,
            )
        finally:
            db.close()

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        db = SessionLocal()
        try:
            c = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
            if not c:
                return None

            deliverables = []
            if c.deliverables:
                for d in c.deliverables:
                    if isinstance(d, dict):
                        deliverables.append(Deliverable(**d))

            return Campaign(
                id=c.id,
                client_id=c.client_id,
                name=c.name,
                status=c.status,
                region=c.region,
                channels=c.channels or [],
                objectives=c.objectives or [],
                timeline=c.timeline or {},
                assigned_agents=c.assigned_agents or [],
                deliverables=deliverables,
                metrics=c.metrics or {},
                brief_summary=c.brief_summary or "",
                budget=c.budget or 0.0,
                spent=c.spent or 0.0,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        finally:
            db.close()

    async def list_campaigns(
        self,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Campaign]:
        """List campaigns with optional filters."""
        db = SessionLocal()
        try:
            query = db.query(CampaignModel)

            if status:
                query = query.filter(CampaignModel.status == status)
            if client_id:
                query = query.filter(CampaignModel.client_id == client_id)

            campaigns = query.order_by(CampaignModel.created_at.desc()).limit(limit).all()

            return [
                Campaign(
                    id=c.id,
                    client_id=c.client_id,
                    name=c.name,
                    status=c.status,
                    region=c.region,
                    channels=c.channels or [],
                    objectives=c.objectives or [],
                    timeline=c.timeline or {},
                    assigned_agents=c.assigned_agents or [],
                    deliverables=[],
                    metrics=c.metrics or {},
                    brief_summary=c.brief_summary or "",
                    budget=c.budget or 0.0,
                    spent=c.spent or 0.0,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
                for c in campaigns
            ]
        finally:
            db.close()

    async def advance_phase(self, campaign_id: str) -> Campaign:
        """
        Advance a campaign to the next phase.
        """
        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            current_idx = self.PHASES.index(campaign.status) if campaign.status in self.PHASES else 0
            if current_idx >= len(self.PHASES) - 1:
                raise ValueError(f"Campaign is already in final phase: {campaign.status}")

            new_phase = self.PHASES[current_idx + 1]
            campaign.status = new_phase

            # Update timeline
            timeline = campaign.timeline or {}
            timeline[new_phase] = datetime.utcnow().isoformat()
            campaign.timeline = timeline

            db.commit()

            return await self.get_campaign(campaign_id)
        finally:
            db.close()

    async def update_phase(self, campaign_id: str, new_phase: str) -> Campaign:
        """Update campaign to a specific phase."""
        if new_phase not in self.PHASES:
            raise ValueError(f"Invalid phase: {new_phase}. Valid phases: {self.PHASES}")

        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            campaign.status = new_phase

            timeline = campaign.timeline or {}
            timeline[new_phase] = datetime.utcnow().isoformat()
            campaign.timeline = timeline

            db.commit()

            return await self.get_campaign(campaign_id)
        finally:
            db.close()

    async def get_campaign_tasks(self, campaign_id: str) -> List[Task]:
        """Get all tasks for a campaign."""
        db = SessionLocal()
        try:
            tasks = db.query(TaskModel).filter(
                TaskModel.campaign_id == campaign_id
            ).order_by(TaskModel.created_at.desc()).all()

            return [
                Task(
                    id=t.id,
                    campaign_id=t.campaign_id,
                    assigned_to=t.assigned_to,
                    assigned_by=t.assigned_by,
                    title=t.title,
                    description=t.description or "",
                    status=t.status,
                    priority=t.priority,
                    due_date=t.due_date,
                    dependencies=t.dependencies or [],
                    deliverable=t.deliverable,
                    deliverable_type=t.deliverable_type,
                    notes=[],
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in tasks
            ]
        finally:
            db.close()

    async def generate_campaign_report(self, campaign_id: str) -> CampaignReport:
        """Generate a comprehensive campaign report."""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        tasks = await self.get_campaign_tasks(campaign_id)

        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Agent contributions
        agent_tasks: Dict[str, int] = {}
        for t in tasks:
            agent_tasks[t.assigned_to] = agent_tasks.get(t.assigned_to, 0) + 1

        from app.agents.registry import get_agent
        agent_contributions = []
        for agent_id, count in sorted(agent_tasks.items(), key=lambda x: -x[1]):
            agent = get_agent(agent_id)
            agent_contributions.append({
                "agent_id": agent_id,
                "agent_name": agent.name if agent else agent_id,
                "avatar": agent.avatar if agent else "👤",
                "tasks": count,
            })

        # Deliverables status
        deliverables_status = campaign.deliverables or []

        # ROI estimate
        roi = 0.0
        if campaign.budget > 0:
            revenue_estimate = campaign.budget * 2.5  # Placeholder
            roi = ((revenue_estimate - campaign.spent) / campaign.spent * 100) if campaign.spent > 0 else 0

        # Recommendations
        recommendations = []
        if completion_rate < 50:
            recommendations.append("Accelerate task completion — consider adding resources")
        if campaign.spent > campaign.budget * 0.8:
            recommendations.append("Budget nearly exhausted — review spend allocation")
        if not recommendations:
            recommendations.append("Campaign on track — continue current execution")

        return CampaignReport(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            status=campaign.status,
            metrics_summary={
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "budget": campaign.budget,
                "spent": campaign.spent,
                "roi_estimate": roi,
            },
            agent_contributions=agent_contributions,
            deliverables_status=deliverables_status,
            roi_estimate=roi,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
        )

    async def update_campaign_metrics(
        self,
        campaign_id: str,
        metrics: Dict[str, float],
    ) -> Campaign:
        """Update campaign metrics."""
        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            current_metrics = campaign.metrics or {}
            current_metrics.update(metrics)
            campaign.metrics = current_metrics

            db.commit()
            return await self.get_campaign(campaign_id)
        finally:
            db.close()

    async def add_deliverable(
        self,
        campaign_id: str,
        deliverable: Dict[str, Any],
    ) -> Campaign:
        """Add a deliverable to a campaign."""
        db = SessionLocal()
        try:
            campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            deliverables = list(campaign.deliverables or [])
            deliverable["id"] = deliverable.get("id") or str(uuid.uuid4())
            deliverable["created_at"] = datetime.utcnow().isoformat()
            deliverables.append(deliverable)
            campaign.deliverables = deliverables

            db.commit()
            return await self.get_campaign(campaign_id)
        finally:
            db.close()


# Global instance
campaign_engine = CampaignEngine()
