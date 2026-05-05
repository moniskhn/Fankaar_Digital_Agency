"""
Claude Mythos — Content Calendar
Timezone-aware scheduling, optimal posting time calculation,
and content calendar generation.
"""

import uuid
from datetime import datetime, timedelta, timezone as tz
from typing import List, Optional

from app.core.config import settings
from app.core.database import ScheduledPostModel, SessionLocal
from app.core.models import ContentCalendarResponse, ScheduledPost, ScheduledPostCreate
from app.services.regional_intel import regional_intel


class ContentCalendarEngine:
    """
    Generates timezone-aware content calendars with optimal posting times.
    """

    # Default optimal posting times by platform (global averages)
    DEFAULT_POSTING_TIMES = {
        "Instagram": ["09:00", "12:00", "18:00"],
        "TikTok": ["07:00", "12:00", "19:00", "21:00"],
        "Facebook": ["09:00", "13:00", "15:00"],
        "Twitter": ["08:00", "12:00", "17:00"],
        "LinkedIn": ["08:00", "12:00", "17:00"],
        "YouTube": ["14:00", "16:00"],
        "Email": ["09:00", "14:00"],
    }

    # Content type → recommended platforms
    CONTENT_TYPE_PLATFORMS = {
        "image": ["Instagram", "Facebook", "LinkedIn", "Twitter"],
        "video": ["TikTok", "Instagram", "YouTube", "Facebook"],
        "carousel": ["Instagram", "LinkedIn", "Facebook"],
        "story": ["Instagram", "Facebook"],
        "reel": ["Instagram", "TikTok"],
        "text": ["Twitter", "LinkedIn", "Facebook"],
        "email": ["Email"],
        "blog": ["Email", "LinkedIn", "Twitter"],
    }

    # How many posts per week by content type
    POSTING_FREQUENCY = {
        "image": 5,
        "video": 3,
        "carousel": 2,
        "story": 7,
        "reel": 4,
        "text": 5,
        "email": 2,
        "blog": 1,
    }

    async def get_optimal_times(
        self,
        region: str,
        platform: str,
        content_type: str = "general",
    ) -> List[datetime]:
        """
        Get optimal posting times for a region and platform.

        Args:
            region: Target region (e.g., "Dubai, UAE")
            platform: Social platform name
            content_type: Type of content

        Returns:
            List of optimal datetime objects for today
        """
        # Get region-specific times
        regional_times = await regional_intel.get_best_posting_times(region, platform)

        if not regional_times:
            platform_clean = platform.capitalize()
            regional_times = self.DEFAULT_POSTING_TIMES.get(
                platform_clean,
                self.DEFAULT_POSTING_TIMES["Instagram"],
            )

        # Convert to datetime objects
        now = datetime.utcnow()
        result = []
        for time_str in regional_times:
            try:
                hour, minute = map(int, time_str.split(":"))
                dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if dt < now:
                    dt += timedelta(days=1)
                result.append(dt)
            except (ValueError, AttributeError):
                continue

        return sorted(result)

    async def create_schedule(
        self,
        campaign_id: str,
        region: str,
        channels: List[str],
        days: int = 30,
        content_types: Optional[List[str]] = None,
    ) -> List[ScheduledPost]:
        """
        Create a content schedule for a campaign.

        Args:
            campaign_id: Campaign ID
            region: Target region
            channels: List of platforms/channels
            days: Number of days to schedule
            content_types: Override default content types

        Returns:
            List of scheduled posts
        """
        if content_types is None:
            content_types = ["image", "video", "text", "story"]

        posts: List[ScheduledPost] = []
        now = datetime.utcnow()

        for day_offset in range(days):
            day = now + timedelta(days=day_offset)

            for channel in channels:
                channel_posts = await self._schedule_day(
                    campaign_id=campaign_id,
                    region=region,
                    channel=channel,
                    day=day,
                    content_types=content_types,
                )
                posts.extend(channel_posts)

        # Save to database
        db = SessionLocal()
        try:
            for post in posts:
                db_post = ScheduledPostModel(
                    id=post.id,
                    campaign_id=post.campaign_id,
                    platform=post.platform,
                    content_type=post.content_type,
                    content_text=post.content_text,
                    media_urls=post.media_urls,
                    scheduled_time=post.scheduled_time,
                    timezone=post.timezone,
                    status=post.status,
                    engagement_estimate=post.engagement_estimate,
                    metadata=post.metadata,
                )
                db.add(db_post)
            db.commit()
        finally:
            db.close()

        return sorted(posts, key=lambda p: p.scheduled_time)

    async def _schedule_day(
        self,
        campaign_id: str,
        region: str,
        channel: str,
        day: datetime,
        content_types: List[str],
    ) -> List[ScheduledPost]:
        """Schedule posts for a single day on a channel."""
        posts = []

        # Get optimal times for this channel in this region
        optimal_times = await self.get_optimal_times(region, channel)

        # Filter content types suitable for this channel
        suitable_types = []
        for ct in content_types:
            platforms = self.CONTENT_TYPE_PLATFORMS.get(ct, [])
            if channel in platforms or any(p.lower() == channel.lower() for p in platforms):
                suitable_types.append(ct)

        if not suitable_types:
            suitable_types = ["text"]

        # Create posts for optimal times
        for i, opt_time in enumerate(optimal_times[:2]):  # Max 2 posts per day per channel
            content_type = suitable_types[i % len(suitable_types)]

            post_time = day.replace(
                hour=opt_time.hour,
                minute=opt_time.minute,
                second=0,
                microsecond=0,
            )

            if post_time < datetime.utcnow():
                post_time += timedelta(days=1)

            post = ScheduledPost(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                platform=channel,
                content_type=content_type,
                content_text=f"[{channel}] {content_type.capitalize()} post for {region} — draft content",
                media_urls=[],
                scheduled_time=post_time,
                timezone="UTC",
                status="scheduled",
                engagement_estimate=0.0,
                metadata={
                    "region": region,
                    "optimal_time_reason": f"Peak engagement time for {channel} in {region}",
                },
            )
            posts.append(post)

        return posts

    async def get_content_calendar(self, campaign_id: str, days: int = 30) -> ContentCalendarResponse:
        """
        Get the content calendar for a campaign.

        Args:
            campaign_id: Campaign ID
            days: Number of days to look ahead

        Returns:
            ContentCalendarResponse with all scheduled posts
        """
        db = SessionLocal()
        try:
            posts_db = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.campaign_id == campaign_id,
            ).order_by(ScheduledPostModel.scheduled_time).all()

            posts = [
                ScheduledPost(
                    id=p.id,
                    campaign_id=p.campaign_id,
                    platform=p.platform,
                    content_type=p.content_type,
                    content_text=p.content_text or "",
                    media_urls=p.media_urls or [],
                    scheduled_time=p.scheduled_time,
                    timezone=p.timezone or "UTC",
                    status=p.status,
                    posted_at=p.posted_at,
                    engagement_estimate=p.engagement_estimate or 0.0,
                    metadata=p.metadata or {},
                )
                for p in posts_db
            ]

            # Get campaign name
            from app.core.database import CampaignModel
            campaign = db.query(CampaignModel).filter(
                CampaignModel.id == campaign_id
            ).first()
            campaign_name = campaign.name if campaign else "Unknown"
            platforms = list(set(p.platform for p in posts))

            return ContentCalendarResponse(
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                posts=posts,
                total_posts=len(posts),
                platforms=platforms,
            )
        finally:
            db.close()

    async def add_scheduled_post(self, post: ScheduledPostCreate) -> ScheduledPost:
        """Add a single scheduled post."""
        db = SessionLocal()
        try:
            post_id = str(uuid.uuid4())
            db_post = ScheduledPostModel(
                id=post_id,
                campaign_id=post.campaign_id,
                platform=post.platform,
                content_type=post.content_type,
                content_text=post.content_text,
                media_urls=post.media_urls,
                scheduled_time=post.scheduled_time,
                timezone=post.timezone,
                status="scheduled",
            )
            db.add(db_post)
            db.commit()

            return ScheduledPost(
                id=post_id,
                campaign_id=post.campaign_id,
                platform=post.platform,
                content_type=post.content_type,
                content_text=post.content_text,
                media_urls=post.media_urls,
                scheduled_time=post.scheduled_time,
                timezone=post.timezone,
                status="scheduled",
            )
        finally:
            db.close()

    async def update_post_status(
        self,
        post_id: str,
        status: str,
    ) -> Optional[ScheduledPost]:
        """Update the status of a scheduled post."""
        db = SessionLocal()
        try:
            post = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.id == post_id
            ).first()

            if not post:
                return None

            post.status = status
            if status == "published":
                post.posted_at = datetime.utcnow()

            db.commit()

            return ScheduledPost(
                id=post.id,
                campaign_id=post.campaign_id,
                platform=post.platform,
                content_type=post.content_type,
                content_text=post.content_text or "",
                media_urls=post.media_urls or [],
                scheduled_time=post.scheduled_time,
                timezone=post.timezone or "UTC",
                status=post.status,
                posted_at=post.posted_at,
                engagement_estimate=post.engagement_estimate or 0.0,
                metadata=post.metadata or {},
            )
        finally:
            db.close()

    async def get_upcoming_posts(self, hours: int = 24) -> List[ScheduledPost]:
        """Get posts scheduled within the next N hours."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            cutoff = now + timedelta(hours=hours)

            posts_db = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.scheduled_time >= now,
                ScheduledPostModel.scheduled_time <= cutoff,
                ScheduledPostModel.status == "scheduled",
            ).order_by(ScheduledPostModel.scheduled_time).all()

            return [
                ScheduledPost(
                    id=p.id,
                    campaign_id=p.campaign_id,
                    platform=p.platform,
                    content_type=p.content_type,
                    content_text=p.content_text or "",
                    media_urls=p.media_urls or [],
                    scheduled_time=p.scheduled_time,
                    timezone=p.timezone or "UTC",
                    status=p.status,
                    posted_at=p.posted_at,
                    engagement_estimate=p.engagement_estimate or 0.0,
                    metadata=p.metadata or {},
                )
                for p in posts_db
            ]
        finally:
            db.close()


# Global instance
content_calendar = ContentCalendarEngine()
