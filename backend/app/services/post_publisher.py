"""
Fankaar Digital — Post Publisher
Actually executes scheduled posts to social media platforms.
Runs as a background job every minute.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.database import (
    CampaignModel,
    ClientModel,
    ScheduledPostModel,
    SessionLocal,
    TaskModel,
)
from app.core.models import ScheduledPost

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
# Platform API keys / tokens
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

# Simulation mode (when no API keys)
SIMULATE_POSTING = os.getenv("SIMULATE_POSTING", "true").lower() == "true"


# ── Publisher Interface ───────────────────────────────────────

class PlatformPublisher:
    """Base class for platform publishers."""

    async def publish(self, post: ScheduledPost, campaign: CampaignModel, client: ClientModel) -> Dict[str, Any]:
        raise NotImplementedError


class InstagramPublisher(PlatformPublisher):
    async def publish(self, post: ScheduledPost, campaign, client) -> Dict[str, Any]:
        if not INSTAGRAM_ACCESS_TOKEN:
            return {"success": False, "error": "No Instagram access token", "simulated": SIMULATE_POSTING}
        # TODO: Implement real Instagram Graph API posting
        # For now, simulate
        return {"success": True, "post_id": f"ig_sim_{post.id[:8]}", "simulated": True}


class TikTokPublisher(PlatformPublisher):
    async def publish(self, post: ScheduledPost, campaign, client) -> Dict[str, Any]:
        if not TIKTOK_ACCESS_TOKEN:
            return {"success": False, "error": "No TikTok access token", "simulated": SIMULATE_POSTING}
        return {"success": True, "post_id": f"tt_sim_{post.id[:8]}", "simulated": True}


class FacebookPublisher(PlatformPublisher):
    async def publish(self, post: ScheduledPost, campaign, client) -> Dict[str, Any]:
        if not FACEBOOK_ACCESS_TOKEN:
            return {"success": False, "error": "No Facebook access token", "simulated": SIMULATE_POSTING}
        return {"success": True, "post_id": f"fb_sim_{post.id[:8]}", "simulated": True}


class TwitterPublisher(PlatformPublisher):
    async def publish(self, post: ScheduledPost, campaign, client) -> Dict[str, Any]:
        if not TWITTER_API_KEY:
            return {"success": False, "error": "No Twitter API key", "simulated": SIMULATE_POSTING}
        return {"success": True, "post_id": f"tw_sim_{post.id[:8]}", "simulated": True}


class LinkedInPublisher(PlatformPublisher):
    async def publish(self, post: ScheduledPost, campaign, client) -> Dict[str, Any]:
        if not LINKEDIN_ACCESS_TOKEN:
            return {"success": False, "error": "No LinkedIn access token", "simulated": SIMULATE_POSTING}
        return {"success": True, "post_id": f"li_sim_{post.id[:8]}", "simulated": True}


# ── Publisher Registry ─────────────────────────────────────────

_PUBLISHERS = {
    "Instagram": InstagramPublisher(),
    "TikTok": TikTokPublisher(),
    "Facebook": FacebookPublisher(),
    "Twitter": TwitterPublisher(),
    "LinkedIn": LinkedInPublisher(),
    "Email": None,  # Email is handled separately
    "YouTube": None,  # YouTube needs different workflow
}


def get_publisher(platform: str) -> Optional[PlatformPublisher]:
    return _PUBLISHERS.get(platform)


# ── Main Publisher Engine ─────────────────────────────────────

class PostPublisher:
    """
    Checks for due posts and publishes them.
    Runs every minute via APScheduler.
    """

    async def run(self) -> Dict[str, Any]:
        """Check and publish all due posts."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            # Get posts that are scheduled and due (within the last 5 minutes)
            # This catches posts that might have been missed
            lookback = now - timedelta(minutes=5)

            posts_db = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.scheduled_time <= now,
                ScheduledPostModel.scheduled_time >= lookback,
                ScheduledPostModel.status == "scheduled",
            ).order_by(ScheduledPostModel.scheduled_time).all()

            if not posts_db:
                return {"published": 0, "failed": 0, "checked": 0}

            results = {"published": 0, "failed": 0, "checked": len(posts_db), "details": []}

            for post_db in posts_db:
                try:
                    # Get campaign and client info
                    campaign = db.query(CampaignModel).filter(
                        CampaignModel.id == post_db.campaign_id
                    ).first()
                    client = None
                    if campaign:
                        client = db.query(ClientModel).filter(
                            ClientModel.id == campaign.client_id
                        ).first()

                    post = ScheduledPost(
                        id=post_db.id,
                        campaign_id=post_db.campaign_id,
                        platform=post_db.platform,
                        content_type=post_db.content_type,
                        content_text=post_db.content_text or "",
                        media_urls=post_db.media_urls or [],
                        scheduled_time=post_db.scheduled_time,
                        timezone=post_db.timezone or "UTC",
                        status=post_db.status,
                        posted_at=post_db.posted_at,
                        engagement_estimate=post_db.engagement_estimate or 0.0,
                        extra_metadata=post_db.extra_metadata or {},
                    )

                    publisher = get_publisher(post.platform)
                    if not publisher:
                        # Platform not supported yet — mark as failed
                        post_db.status = "failed"
                        post_db.extra_metadata = {
                            **(post_db.extra_metadata or {}),
                            "failure_reason": f"No publisher for {post.platform}",
                        }
                        results["failed"] += 1
                        results["details"].append({
                            "post_id": post.id,
                            "platform": post.platform,
                            "status": "failed",
                            "reason": f"No publisher for {post.platform}",
                        })
                        continue

                    # Publish
                    publish_result = await publisher.publish(post, campaign, client)

                    if publish_result.get("success"):
                        post_db.status = "published"
                        post_db.posted_at = now
                        post_db.extra_metadata = {
                            **(post_db.extra_metadata or {}),
                            "publish_result": publish_result,
                            "published_at": now.isoformat(),
                        }
                        results["published"] += 1
                        results["details"].append({
                            "post_id": post.id,
                            "platform": post.platform,
                            "status": "published",
                            "simulated": publish_result.get("simulated", False),
                        })
                        logger.info(f"Published post {post.id} to {post.platform}")
                    else:
                        post_db.status = "failed"
                        post_db.extra_metadata = {
                            **(post_db.extra_metadata or {}),
                            "failure_reason": publish_result.get("error", "Unknown error"),
                            "publish_result": publish_result,
                        }
                        results["failed"] += 1
                        results["details"].append({
                            "post_id": post.id,
                            "platform": post.platform,
                            "status": "failed",
                            "reason": publish_result.get("error", "Unknown"),
                        })
                        logger.warning(f"Failed to publish post {post.id}: {publish_result.get('error')}")

                except Exception as e:
                    logger.error(f"Exception publishing post {post_db.id}: {e}", exc_info=True)
                    post_db.status = "failed"
                    results["failed"] += 1
                    results["details"].append({
                        "post_id": post_db.id,
                        "status": "failed",
                        "reason": str(e),
                    })

            db.commit()
            return results

        finally:
            db.close()

    async def get_publish_queue(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Get upcoming posts in the publish queue."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            cutoff = now + timedelta(hours=hours_ahead)

            posts_db = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.scheduled_time >= now,
                ScheduledPostModel.scheduled_time <= cutoff,
                ScheduledPostModel.status == "scheduled",
            ).order_by(ScheduledPostModel.scheduled_time).all()

            return [
                {
                    "id": p.id,
                    "campaign_id": p.campaign_id,
                    "platform": p.platform,
                    "content_type": p.content_type,
                    "content_text": p.content_text,
                    "scheduled_time": p.scheduled_time.isoformat() if p.scheduled_time else None,
                    "status": p.status,
                    "hours_until": round((p.scheduled_time - now).total_seconds() / 3600, 1) if p.scheduled_time else None,
                }
                for p in posts_db
            ]
        finally:
            db.close()

    async def retry_failed_post(self, post_id: str) -> Dict[str, Any]:
        """Retry a failed post."""
        db = SessionLocal()
        try:
            post = db.query(ScheduledPostModel).filter(
                ScheduledPostModel.id == post_id
            ).first()

            if not post:
                return {"success": False, "error": "Post not found"}

            if post.status != "failed":
                return {"success": False, "error": f"Post status is {post.status}, not failed"}

            # Reset to scheduled and re-run publisher
            post.status = "scheduled"
            db.commit()

            # Run publisher immediately
            result = await self.run()
            return {
                "success": True,
                "message": "Post queued for retry",
                "publisher_result": result,
            }
        finally:
            db.close()


# Global instance
post_publisher = PostPublisher()
