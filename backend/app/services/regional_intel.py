"""
Claude Mythos — Regional Intelligence Engine
Researches regions via web search, builds RegionalProfile with
culture, platforms, best times, CTAs, personas. Caches in SQLite.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import RegionalProfileModel, SessionLocal
from app.core.models import (
    CulturalCTA,
    Persona,
    PlatformInsight,
    RegionalProfile,
)
from app.services.llm_client import llm_client


class RegionalIntelEngine:
    """
    Provides culturally-aware, region-specific marketing intelligence.
    Researches regions and caches results in SQLite.
    """

    def __init__(self):
        self.cache_ttl_hours = settings.regional_cache_ttl_hours

    async def get_or_build_profile(self, region: str) -> RegionalProfile:
        """
        Get a regional profile from cache or build via research.
        """
        # Try cache first
        cached = self._get_cached_profile(region)
        if cached:
            return cached

        # Build via research
        profile = await self.research_region(region)

        # Cache the result
        self._cache_profile(profile)

        return profile

    async def research_region(self, region: str) -> RegionalProfile:
        """
        Research a region via web search + LLM synthesis.
        """
        # Web search for different aspects
        search_results = await self._web_search_region(region)

        # Synthesize into structured profile using LLM
        profile = await self._synthesize_profile(region, search_results)

        return profile

    async def _web_search_region(self, region: str) -> Dict[str, str]:
        """Perform web searches for different regional aspects."""
        results = {}

        try:
            search_queries = [
                f"social media usage {region} 2025 2026 statistics",
                f"digital marketing {region} cultural tips best practices",
                f"best time to post social media {region}",
                f"consumer behavior {region} marketing trends",
                f"popular social media platforms {region}",
            ]

            for query in search_queries:
                try:
                    search_result = await self._perform_search(query)
                    results[query] = search_result
                except Exception:
                    results[query] = ""

        except Exception:
            pass

        return results

    async def _perform_search(self, query: str) -> str:
        """Perform a web search and return results."""
        try:
            from mshtools.web_search import search as web_search
            search_results = web_search(query)
            return search_results if search_results else ""
        except Exception:
            return ""

    async def _synthesize_profile(
        self,
        region: str,
        search_results: Dict[str, str],
    ) -> RegionalProfile:
        """Use LLM to synthesize search results into structured profile."""
        search_text = "\n\n".join(
            f"Query: {q}\nResults: {r[:2000]}"
            for q, r in search_results.items() if r
        )

        if not search_text:
            search_text = f"No search data available for {region}. Using general knowledge."

        prompt = f"""
        Based on the following research about {region}, create a comprehensive regional marketing profile.

        RESEARCH DATA:
        {search_text[:5000]}

        Create a detailed marketing profile for {region} covering:

        1. Culture notes (communication style, values, sensitivities)
        2. Primary and secondary languages
        3. Social media platforms (which are popular, user demographics, content formats)
        4. Best posting times by platform
        5. Culturally-appropriate CTAs
        6. Audience personas (2-3 key segments)
        7. Content themes that resonate
        8. Cultural taboos to avoid
        9. Current local trends
        10. Competitor landscape overview

        Respond as valid JSON matching this structure:
        {{
            "culture_notes": "string",
            "language_primary": "string",
            "languages_secondary": ["string"],
            "social_platforms": [
                {{
                    "platform": "string",
                    "popularity": "high|medium|low",
                    "user_demo": "string",
                    "content_formats": ["string"],
                    "best_practices": ["string"],
                    "avg_engagement": "string"
                }}
            ],
            "best_posting_times": {{
                "platform_name": ["HH:MM", "HH:MM"]
            }},
            "ctas_by_culture": [
                {{
                    "text": "string",
                    "context": "string",
                    "effectiveness": "high|medium|low"
                }}
            ],
            "audience_personas": [
                {{
                    "name": "string",
                    "age_range": "string",
                    "interests": ["string"],
                    "pain_points": ["string"],
                    "platforms": ["string"],
                    "content_preferences": ["string"],
                    "purchase_behavior": "string"
                }}
            ],
            "content_themes": ["string"],
            "taboos": ["string"],
            "local_trends": ["string"],
            "competitor_landscape": "string"
        }}

        Be specific and detailed. Use actual knowledge about {region}.
        """

        try:
            response = await llm_client.complete(
                prompt=prompt,
                temperature=0.3,
            )
            data = json.loads(response.text)
        except (json.JSONDecodeError, Exception):
            # Fallback: extract JSON from response
            try:
                if "```json" in response.text:
                    json_str = response.text.split("```json")[1].split("```")[0].strip()
                    data = json.loads(json_str)
                elif "```" in response.text:
                    json_str = response.text.split("```")[1].split("```")[0].strip()
                    data = json.loads(json_str)
                else:
                    data = self._generate_default_profile_data(region)
            except Exception:
                data = self._generate_default_profile_data(region)

        # Build Pydantic model
        social_platforms = [
            PlatformInsight(**p) for p in data.get("social_platforms", [])
        ]
        ctas = [CulturalCTA(**c) for c in data.get("ctas_by_culture", [])]
        personas = [Persona(**p) for p in data.get("audience_personas", [])]

        return RegionalProfile(
            region=region,
            culture_notes=data.get("culture_notes", ""),
            language_primary=data.get("language_primary", ""),
            languages_secondary=data.get("languages_secondary", []),
            social_platforms=social_platforms,
            best_posting_times=data.get("best_posting_times", {}),
            ctas_by_culture=ctas,
            audience_personas=personas,
            content_themes=data.get("content_themes", []),
            taboos=data.get("taboos", []),
            local_trends=data.get("local_trends", []),
            competitor_landscape=data.get("competitor_landscape", ""),
        )

    def _generate_default_profile_data(self, region: str) -> Dict[str, Any]:
        """Generate default profile data when research fails."""
        return {
            "culture_notes": f"General marketing guidance for {region}. Adapt messaging to local culture and preferences.",
            "language_primary": "English",
            "languages_secondary": [],
            "social_platforms": [
                {
                    "platform": "Instagram",
                    "popularity": "high",
                    "user_demo": "18-45, urban",
                    "content_formats": ["Images", "Reels", "Stories"],
                    "best_practices": ["Visual-first content", "Hashtags", "Influencer collabs"],
                    "avg_engagement": "2-4%",
                },
                {
                    "platform": "Facebook",
                    "popularity": "medium",
                    "user_demo": "25-65, broad",
                    "content_formats": ["Videos", "Posts", "Ads"],
                    "best_practices": ["Community building", "Targeted ads", "Groups"],
                    "avg_engagement": "1-2%",
                },
            ],
            "best_posting_times": {
                "Instagram": ["09:00", "18:00"],
                "Facebook": ["10:00", "15:00"],
            },
            "ctas_by_culture": [
                {"text": "Learn More", "context": "General", "effectiveness": "medium"},
                {"text": "Shop Now", "context": "E-commerce", "effectiveness": "high"},
            ],
            "audience_personas": [
                {
                    "name": "Urban Professional",
                    "age_range": "25-40",
                    "interests": ["Technology", "Career", "Lifestyle"],
                    "pain_points": ["Time constraints", "Information overload"],
                    "platforms": ["Instagram", "LinkedIn"],
                    "content_preferences": ["Short videos", "Infographics"],
                    "purchase_behavior": "Research online, purchase online",
                }
            ],
            "content_themes": ["Lifestyle", "Education", "Entertainment"],
            "taboos": ["Avoid culturally insensitive content"],
            "local_trends": ["Mobile-first consumption", "Video content growth"],
            "competitor_landscape": f"Competitive market in {region}. Research specific competitors for detailed analysis.",
        }

    def _get_cached_profile(self, region: str) -> Optional[RegionalProfile]:
        """Get profile from SQLite cache if not expired."""
        db = SessionLocal()
        try:
            record = db.query(RegionalProfileModel).filter(
                RegionalProfileModel.region.ilike(region)
            ).first()

            if not record:
                return None

            # Check expiry
            if record.expires_at and record.expires_at < datetime.utcnow():
                return None

            # Build from cached data
            social_platforms = [
                PlatformInsight(**p) for p in (record.social_platforms or [])
            ]
            ctas = [CulturalCTA(**c) for c in (record.ctas_by_culture or [])]
            personas = [Persona(**p) for p in (record.audience_personas or [])]

            return RegionalProfile(
                region=record.region,
                culture_notes=record.culture_notes or "",
                language_primary=record.language_primary or "",
                languages_secondary=record.languages_secondary or [],
                social_platforms=social_platforms,
                best_posting_times=record.best_posting_times or {},
                ctas_by_culture=ctas,
                audience_personas=personas,
                content_themes=record.content_themes or [],
                taboos=record.taboos or [],
                local_trends=record.local_trends or [],
                competitor_landscape=record.competitor_landscape or "",
            )
        finally:
            db.close()

    def _cache_profile(self, profile: RegionalProfile) -> None:
        """Cache a profile in SQLite."""
        db = SessionLocal()
        try:
            # Delete existing
            db.query(RegionalProfileModel).filter(
                RegionalProfileModel.region.ilike(profile.region)
            ).delete(synchronize_session=False)

            # Insert new
            record = RegionalProfileModel(
                id=str(datetime.utcnow().timestamp()),
                region=profile.region,
                culture_notes=profile.culture_notes,
                language_primary=profile.language_primary,
                languages_secondary=profile.languages_secondary,
                social_platforms=[p.model_dump() for p in profile.social_platforms],
                best_posting_times=profile.best_posting_times,
                ctas_by_culture=[c.model_dump() for c in profile.ctas_by_culture],
                audience_personas=[p.model_dump() for p in profile.audience_personas],
                content_themes=profile.content_themes,
                taboos=profile.taboos,
                local_trends=profile.local_trends,
                competitor_landscape=profile.competitor_landscape,
                cached_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=self.cache_ttl_hours),
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    # ── Public API ──

    async def get_best_posting_times(self, region: str, platform: str) -> List[str]:
        """Get optimal posting times for a region and platform."""
        profile = await self.get_or_build_profile(region)
        return profile.best_posting_times.get(platform, ["09:00", "15:00", "18:00"])

    async def get_cultural_ctas(self, region: str, objective: str = "general") -> List[CulturalCTA]:
        """Get culturally-appropriate CTAs for a region."""
        profile = await self.get_or_build_profile(region)
        return [c for c in profile.ctas_by_culture if objective.lower() in c.context.lower()] or profile.ctas_by_culture

    async def get_audience_personas(self, region: str, industry: str = "") -> List[Persona]:
        """Get audience personas for a region and optional industry."""
        profile = await self.get_or_build_profile(region)
        return profile.audience_personas

    async def get_local_trends(self, region: str) -> List[str]:
        """Get current local trends for a region."""
        profile = await self.get_or_build_profile(region)
        return profile.local_trends

    async def get_content_themes(self, region: str) -> List[str]:
        """Get content themes that resonate in a region."""
        profile = await self.get_or_build_profile(region)
        return profile.content_themes

    async def get_taboos(self, region: str) -> List[str]:
        """Get cultural taboos to avoid in a region."""
        profile = await self.get_or_build_profile(region)
        return profile.taboos

    async def get_platform_insights(self, region: str) -> List[PlatformInsight]:
        """Get social platform insights for a region."""
        profile = await self.get_or_build_profile(region)
        return profile.social_platforms


# Global instance
regional_intel = RegionalIntelEngine()
