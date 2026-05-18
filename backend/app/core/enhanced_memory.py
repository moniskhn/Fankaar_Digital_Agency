"""
Fankaar Digital -- Enhanced Agent Memory System
Rich, human-like memory with 4 types:
  A. Episodic Memory  -- "What happened" (events, experiences)
  B. Semantic Memory  -- "What I know" (facts, knowledge, insights)
  C. Procedural Memory -- "How I do things" (patterns, workflows)
  D. Client-Specific Memory -- "Everything about each client"

Completely replaces memory.py imports.  Backwards-compatible with AgentMemory.
"""

import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session

from app.core.database import (
    ActivityLogModel,
    AgentClientMemoryModel,
    AgentEpisodeModel,
    AgentFactModel,
    AgentPatternModel,
    MessageModel,
    SessionLocal,
    ClientModel,
    CampaignModel,
)


# ═══════════════════════════════════════════════════════════════
# EnhancedAgentMemory
# ═══════════════════════════════════════════════════════════════

class EnhancedAgentMemory:
    """
    Rich, human-like persistent memory for a single agent.

    Four memory compartments:
      * Episodic  -- events with timestamps, emotions, importance
      * Semantic  -- facts / knowledge with confidence scores
      * Procedural -- reusable patterns, workflows, templates
      * Client    -- per-client namespaces (brand voice, prefs, ...)
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    # ── DB helpers ─────────────────────────────────────────────

    def _get_db(self) -> Session:
        return SessionLocal()

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _ago(self, days: int) -> datetime:
        return self._now() - timedelta(days=days)

    # ═══════════════════════════════════════════════════════════
    # A. EPISODIC MEMORY  -- "What happened"
    # ═══════════════════════════════════════════════════════════

    def record_episode(
        self,
        event_type: str,
        description: str,
        client_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        importance: int = 5,
        emotions: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record an event in episodic memory.

        Args:
            event_type: e.g. task_completed, conversation, decision, feedback
            description: Human-readable description of what happened
            client_id: Optional associated client
            campaign_id: Optional associated campaign
            importance: 1-10 (10 = career-defining moment)
            emotions: {"valence": "positive|negative|neutral", "intensity": 1-10}

        Returns:
            The episode ID.
        """
        db = self._get_db()
        try:
            episode = AgentEpisodeModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                event_type=event_type,
                description=description,
                client_id=client_id,
                campaign_id=campaign_id,
                importance=max(1, min(10, importance)),
                emotions=emotions or {"valence": "neutral", "intensity": 5},
                timestamp=self._now(),
            )
            db.add(episode)
            db.commit()

            # Also auto-extract a semantic fact if the episode looks insightful
            self._auto_extract_fact_from_episode(db, episode)

            return episode.id
        finally:
            db.close()

    def _auto_extract_fact_from_episode(self, db: Session, episode: AgentEpisodeModel) -> None:
        """If an episode contains a clear learning, auto-create a semantic fact."""
        # Only high-importance positive learnings become auto-facts
        if episode.importance >= 7 and episode.emotions.get("valence") == "positive":
            fact_key = f"auto_{episode.event_type}_{episode.client_id or 'general'}"
            # Check if fact already exists
            existing = (
                db.query(AgentFactModel)
                .filter_by(agent_id=self.agent_id, key=fact_key)
                .first()
            )
            if not existing:
                fact = AgentFactModel(
                    id=str(uuid.uuid4()),
                    agent_id=self.agent_id,
                    key=fact_key,
                    value=episode.description[:500],
                    category="auto_learned",
                    client_id=episode.client_id,
                    confidence=0.6,
                    source="episode",
                )
                db.add(fact)
                db.commit()

    def get_episodes(
        self,
        client_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since_days: int = 30,
        min_importance: int = 1,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve episodic memories with flexible filtering."""
        db = self._get_db()
        try:
            query = db.query(AgentEpisodeModel).filter(
                AgentEpisodeModel.agent_id == self.agent_id,
                AgentEpisodeModel.importance >= min_importance,
                AgentEpisodeModel.timestamp >= self._ago(since_days),
            )
            if client_id:
                query = query.filter(AgentEpisodeModel.client_id == client_id)
            if campaign_id:
                query = query.filter(AgentEpisodeModel.campaign_id == campaign_id)
            if event_type:
                query = query.filter(AgentEpisodeModel.event_type == event_type)

            episodes = query.order_by(desc(AgentEpisodeModel.timestamp)).limit(limit).all()
            return [ep.to_dict() for ep in episodes]
        finally:
            db.close()

    def summarize_week(self) -> str:
        """Auto-summarize the past week's episodes into key experiences."""
        db = self._get_db()
        try:
            week_ago = self._ago(7)
            episodes = (
                db.query(AgentEpisodeModel)
                .filter(
                    AgentEpisodeModel.agent_id == self.agent_id,
                    AgentEpisodeModel.timestamp >= week_ago,
                )
                .order_by(desc(AgentEpisodeModel.importance))
                .all()
            )

            if not episodes:
                return f"[{self.agent_id}] No significant episodes this week."

            # Group by event type
            by_type: Dict[str, List[AgentEpisodeModel]] = {}
            total_importance = 0
            positive_count = 0
            negative_count = 0

            for ep in episodes:
                by_type.setdefault(ep.event_type, []).append(ep)
                total_importance += ep.importance
                valence = (ep.emotions or {}).get("valence", "neutral")
                if valence == "positive":
                    positive_count += 1
                elif valence == "negative":
                    negative_count += 1

            lines = [
                f"WEEKLY SUMMARY for {self.agent_id}",
                f"  {len(episodes)} episodes | Avg importance: {total_importance / len(episodes):.1f}/10",
                f"  Sentiment: {positive_count} positive, {negative_count} negative",
                "",
            ]

            for event_type, eps in sorted(by_type.items(), key=lambda x: -len(x[1])):
                lines.append(f"  [{event_type.upper()}] ({len(eps)} events)")
                for ep in sorted(eps, key=lambda e: -e.importance)[:3]:
                    emoji = "+" if (ep.emotions or {}).get("valence") == "positive" else "~"
                    lines.append(f"    {emoji} [{ep.importance}/10] {ep.description[:120]}")

            summary_text = "\n".join(lines)

            # Store the summary back onto each high-importance episode
            for ep in episodes:
                if ep.importance >= 7:
                    ep.summary = summary_text[:500]
            db.commit()

            return summary_text
        finally:
            db.close()

    def search_episodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Keyword-search episode descriptions."""
        db = self._get_db()
        try:
            like_q = f"%{query}%"
            episodes = (
                db.query(AgentEpisodeModel)
                .filter(
                    AgentEpisodeModel.agent_id == self.agent_id,
                    or_(
                        AgentEpisodeModel.description.ilike(like_q),
                        AgentEpisodeModel.event_type.ilike(like_q),
                        AgentEpisodeModel.client_id.ilike(like_q),
                    ),
                )
                .order_by(desc(AgentEpisodeModel.timestamp))
                .limit(limit)
                .all()
            )
            return [ep.to_dict() for ep in episodes]
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # B. SEMANTIC MEMORY  -- "What I know"
    # ═══════════════════════════════════════════════════════════

    def learn_fact(
        self,
        key: str,
        value: str,
        category: str = "general",
        client_id: Optional[str] = None,
        confidence: float = 1.0,
        source: str = "task",
    ) -> str:
        """Learn (store) a fact in semantic memory.

        If a fact with the same key already exists, updates confidence
        and value (merging knowledge).
        """
        db = self._get_db()
        try:
            existing = (
                db.query(AgentFactModel)
                .filter_by(agent_id=self.agent_id, key=key)
                .first()
            )

            if existing:
                # Merge: update value and boost confidence slightly
                existing.value = value
                existing.confidence = min(1.0, max(existing.confidence, confidence) + 0.05)
                existing.access_count = 0
                existing.timestamp = self._now()
                db.commit()
                return existing.id

            fact = AgentFactModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                key=key,
                value=value,
                category=category,
                client_id=client_id,
                confidence=max(0.0, min(1.0, confidence)),
                source=source,
                timestamp=self._now(),
            )
            db.add(fact)
            db.commit()
            return fact.id
        finally:
            db.close()

    def recall_fact(self, key: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Recall a single fact by key, incrementing its access count."""
        db = self._get_db()
        try:
            query = db.query(AgentFactModel).filter(
                AgentFactModel.agent_id == self.agent_id,
                AgentFactModel.key == key,
            )
            if client_id:
                query = query.filter(AgentFactModel.client_id == client_id)

            fact = query.first()
            if fact:
                fact.access_count = (fact.access_count or 0) + 1
                db.commit()
                return fact.to_dict()
            return {}
        finally:
            db.close()

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        client_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Keyword-search facts by key, value, or category."""
        db = self._get_db()
        try:
            like_q = f"%{query}%"
            q = db.query(AgentFactModel).filter(
                AgentFactModel.agent_id == self.agent_id,
                or_(
                    AgentFactModel.key.ilike(like_q),
                    AgentFactModel.value.ilike(like_q),
                    AgentFactModel.category.ilike(like_q),
                ),
            )
            if category:
                q = q.filter(AgentFactModel.category == category)
            if client_id:
                q = q.filter(AgentFactModel.client_id == client_id)

            facts = q.order_by(desc(AgentFactModel.confidence)).limit(limit).all()

            # Bump access counts
            for f in facts:
                f.access_count = (f.access_count or 0) + 1
            db.commit()

            return [fact.to_dict() for fact in facts]
        finally:
            db.close()

    def get_client_knowledge(self, client_id: str) -> Dict[str, Any]:
        """Return every known fact about a specific client."""
        db = self._get_db()
        try:
            facts = (
                db.query(AgentFactModel)
                .filter(
                    AgentFactModel.agent_id == self.agent_id,
                    AgentFactModel.client_id == client_id,
                )
                .order_by(desc(AgentFactModel.confidence))
                .all()
            )

            categories: Dict[str, List[Dict]] = {}
            for f in facts:
                categories.setdefault(f.category, []).append(f.to_dict())

            return {
                "client_id": client_id,
                "agent_id": self.agent_id,
                "total_facts": len(facts),
                "by_category": categories,
            }
        finally:
            db.close()

    def get_all_knowledge(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all facts, optionally filtered by category."""
        db = self._get_db()
        try:
            query = db.query(AgentFactModel).filter(
                AgentFactModel.agent_id == self.agent_id
            )
            if category:
                query = query.filter(AgentFactModel.category == category)
            facts = query.order_by(desc(AgentFactModel.confidence)).all()
            return [f.to_dict() for f in facts]
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # C. PROCEDURAL MEMORY  -- "How I do things"
    # ═══════════════════════════════════════════════════════════

    def record_pattern(
        self,
        pattern_name: str,
        description: str,
        context: str,
        success_rating: float,
        client_type: Optional[str] = None,
    ) -> str:
        """Record a successful (or unsuccessful) pattern / workflow.

        Args:
            pattern_name: Short identifier, e.g. "dubai_headline_formula_v1"
            description: Detailed description of the pattern
            context: Domain, e.g. "copywriting", "seo", "research"
            success_rating: 0.0-1.0 (how well it worked)
            client_type: e.g. "luxury", "startup", "enterprise"
        """
        db = self._get_db()
        try:
            # Check if pattern already exists -- update success rating
            existing = (
                db.query(AgentPatternModel)
                .filter_by(
                    agent_id=self.agent_id,
                    pattern_name=pattern_name,
                )
                .first()
            )

            if existing:
                # Weighted average of success ratings
                old_rating = existing.success_rating or 0.5
                old_count = existing.usage_count or 0
                new_count = old_count + 1
                blended = ((old_rating * old_count) + success_rating) / new_count
                existing.success_rating = round(blended, 3)
                existing.usage_count = new_count
                existing.description = description  # Keep latest version
                db.commit()
                return existing.id

            pattern = AgentPatternModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                pattern_name=pattern_name,
                description=description,
                context=context,
                success_rating=max(0.0, min(1.0, success_rating)),
                usage_count=1,
                client_type=client_type,
                timestamp=self._now(),
            )
            db.add(pattern)
            db.commit()
            return pattern.id
        finally:
            db.close()

    def get_patterns(
        self,
        context: Optional[str] = None,
        client_type: Optional[str] = None,
        min_rating: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Retrieve procedural patterns with filtering."""
        db = self._get_db()
        try:
            query = db.query(AgentPatternModel).filter(
                AgentPatternModel.agent_id == self.agent_id,
                AgentPatternModel.success_rating >= min_rating,
            )
            if context:
                query = query.filter(AgentPatternModel.context == context)
            if client_type:
                query = query.filter(AgentPatternModel.client_type == client_type)

            patterns = query.order_by(desc(AgentPatternModel.success_rating)).all()
            return [p.to_dict() for p in patterns]
        finally:
            db.close()

    def get_best_practices(
        self,
        task_type: str,
        client_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get the top-rated patterns for a given task type.

        Args:
            task_type: e.g. "copywriting", "seo", "research", "design"
            client_type: Optional client segment filter
        """
        db = self._get_db()
        try:
            query = db.query(AgentPatternModel).filter(
                AgentPatternModel.agent_id == self.agent_id,
                AgentPatternModel.context.ilike(f"%{task_type}%"),
                AgentPatternModel.success_rating >= 0.6,
            )
            if client_type:
                query = query.filter(
                    or_(
                        AgentPatternModel.client_type == client_type,
                        AgentPatternModel.client_type.is_(None),
                    )
                )

            patterns = query.order_by(
                desc(AgentPatternModel.success_rating),
                desc(AgentPatternModel.usage_count),
            ).limit(10).all()
            return [p.to_dict() for p in patterns]
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # D. CLIENT-SPECIFIC MEMORY  -- "Everything about each client"
    # ═══════════════════════════════════════════════════════════

    def build_client_profile(self, client_id: str) -> Dict[str, Any]:
        """Compile a full profile of everything known about a client."""
        db = self._get_db()
        try:
            # Get all client memory entries
            memories = (
                db.query(AgentClientMemoryModel)
                .filter(
                    AgentClientMemoryModel.agent_id == self.agent_id,
                    AgentClientMemoryModel.client_id == client_id,
                )
                .order_by(desc(AgentClientMemoryModel.timestamp))
                .all()
            )

            # Get semantic facts about client
            facts = (
                db.query(AgentFactModel)
                .filter(
                    AgentFactModel.agent_id == self.agent_id,
                    AgentFactModel.client_id == client_id,
                )
                .order_by(desc(AgentFactModel.confidence))
                .all()
            )

            # Get recent episodes about client
            episodes = (
                db.query(AgentEpisodeModel)
                .filter(
                    AgentEpisodeModel.agent_id == self.agent_id,
                    AgentEpisodeModel.client_id == client_id,
                    AgentEpisodeModel.timestamp >= self._ago(90),
                )
                .order_by(desc(AgentEpisodeModel.timestamp))
                .limit(20)
                .all()
            )

            # Get applicable patterns
            client_record = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            client_type = "general"
            if client_record and client_record.industry:
                client_type = client_record.industry.lower()

            patterns = self.get_patterns(client_type=client_type)

            # Categorize memories
            by_type: Dict[str, List[str]] = {}
            for m in memories:
                by_type.setdefault(m.memory_type, []).append(m.content)

            return {
                "client_id": client_id,
                "agent_id": self.agent_id,
                "basic_info": {
                    "name": client_record.name if client_record else "Unknown",
                    "industry": client_record.industry if client_record else "Unknown",
                    "region": client_record.region if client_record else "Unknown",
                    "brand_voice": client_record.brand_voice if client_record else "",
                } if client_record else None,
                "memories_by_type": by_type,
                "semantic_facts": [f.to_dict() for f in facts],
                "recent_episodes": [ep.to_dict() for ep in episodes],
                "applicable_patterns": patterns[:5],
                "total_memories": len(memories),
                "total_facts": len(facts),
            }
        finally:
            db.close()

    def update_client_preference(
        self,
        client_id: str,
        preference_type: str,
        value: str,
    ) -> str:
        """Store or update a client preference.

        Args:
            client_id: The client UUID
            preference_type: e.g. "tone", "format", "response_speed", "review_style"
            value: The preference value
        """
        db = self._get_db()
        try:
            # Check for existing preference of this type
            existing = (
                db.query(AgentClientMemoryModel)
                .filter(
                    AgentClientMemoryModel.agent_id == self.agent_id,
                    AgentClientMemoryModel.client_id == client_id,
                    AgentClientMemoryModel.memory_type == f"preference:{preference_type}",
                )
                .first()
            )

            if existing:
                existing.content = value
                existing.timestamp = self._now()
                db.commit()
                return existing.id

            mem = AgentClientMemoryModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                client_id=client_id,
                memory_type=f"preference:{preference_type}",
                content=value,
                timestamp=self._now(),
            )
            db.add(mem)
            db.commit()

            # Also store as semantic fact for easy retrieval
            self.learn_fact(
                key=f"client_{client_id}_{preference_type}",
                value=value,
                category="client_preference",
                client_id=client_id,
                confidence=0.9,
                source="explicit_preference",
            )

            return mem.id
        finally:
            db.close()

    def get_client_history(self, client_id: str) -> Dict[str, Any]:
        """Get full interaction history with a client."""
        db = self._get_db()
        try:
            # All episodes
            episodes = (
                db.query(AgentEpisodeModel)
                .filter(
                    AgentEpisodeModel.agent_id == self.agent_id,
                    AgentEpisodeModel.client_id == client_id,
                )
                .order_by(desc(AgentEpisodeModel.timestamp))
                .all()
            )

            # All client memories
            memories = (
                db.query(AgentClientMemoryModel)
                .filter(
                    AgentClientMemoryModel.agent_id == self.agent_id,
                    AgentClientMemoryModel.client_id == client_id,
                )
                .order_by(desc(AgentClientMemoryModel.timestamp))
                .all()
            )

            # Campaigns worked on
            campaign_ids = list({
                ep.campaign_id for ep in episodes if ep.campaign_id
            })

            return {
                "client_id": client_id,
                "agent_id": self.agent_id,
                "total_interactions": len(episodes),
                "episodes": [ep.to_dict() for ep in episodes],
                "memories": [m.to_dict() for m in memories],
                "campaigns_worked": campaign_ids,
            }
        finally:
            db.close()

    def remember_client_feedback(
        self,
        client_id: str,
        deliverable_type: str,
        feedback: str,
        rating: int,
    ) -> str:
        """Record client feedback on a deliverable.

        Args:
            client_id: The client
            deliverable_type: e.g. "copy", "design", "strategy"
            feedback: Raw feedback text
            rating: 1-5 (5 = loved it)
        """
        db = self._get_db()
        try:
            mem = AgentClientMemoryModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                client_id=client_id,
                memory_type="feedback",
                content=json.dumps({
                    "deliverable_type": deliverable_type,
                    "feedback": feedback,
                    "rating": rating,
                }),
                timestamp=self._now(),
            )
            db.add(mem)
            db.commit()

            # Also store as semantic fact and episode
            sentiment = "positive" if rating >= 4 else "neutral" if rating >= 3 else "negative"

            self.learn_fact(
                key=f"feedback_{client_id}_{deliverable_type}",
                value=f"Rating {rating}/5: {feedback[:300]}",
                category="client_feedback",
                client_id=client_id,
                confidence=0.85 if rating >= 4 else 0.7,
                source="feedback",
            )

            self.record_episode(
                event_type="client_feedback",
                description=f"Received {rating}/5 feedback on {deliverable_type}: {feedback[:200]}",
                client_id=client_id,
                importance=6 if rating <= 2 else 4,
                emotions={"valence": sentiment, "intensity": rating * 2},
            )

            return mem.id
        finally:
            db.close()

    def add_client_note(
        self,
        client_id: str,
        note: str,
        memory_type: str = "general_note",
        campaign_id: Optional[str] = None,
    ) -> str:
        """Add a free-form note about a client."""
        db = self._get_db()
        try:
            mem = AgentClientMemoryModel(
                id=str(uuid.uuid4()),
                agent_id=self.agent_id,
                client_id=client_id,
                memory_type=memory_type,
                content=note,
                timestamp=self._now(),
                campaign_id=campaign_id,
            )
            db.add(mem)
            db.commit()
            return mem.id
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # Memory for LLM Context  -- THE KEY METHOD
    # ═══════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════

    def get_context_for_task(self, task: Dict[str, Any]) -> str:
        """Build a rich context string for LLM prompt injection.

        This compiles the most relevant episodic, semantic, procedural,
        and client memories into a concise briefing that gets injected
        into the agent's think() call.

        Args:
            task: Dict with keys like 'title', 'description', 'client_id',
                  'campaign_id', 'task_type', etc.

        Returns:
            A formatted context string ready for LLM consumption.
        """
        client_id = task.get("client_id") or task.get("client")
        campaign_id = task.get("campaign_id") or task.get("campaign")
        task_desc = task.get("description", task.get("title", ""))
        task_type = task.get("task_type", "")

        parts: List[str] = []
        parts.append(f"=== MEMORY CONTEXT for {self.agent_id.upper()} ===\n")

        # ── 1. Semantic knowledge relevant to this task ──
        semantic_section = self._build_semantic_context(task_desc, task_type, client_id)
        if semantic_section:
            parts.append(semantic_section)

        # ── 2. Recent relevant episodes ──
        episodic_section = self._build_episodic_context(client_id, campaign_id, task_desc)
        if episodic_section:
            parts.append(episodic_section)

        # ── 3. Procedural patterns / best practices ──
        procedural_section = self._build_procedural_context(task_type, client_id)
        if procedural_section:
            parts.append(procedural_section)

        # ── 4. Client-specific profile ──
        if client_id:
            client_section = self._build_client_context(client_id)
            if client_section:
                parts.append(client_section)

        # ── 5. Conversation continuity ──
        convo_section = self._build_conversation_context()
        if convo_section:
            parts.append(convo_section)

        return "\n".join(parts)

    def _build_semantic_context(
        self, task_desc: str, task_type: str, client_id: Optional[str]
    ) -> str:
        """Gather relevant semantic facts."""
        db = self._get_db()
        try:
            facts: List[AgentFactModel] = []

            # Search by task description keywords
            keywords = self._extract_keywords(task_desc)
            for kw in keywords[:3]:
                found = (
                    db.query(AgentFactModel)
                    .filter(
                        AgentFactModel.agent_id == self.agent_id,
                        or_(
                            AgentFactModel.key.ilike(f"%{kw}%"),
                            AgentFactModel.value.ilike(f"%{kw}%"),
                        ),
                        AgentFactModel.confidence >= 0.5,
                    )
                    .order_by(desc(AgentFactModel.confidence))
                    .limit(3)
                    .all()
                )
                facts.extend(found)

            # If task_type given, search by category
            if task_type:
                cat_facts = (
                    db.query(AgentFactModel)
                    .filter(
                        AgentFactModel.agent_id == self.agent_id,
                        AgentFactModel.category.ilike(f"%{task_type}%"),
                        AgentFactModel.confidence >= 0.5,
                    )
                    .order_by(desc(AgentFactModel.confidence))
                    .limit(5)
                    .all()
                )
                facts.extend(cat_facts)

            # Client-specific facts
            if client_id:
                client_facts = (
                    db.query(AgentFactModel)
                    .filter(
                        AgentFactModel.agent_id == self.agent_id,
                        AgentFactModel.client_id == client_id,
                        AgentFactModel.confidence >= 0.4,
                    )
                    .order_by(desc(AgentFactModel.confidence))
                    .limit(5)
                    .all()
                )
                facts.extend(client_facts)

            # Deduplicate by key
            seen = set()
            unique_facts = []
            for f in facts:
                if f.key not in seen:
                    seen.add(f.key)
                    unique_facts.append(f)

            if not unique_facts:
                return ""

            lines = ["--- What I Know (Semantic Memory) ---"]
            for f in unique_facts[:8]:
                confidence_indicator = "  "
                if f.confidence >= 0.9:
                    confidence_indicator = "* "  # High confidence
                elif f.confidence >= 0.7:
                    confidence_indicator = "+ "  # Good confidence
                lines.append(f"  {confidence_indicator}[{f.category}] {f.key}: {f.value[:200]}")
            return "\n".join(lines) + "\n"
        finally:
            db.close()

    def _build_episodic_context(
        self, client_id: Optional[str], campaign_id: Optional[str], task_desc: str
    ) -> str:
        """Gather relevant recent episodes."""
        db = self._get_db()
        try:
            query = db.query(AgentEpisodeModel).filter(
                AgentEpisodeModel.agent_id == self.agent_id,
                AgentEpisodeModel.timestamp >= self._ago(30),
                AgentEpisodeModel.importance >= 4,
            )

            if client_id:
                query = query.filter(AgentEpisodeModel.client_id == client_id)
            elif campaign_id:
                query = query.filter(AgentEpisodeModel.campaign_id == campaign_id)

            episodes = query.order_by(
                desc(AgentEpisodeModel.importance),
                desc(AgentEpisodeModel.timestamp),
            ).limit(8).all()

            if not episodes:
                return ""

            lines = ["--- Recent Experiences (Episodic Memory) ---"]
            for ep in episodes[:6]:
                ago = self._time_ago(ep.timestamp)
                valence = (ep.emotions or {}).get("valence", "neutral")
                emoji = {"positive": "+", "negative": "-", "neutral": "~"}.get(valence, "~")
                lines.append(
                    f"  [{ago}] {emoji} [{ep.importance}/10] {ep.event_type}: "
                    f"{ep.description[:150]}"
                )
            return "\n".join(lines) + "\n"
        finally:
            db.close()

    def _build_procedural_context(self, task_type: str, client_id: Optional[str]) -> str:
        """Gather relevant patterns and best practices."""
        db = self._get_db()
        try:
            patterns: List[AgentPatternModel] = []

            # Search by task type context
            if task_type:
                p1 = (
                    db.query(AgentPatternModel)
                    .filter(
                        AgentPatternModel.agent_id == self.agent_id,
                        AgentPatternModel.context.ilike(f"%{task_type}%"),
                        AgentPatternModel.success_rating >= 0.5,
                    )
                    .order_by(desc(AgentPatternModel.success_rating))
                    .limit(4)
                    .all()
                )
                patterns.extend(p1)

            # Search by description keywords
            keywords = self._extract_keywords(task_type or "")
            for kw in keywords[:2]:
                p2 = (
                    db.query(AgentPatternModel)
                    .filter(
                        AgentPatternModel.agent_id == self.agent_id,
                        AgentPatternModel.description.ilike(f"%{kw}%"),
                        AgentPatternModel.success_rating >= 0.5,
                    )
                    .order_by(desc(AgentPatternModel.success_rating))
                    .limit(3)
                    .all()
                )
                patterns.extend(p2)

            # Client-type specific patterns
            if client_id:
                client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
                if client and client.industry:
                    p3 = (
                        db.query(AgentPatternModel)
                        .filter(
                            AgentPatternModel.agent_id == self.agent_id,
                            AgentPatternModel.client_type.ilike(f"%{client.industry}%"),
                            AgentPatternModel.success_rating >= 0.5,
                        )
                        .order_by(desc(AgentPatternModel.success_rating))
                        .limit(3)
                        .all()
                    )
                    patterns.extend(p3)

            # Deduplicate
            seen = set()
            unique = []
            for p in patterns:
                if p.id not in seen:
                    seen.add(p.id)
                    unique.append(p)

            if not unique:
                return ""

            lines = ["--- Proven Patterns (Procedural Memory) ---"]
            for p in unique[:5]:
                stars = "*" * int(p.success_rating * 5)
                ct = f" | {p.client_type}" if p.client_type else ""
                lines.append(
                    f"  [{stars}{ct}] {p.pattern_name}: {p.description[:180]}"
                )
            return "\n".join(lines) + "\n"
        finally:
            db.close()

    def _build_client_context(self, client_id: str) -> str:
        """Build a rich client-specific context section."""
        db = self._get_db()
        try:
            # Get client record
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()

            # Get preferences
            prefs = (
                db.query(AgentClientMemoryModel)
                .filter(
                    AgentClientMemoryModel.agent_id == self.agent_id,
                    AgentClientMemoryModel.client_id == client_id,
                    AgentClientMemoryModel.memory_type.like("preference:%"),
                )
                .all()
            )

            # Get recent feedback
            feedback_entries = (
                db.query(AgentClientMemoryModel)
                .filter(
                    AgentClientMemoryModel.agent_id == self.agent_id,
                    AgentClientMemoryModel.client_id == client_id,
                    AgentClientMemoryModel.memory_type == "feedback",
                )
                .order_by(desc(AgentClientMemoryModel.timestamp))
                .limit(3)
                .all()
            )

            lines = [f"--- Client Profile: {client.name if client else client_id} ---"]

            if client:
                lines.append(f"  Industry: {client.industry} | Region: {client.region}")
                if client.brand_voice:
                    lines.append(f"  Brand Voice: {client.brand_voice[:150]}")
                if client.target_audience:
                    lines.append(f"  Audience: {client.target_audience[:150]}")

            if prefs:
                lines.append("  Preferences:")
                for p in prefs:
                    pref_name = p.memory_type.replace("preference:", "")
                    lines.append(f"    - {pref_name}: {p.content[:120]}")

            if feedback_entries:
                lines.append("  Recent Feedback:")
                for fb in feedback_entries:
                    try:
                        fb_data = json.loads(fb.content)
                        lines.append(
                            f"    - {fb_data.get('deliverable_type', '?')}: "
                            f"{fb_data.get('rating', '?')}/5 -- "
                            f"{fb_data.get('feedback', '')[:120]}"
                        )
                    except (json.JSONDecodeError, TypeError):
                        lines.append(f"    - {fb.content[:120]}")

            # Relevant facts about this client
            facts = (
                db.query(AgentFactModel)
                .filter(
                    AgentFactModel.agent_id == self.agent_id,
                    AgentFactModel.client_id == client_id,
                    AgentFactModel.confidence >= 0.5,
                )
                .order_by(desc(AgentFactModel.confidence))
                .limit(4)
                .all()
            )
            if facts:
                lines.append("  Key Learnings:")
                for f in facts:
                    lines.append(f"    - [{f.category}] {f.value[:150]}")

            return "\n".join(lines) + "\n"
        finally:
            db.close()

    def _build_conversation_context(self) -> str:
        """Include very recent conversation history for continuity."""
        db = self._get_db()
        try:
            messages = (
                db.query(MessageModel)
                .filter(
                    (MessageModel.from_agent == self.agent_id)
                    | (MessageModel.to_agent == self.agent_id),
                )
                .order_by(desc(MessageModel.timestamp))
                .limit(5)
                .all()
            )

            if not messages:
                return ""

            lines = ["--- Recent Conversations ---"]
            for m in reversed(messages):
                lines.append(f"  {m.from_agent}: {m.content[:120]}")
            return "\n".join(lines) + "\n"
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # Agent Biography
    # ═══════════════════════════════════════════════════════════

    def get_agent_biography(self) -> str:
        """Generate an auto-updating biography / resume of the agent.

        Summarizes the agent's experiences, knowledge base, specialties,
        and track record across all memory systems.
        """
        db = self._get_db()
        try:
            # Count episodes by type
            episode_counts = (
                db.query(
                    AgentEpisodeModel.event_type,
                    func.count(AgentEpisodeModel.id),
                )
                .filter(AgentEpisodeModel.agent_id == self.agent_id)
                .group_by(AgentEpisodeModel.event_type)
                .all()
            )

            # Count facts by category
            fact_counts = (
                db.query(
                    AgentFactModel.category,
                    func.count(AgentFactModel.id),
                )
                .filter(AgentFactModel.agent_id == self.agent_id)
                .group_by(AgentFactModel.category)
                .all()
            )

            # Top patterns
            top_patterns = (
                db.query(AgentPatternModel)
                .filter(AgentPatternModel.agent_id == self.agent_id)
                .order_by(desc(AgentPatternModel.success_rating))
                .limit(5)
                .all()
            )

            # Recent high-importance episodes (milestones)
            milestones = (
                db.query(AgentEpisodeModel)
                .filter(
                    AgentEpisodeModel.agent_id == self.agent_id,
                    AgentEpisodeModel.importance >= 8,
                )
                .order_by(desc(AgentEpisodeModel.timestamp))
                .limit(5)
                .all()
            )

            # Unique clients worked with
            client_count = (
                db.query(func.count(func.distinct(AgentEpisodeModel.client_id)))
                .filter(AgentEpisodeModel.agent_id == self.agent_id)
                .scalar()
            )

            total_episodes = (
                db.query(func.count(AgentEpisodeModel.id))
                .filter(AgentEpisodeModel.agent_id == self.agent_id)
                .scalar()
            )

            total_facts = (
                db.query(func.count(AgentFactModel.id))
                .filter(AgentFactModel.agent_id == self.agent_id)
                .scalar()
            )

            lines = [
                f"AGENT BIOGRAPHY: {self.agent_id.upper()}",
                "",
                f"  Total Experiences: {total_episodes} episodes",
                f"  Knowledge Base: {total_facts} facts",
                f"  Clients Served: {client_count}",
                "",
                "  EXPERIENCE BREAKDOWN:",
            ]
            for event_type, count in sorted(episode_counts, key=lambda x: -x[1]):
                lines.append(f"    - {event_type}: {count}")

            lines.append("")
            lines.append("  KNOWLEDGE DOMAINS:")
            for category, count in sorted(fact_counts, key=lambda x: -x[1]):
                lines.append(f"    - {category}: {count} facts")

            if top_patterns:
                lines.append("")
                lines.append("  TOP PERFORMING PATTERNS:")
                for p in top_patterns:
                    lines.append(
                        f"    - {p.pattern_name} ({p.success_rating:.0%} success, "
                        f"{p.usage_count} uses)"
                    )

            if milestones:
                lines.append("")
                lines.append("  KEY MILESTONES:")
                for m in milestones:
                    ago = self._time_ago(m.timestamp)
                    lines.append(f"    - [{ago}] {m.description[:150]}")

            return "\n".join(lines)
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════
    # Utility helpers
    # ═══════════════════════════════════════════════════════════

    def _extract_keywords(self, text_str: str) -> List[str]:
        """Extract meaningful keywords from task description."""
        if not text_str:
            return []
        # Simple keyword extraction: meaningful words > 3 chars
        stopwords = {
            "the", "and", "for", "with", "from", "that", "this", "have",
            "has", "had", "will", "would", "could", "should", "may", "might",
            "can", "shall", "about", "into", "through", "during", "before",
            "after", "above", "below", "between", "among", "within", "without",
            "create", "write", "generate", "make", "produce", "build", "develop",
            "using", "based", "need", "want", "require", "please",
        }
        words = re.findall(r"[a-zA-Z]{3,}", text_str.lower())
        keywords = [w for w in words if w not in stopwords]
        # Return unique keywords, preserving rough frequency order
        seen = set()
        result = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                result.append(kw)
        return result[:5]

    @staticmethod
    def _time_ago(dt: Optional[datetime]) -> str:
        """Human-readable relative time."""
        if not dt:
            return "unknown"
        delta = datetime.utcnow() - dt
        if delta.days >= 30:
            return f"{delta.days // 30}mo ago"
        if delta.days >= 1:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours >= 1:
            return f"{hours}h ago"
        mins = delta.seconds // 60
        return f"{mins}m ago"

    # ═══════════════════════════════════════════════════════════
    # Backwards-compatible wrappers (AgentMemory interface)
    # ═══════════════════════════════════════════════════════════

    def add_message(
        self,
        content: str,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        message_type: str = "chat",
        extra_metadata: Optional[Dict[str, Any]] = None,
        campaign_id: Optional[str] = None,
    ) -> str:
        """Backwards-compatible message storage."""
        db = self._get_db()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                from_agent=from_agent or self.agent_id,
                to_agent=to_agent or self.agent_id,
                content=content,
                timestamp=self._now(),
                message_type=message_type,
                extra_metadata=extra_metadata or {},
                campaign_id=campaign_id,
            )
            db.add(msg)
            db.commit()

            # Also record as an episode (lightweight)
            if message_type in ("task", "decision", "report"):
                self.record_episode(
                    event_type=f"message_{message_type}",
                    description=f"{from_agent or self.agent_id} -> {to_agent or self.agent_id}: {content[:200]}",
                    client_id=campaign_id,
                    importance=3,
                )

            return msg.id
        finally:
            db.close()

    def get_conversation_history(
        self,
        with_agent: Optional[str] = None,
        limit: int = 50,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Backwards-compatible conversation retrieval."""
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

            messages = query.order_by(desc(MessageModel.timestamp)).limit(limit).all()
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
        """Get recent conversation context formatted for LLM prompt."""
        history = self.get_conversation_history(limit=limit)
        if not history:
            return "No previous context."
        lines = []
        for msg in history:
            sender = msg["from_agent"]
            content = msg["content"][:200]
            lines.append(f"{sender}: {content}")
        return "\n".join(lines)

    def set_state(self, key: str, value: Any) -> None:
        """Store a state value as a system message."""
        self.add_message(
            content=f"STATE:{key}={json.dumps(value)}",
            from_agent="system",
            to_agent=self.agent_id,
            message_type="system",
            extra_metadata={"state_key": key, "state_value": value},
        )

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a state value."""
        db = self._get_db()
        try:
            msg = (
                db.query(MessageModel)
                .filter(
                    MessageModel.to_agent == self.agent_id,
                    MessageModel.message_type == "system",
                    MessageModel.content.like(f"STATE:{key}=%"),
                )
                .order_by(desc(MessageModel.timestamp))
                .first()
            )
            if msg and msg.extra_metadata:
                return msg.extra_metadata.get("state_value", default)
            return default
        finally:
            db.close()

    def log_activity(
        self,
        action: str,
        target_type: str = "general",
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log activity AND record as an episode."""
        db = self._get_db()
        try:
            from app.core.database import ActivityLogModel
            log = ActivityLogModel(
                id=str(uuid.uuid4()),
                actor=self.agent_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details or {},
                timestamp=self._now(),
            )
            db.add(log)
            db.commit()

            # Record as episode for rich memory
            self.record_episode(
                event_type=f"activity_{action}",
                description=f"{action} on {target_type}: {str(details)[:200]}",
                importance=3,
            )

            return log.id
        finally:
            db.close()

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity log entries."""
        db = self._get_db()
        try:
            logs = (
                db.query(ActivityLogModel)
                .filter(ActivityLogModel.actor == self.agent_id)
                .order_by(desc(ActivityLogModel.timestamp))
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

    def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search all memory systems for a keyword."""
        results: List[Dict[str, Any]] = []

        # Search episodes
        ep_results = self.search_episodes(query, limit=limit // 2)
        for ep in ep_results:
            ep["_source"] = "episodic"
            results.append(ep)

        # Search facts
        fact_results = self.search_knowledge(query, limit=limit // 2)
        for f in fact_results:
            f["_source"] = "semantic"
            results.append(f)

        # Sort by recency
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]

    def clear_conversation_history(self, older_than_days: Optional[int] = None) -> int:
        """Clear conversation history."""
        db = self._get_db()
        try:
            query = db.query(MessageModel).filter(
                (MessageModel.from_agent == self.agent_id)
                | (MessageModel.to_agent == self.agent_id)
            )
            if older_than_days:
                cutoff = self._ago(older_than_days)
                query = query.filter(MessageModel.timestamp < cutoff)
            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()

    def clear_episodes(self, older_than_days: Optional[int] = None) -> int:
        """Clear episodic memories, optionally only old ones."""
        db = self._get_db()
        try:
            query = db.query(AgentEpisodeModel).filter(
                AgentEpisodeModel.agent_id == self.agent_id
            )
            if older_than_days:
                query = query.filter(AgentEpisodeModel.timestamp < self._ago(older_than_days))
            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()

    def clear_facts(self, older_than_days: Optional[int] = None) -> int:
        """Clear semantic facts, optionally only old ones."""
        db = self._get_db()
        try:
            query = db.query(AgentFactModel).filter(
                AgentFactModel.agent_id == self.agent_id
            )
            if older_than_days:
                query = query.filter(AgentFactModel.timestamp < self._ago(older_than_days))
            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()

    def clear_patterns(self, older_than_days: Optional[int] = None) -> int:
        """Clear procedural patterns, optionally only old ones."""
        db = self._get_db()
        try:
            query = db.query(AgentPatternModel).filter(
                AgentPatternModel.agent_id == self.agent_id
            )
            if older_than_days:
                query = query.filter(AgentPatternModel.timestamp < self._ago(older_than_days))
            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()

    def clear_all_memory(self, keep_days: int = 0) -> Dict[str, int]:
        """Nuclear option: clear all memory compartments.

        Args:
            keep_days: If > 0, only clear entries older than N days.

        Returns:
            Dict with counts of what was deleted per compartment.
        """
        older = keep_days if keep_days > 0 else None
        return {
            "episodes": self.clear_episodes(older),
            "facts": self.clear_facts(older),
            "patterns": self.clear_patterns(older),
            "conversations": self.clear_conversation_history(older),
        }
