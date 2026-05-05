"""
Claude Mythos — Client Onboarding Service
5-step guided onboarding: Business Info, Marketing Goals, Region & Audience,
Brand Voice, Package Selection. Saves progress, auto-assigns agents, triggers welcome.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import SessionLocal, generate_uuid
from app.services.service_catalog import (
    AGENT_SERVICE_MAP,
    PACKAGES,
    ServiceCatalog,
    service_catalog,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# IN-MEMORY ONBOARDING SESSION STORE
# ═══════════════════════════════════════════════════════════════════

class OnboardingSessionStore:
    """In-memory store for onboarding sessions with TTL cleanup."""

    _sessions: Dict[str, Dict[str, Any]] = {}
    _ttl_hours = 72  # Sessions expire after 72 hours of inactivity

    @classmethod
    def create_session(cls) -> str:
        """Create a new onboarding session."""
        session_id = f"obs_{uuid.uuid4().hex[:16]}"
        cls._sessions[session_id] = {
            "session_id": session_id,
            "current_step": 1,
            "completed_steps": [],
            "data": {},
            "status": "in_progress",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "client_id": None,
            "subscription_id": None,
        }
        return session_id

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID, checking TTL."""
        session = cls._sessions.get(session_id)
        if not session:
            return None

        # Check TTL
        updated = datetime.fromisoformat(session["updated_at"])
        if datetime.utcnow() - updated > timedelta(hours=cls._ttl_hours):
            session["status"] = "expired"
            return session

        return session

    @classmethod
    def save_step(cls, session_id: str, step_number: int, data: Dict[str, Any]) -> bool:
        """Save data for a specific step."""
        session = cls._sessions.get(session_id)
        if not session:
            return False

        session["data"][f"step_{step_number}"] = data
        session["updated_at"] = datetime.utcnow().isoformat()

        if step_number not in session["completed_steps"]:
            session["completed_steps"].append(step_number)

        # Auto-advance current step if completed
        if step_number >= session["current_step"]:
            session["current_step"] = min(step_number + 1, 6)

        return True

    @classmethod
    def complete_session(cls, session_id: str, client_id: str, subscription_id: str):
        """Mark session as completed."""
        session = cls._sessions.get(session_id)
        if session:
            session["status"] = "completed"
            session["client_id"] = client_id
            session["subscription_id"] = subscription_id
            session["completed_at"] = datetime.utcnow().isoformat()
            session["updated_at"] = datetime.utcnow().isoformat()

    @classmethod
    def get_progress(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a session."""
        session = cls.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "current_step": session["current_step"],
            "completed_steps": session["completed_steps"],
            "total_steps": 5,
            "status": session["status"],
            "step_data_summary": {
                step_key: list(data.keys())
                for step_key, data in session["data"].items()
            },
            "is_complete": len(session["completed_steps"]) >= 5,
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
        }


# ═══════════════════════════════════════════════════════════════════
# STEP VALIDATORS
# ═══════════════════════════════════════════════════════════════════

STEP_FIELDS = {
    1: ["company_name", "industry", "website", "contact_name", "contact_email", "contact_phone", "company_size", "annual_revenue"],
    2: ["primary_goals", "target_audience_description", "current_marketing_spend", "previous_agency_experience", "key_challenges"],
    3: ["primary_market", "languages_needed", "platform_preferences", "cultural_considerations", "competitor_regions"],
    4: ["tone_preference", "competitor_brands", "things_to_avoid", "brand_guidelines_url", "brand_personality", "visual_style"],
    5: ["selected_package", "selected_addons", "billing_cycle", "contract_accepted", "stripe_checkout_session_id"],
}


def _validate_step_data(step_number: int, data: Dict[str, Any]) -> List[str]:
    """Validate step data and return list of missing required fields."""
    required = {
        1: ["company_name", "industry", "contact_name", "contact_email"],
        2: ["primary_goals"],
        3: ["primary_market"],
        4: ["tone_preference"],
        5: ["selected_package", "contract_accepted"],
    }

    missing = []
    for field in required.get(step_number, []):
        if field not in data or data[field] is None or data[field] == "":
            missing.append(field)
    return missing


# ═══════════════════════════════════════════════════════════════════
# CLIENT ONBOARDING SERVICE
# ═══════════════════════════════════════════════════════════════════

class ClientOnboardingService:
    """
    5-step client onboarding flow with progress persistence,
    auto agent assignment, and welcome sequence triggering.
    """

    async def start_onboarding(self) -> str:
        """Start a new onboarding session and return the session ID."""
        session_id = OnboardingSessionStore.create_session()
        logger.info(f"New onboarding session started: {session_id}")
        return session_id

    async def save_step(self, session_id: str, step_number: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save data for a specific onboarding step.

        Args:
            session_id: The onboarding session ID
            step_number: 1-5
            data: Step-specific data dict

        Returns:
            Dict with success status, missing fields, and next step info
        """
        if step_number < 1 or step_number > 5:
            return {"error": "Invalid step number. Must be 1-5."}

        session = OnboardingSessionStore.get_session(session_id)
        if not session:
            return {"error": "Session not found or expired"}

        if session["status"] == "expired":
            return {"error": "Session has expired. Please start a new onboarding."}

        # Validate
        missing = _validate_step_data(step_number, data)
        if missing:
            return {
                "success": False,
                "missing_required_fields": missing,
                "message": f"Missing required fields: {', '.join(missing)}",
            }

        # Save
        success = OnboardingSessionStore.save_step(session_id, step_number, data)
        if not success:
            return {"error": "Failed to save step data"}

        # Get updated progress
        progress = OnboardingSessionStore.get_progress(session_id)

        return {
            "success": True,
            "step_saved": step_number,
            "current_step": progress["current_step"],
            "completed_steps": progress["completed_steps"],
            "is_complete": progress["is_complete"],
            "next_step": progress["current_step"] if progress["current_step"] <= 5 else None,
        }

    async def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current onboarding progress."""
        return OnboardingSessionStore.get_progress(session_id)

    async def complete_onboarding(self, session_id: str) -> Dict[str, Any]:
        """
        Complete the onboarding process:
        1. Validate all steps are complete
        2. Create client in database
        3. Assign agents based on package
        4. Trigger welcome sequence
        5. Generate client brief

        Returns:
            Dict with client_id, subscription_id, assigned_agents, brief
        """
        session = OnboardingSessionStore.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        if len(session["completed_steps"]) < 5:
            missing_steps = [s for s in range(1, 6) if s not in session["completed_steps"]]
            return {
                "error": "Onboarding incomplete",
                "missing_steps": missing_steps,
                "message": f"Please complete steps: {missing_steps}",
            }

        try:
            # Extract data from all steps
            step1 = session["data"].get("step_1", {})
            step2 = session["data"].get("step_2", {})
            step3 = session["data"].get("step_3", {})
            step4 = session["data"].get("step_4", {})
            step5 = session["data"].get("step_5", {})

            package_id = step5.get("selected_package", "starter")

            # 1. Create client in database
            client_id = await self._create_client_record(
                step1, step2, step3, step4, package_id
            )

            # 2. Auto-assign team
            assigned_agents = await self.auto_assign_team(client_id, package_id)

            # 3. Trigger welcome sequence
            await self.trigger_welcome_sequence(client_id, assigned_agents)

            # 4. Generate client brief
            brief = await self.generate_client_brief(session_id)

            # 5. Mark session complete
            OnboardingSessionStore.complete_session(session_id, client_id, "pending_subscription")

            logger.info(f"Onboarding completed for client {client_id} with package {package_id}")

            return {
                "success": True,
                "client_id": client_id,
                "subscription_id": "pending_payment",  # Will be set after Stripe checkout
                "package_id": package_id,
                "assigned_agents": assigned_agents,
                "agent_count": len(assigned_agents),
                "client_brief_summary": brief.get("executive_summary", ""),
                "next_steps": [
                    "Complete Stripe Checkout to activate subscription",
                    "First campaign kickoff will begin within 24 hours",
                    "Your dedicated team will reach out within 1 business day",
                ],
            }

        except Exception as e:
            logger.error(f"Error completing onboarding: {e}")
            return {"error": f"Failed to complete onboarding: {str(e)}"}

    async def auto_assign_team(self, client_id: str, package_id: str) -> List[Dict[str, Any]]:
        """
        Auto-assign agents to a client based on their selected package.

        Args:
            client_id: The newly created client ID
            package_id: 'starter', 'growth', or 'enterprise'

        Returns:
            List of assigned agent details
        """
        package = PACKAGES.get(package_id)
        if not package:
            package = PACKAGES["starter"]

        assigned = []
        db = SessionLocal()

        try:
            from app.agents.registry import get_agent
            from app.core.database import ClientModel

            for agent_id in package["agents"]:
                agent = get_agent(agent_id)
                if agent:
                    assigned.append({
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "role": agent.role,
                        "title": agent.title,
                        "avatar": agent.avatar,
                        "service": AGENT_SERVICE_MAP.get(agent_id, ""),
                    })

            # Update client with assigned agents
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if client:
                client.assigned_agents = [a["agent_id"] for a in assigned]
                db.commit()

            logger.info(f"Assigned {len(assigned)} agents to client {client_id}")
            return assigned
        except Exception as e:
            logger.error(f"Error assigning team: {e}")
            return []
        finally:
            db.close()

    async def trigger_welcome_sequence(
        self, client_id: str, assigned_agents: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger welcome messages to relevant agents for a new client.

        Args:
            client_id: The new client ID
            assigned_agents: Pre-computed list of assigned agents

        Returns:
            Dict with welcome messages sent
        """
        try:
            db = SessionLocal()
            from app.core.database import ClientModel, MessageModel

            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client:
                return {"error": "Client not found"}

            messages_sent = []

            # Welcome message from Jon (CEO) to the client
            ceo_welcome = (
                f"Welcome to Claude Mythos, {client.name}! I'm Jon, the CEO. "
                f"Your dedicated team is assembled and ready to deliver exceptional results. "
                f"We'll have our first strategy session scheduled within 24 hours. "
                f"If you ever need me directly, just send a message."
            )
            db.add(MessageModel(
                id=generate_uuid(),
                from_agent="jon",
                to_agent="davos",  # Davos relays to client
                content=ceo_welcome,
                message_type="welcome",
                metadata={"client_id": client_id, "package_id": client.package_id},
            ))
            messages_sent.append({"from": "jon", "to": "davos", "type": "ceo_welcome"})

            # Davos (Client Relations) welcome
            davos_welcome = (
                f"Hello! I'm Davos, your client success lead for {client.name}. "
                f"I'll be your main point of contact. I'll be setting up our kickoff call "
                f"and ensuring everything runs smoothly. Expect to hear from me within the hour!"
            )
            db.add(MessageModel(
                id=generate_uuid(),
                from_agent="davos",
                to_agent="jon",
                content=davos_welcome,
                message_type="welcome",
                metadata={"client_id": client_id},
            ))
            messages_sent.append({"from": "davos", "to": "jon", "type": "client_success_welcome"})

            # Brienne (Project Management) sets up project
            brienne_task = (
                f"New client onboarding: {client.name}. Industry: {client.industry}. "
                f"Setting up project structure, timelines, and initial sprint plan. "
                f"Will coordinate with all assigned team members."
            )
            db.add(MessageModel(
                id=generate_uuid(),
                from_agent="brienne",
                to_agent="jon",
                content=brienne_task,
                message_type="task",
                metadata={"client_id": client_id, "action": "setup_project"},
            ))
            messages_sent.append({"from": "brienne", "to": "jon", "type": "project_setup"})

            # Send welcome messages to each assigned agent
            if assigned_agents:
                for agent_info in assigned_agents:
                    agent_id = agent_info["agent_id"]
                    if agent_id in ("jon", "davos", "brienne"):
                        continue  # Already messaged

                    welcome_msg = (
                        f"New assignment: {client.name} ({client.industry}). "
                        f"Region: {client.region}. Package: {client.package_id or 'starter'}. "
                        f"Please review the client brief and prepare your initial strategy."
                    )
                    db.add(MessageModel(
                        id=generate_uuid(),
                        from_agent="jon",
                        to_agent=agent_id,
                        content=welcome_msg,
                        message_type="welcome",
                        metadata={"client_id": client_id, "agent_role": agent_info.get("role", "")},
                    ))
                    messages_sent.append({"from": "jon", "to": agent_id, "type": "agent_assignment"})

            db.commit()
            logger.info(f"Welcome sequence triggered for client {client_id}: {len(messages_sent)} messages")
            return {"messages_sent": len(messages_sent), "details": messages_sent}

        except Exception as e:
            logger.error(f"Error triggering welcome sequence: {e}")
            return {"error": str(e)}

    async def generate_client_brief(self, session_id: str) -> Dict[str, Any]:
        """
        Compile a comprehensive client brief from all onboarding data.

        Args:
            session_id: The onboarding session ID

        Returns:
            Compiled brief document
        """
        session = OnboardingSessionStore.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        step1 = session["data"].get("step_1", {})
        step2 = session["data"].get("step_2", {})
        step3 = session["data"].get("step_3", {})
        step4 = session["data"].get("step_4", {})
        step5 = session["data"].get("step_5", {})
        package_id = step5.get("selected_package", "starter")
        package = PACKAGES.get(package_id, {})

        goals = step2.get("primary_goals", [])
        if isinstance(goals, str):
            goals = [goals]

        brief = {
            "brief_id": f"brief_{uuid.uuid4().hex[:12]}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": (
                f"{step1.get('company_name', 'Unknown')} is a "
                f"{step1.get('company_size', 'small')} company in the "
                f"{step1.get('industry', 'unknown')} industry, looking to "
                f"achieve {', '.join(g[:3]) if goals else 'marketing growth'} "
                f"through the {package.get('name', 'Starter')} package."
            ),
            "company_profile": {
                "name": step1.get("company_name", ""),
                "industry": step1.get("industry", ""),
                "website": step1.get("website", ""),
                "size": step1.get("company_size", ""),
                "annual_revenue": step1.get("annual_revenue", ""),
                "contact": {
                    "name": step1.get("contact_name", ""),
                    "email": step1.get("contact_email", ""),
                    "phone": step1.get("contact_phone", ""),
                },
            },
            "marketing_goals": {
                "primary_objectives": goals,
                "target_audience": step2.get("target_audience_description", ""),
                "current_spend": step2.get("current_marketing_spend", ""),
                "previous_agency": step2.get("previous_agency_experience", ""),
                "key_challenges": step2.get("key_challenges", []),
            },
            "market_profile": {
                "primary_market": step3.get("primary_market", ""),
                "languages": step3.get("languages_needed", []),
                "platforms": step3.get("platform_preferences", []),
                "cultural_notes": step3.get("cultural_considerations", ""),
                "competitor_regions": step3.get("competitor_regions", []),
            },
            "brand_voice": {
                "tone": step4.get("tone_preference", ""),
                "brand_personality": step4.get("brand_personality", ""),
                "visual_style": step4.get("visual_style", ""),
                "admired_brands": step4.get("competitor_brands", []),
                "avoid": step4.get("things_to_avoid", []),
                "guidelines_url": step4.get("brand_guidelines_url", ""),
            },
            "selected_package": {
                "id": package_id,
                "name": package.get("name", ""),
                "price_monthly": package.get("price_monthly", 0),
                "campaigns": package.get("campaigns", 0),
                "agent_count": len(package.get("agents", [])),
                "billing_cycle": step5.get("billing_cycle", "monthly"),
                "selected_addons": step5.get("selected_addons", []),
            },
            "recommended_first_campaigns": self._suggest_first_campaigns(
                goals, step3.get("primary_market", ""), step1.get("industry", "")
            ),
            "team_assigned": [
                {"agent_id": aid, "service": AGENT_SERVICE_MAP.get(aid, "")}
                for aid in package.get("agents", [])
            ],
        }

        return brief

    def _suggest_first_campaigns(
        self, goals: List[str], primary_market: str, industry: str
    ) -> List[Dict[str, str]]:
        """Suggest initial campaigns based on goals and market."""
        suggestions = []
        goal_str = " ".join(g.lower() for g in goals)

        if "awareness" in goal_str or "reach" in goal_str or "brand" in goal_str:
            suggestions.append({
                "name": f"Brand Awareness Launch — {primary_market}",
                "objective": "Build brand recognition and reach in target market",
                "channels": "Social media, display, video",
                "estimated_duration": "4-6 weeks",
                "lead_agents": ["missandei", "rhaegar", "bronn"],
            })

        if "leads" in goal_str or "conversion" in goal_str or "sales" in goal_str:
            suggestions.append({
                "name": f"Lead Generation — {industry}",
                "objective": "Generate qualified leads through paid and organic channels",
                "channels": "Paid search, social ads, landing pages, email",
                "estimated_duration": "6-8 weeks",
                "lead_agents": ["bronn", "greyworm", "margaery", "tyrion"],
            })

        if "engagement" in goal_str or "community" in goal_str:
            suggestions.append({
                "name": "Community Building & Engagement",
                "objective": "Grow and engage community across social platforms",
                "channels": "Social media, email, content",
                "estimated_duration": "Ongoing",
                "lead_agents": ["missandei", "tyrion", "margaery"],
            })

        if "seo" in goal_str or "organic" in goal_str:
            suggestions.append({
                "name": f"SEO Foundation — {industry}",
                "objective": "Build organic search visibility and traffic",
                "channels": "SEO, content, technical optimization",
                "estimated_duration": "3-6 months (ongoing)",
                "lead_agents": ["sandoq", "tyrion", "samwell"],
            })

        if not suggestions:
            suggestions.append({
                "name": f"Market Entry — {primary_market}",
                "objective": "Establish presence and test messaging in target market",
                "channels": "Social media, paid ads, content",
                "estimated_duration": "4-6 weeks",
                "lead_agents": ["missandei", "bronn", "bran"],
            })

        return suggestions

    # ── Internal Helpers ─────────────────────────────────────────

    async def _create_client_record(
        self,
        step1: Dict[str, Any],
        step2: Dict[str, Any],
        step3: Dict[str, Any],
        step4: Dict[str, Any],
        package_id: str,
    ) -> str:
        """Create a client record in the database from onboarding data."""
        db = SessionLocal()
        try:
            from app.core.database import ClientModel

            goals = step2.get("primary_goals", [])
            if isinstance(goals, str):
                goals = [goals]

            client_id = generate_uuid()
            client = ClientModel(
                id=client_id,
                name=step1.get("company_name", "Unknown"),
                industry=step1.get("industry", "Other"),
                region=step3.get("primary_market", "Global"),
                timezone=step3.get("timezone", "UTC"),
                target_audience=step2.get("target_audience_description", ""),
                brand_voice=step4.get("tone_preference", ""),
                goals=goals,
                budget_range=step2.get("current_marketing_spend", ""),
                contact_name=step1.get("contact_name", ""),
                contact_email=step1.get("contact_email", ""),
                contact_phone=step1.get("contact_phone", ""),
                notes=json.dumps({
                    "onboarding_completed": datetime.utcnow().isoformat(),
                    "company_size": step1.get("company_size", ""),
                    "annual_revenue": step1.get("annual_revenue", ""),
                    "website": step1.get("website", ""),
                    "languages_needed": step3.get("languages_needed", []),
                    "platform_preferences": step3.get("platform_preferences", []),
                    "cultural_considerations": step3.get("cultural_considerations", ""),
                    "brand_personality": step4.get("brand_personality", ""),
                    "visual_style": step4.get("visual_style", ""),
                    "things_to_avoid": step4.get("things_to_avoid", []),
                    "previous_agency": step2.get("previous_agency_experience", ""),
                    "key_challenges": step2.get("key_challenges", []),
                }),
                status="active",
                package_id=package_id,
                subscription_status="trialing" if package_id == "starter" else "pending",
            )
            db.add(client)
            db.commit()

            logger.info(f"Client record created: {client_id} — {client.name}")
            return client_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating client record: {e}")
            raise
        finally:
            db.close()


# ═══════════════════════════════════════════════════════════════════
# Global instance
# ═══════════════════════════════════════════════════════════════════

onboarding_service = ClientOnboardingService()
