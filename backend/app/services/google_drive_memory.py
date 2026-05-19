"""
Fankaar Digital — Google Drive Agent Memory Sync
Every agent gets a folder in Google Drive.
Memory (episodes, facts, patterns, client data) syncs to Drive as JSON.
Falls back to local SQLite if Drive is unavailable.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────
DRIVE_ENABLED = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# ── Lazy imports (only load if Drive is enabled) ─────────────
_drive_service = None

def _get_drive_service():
    global _drive_service
    if _drive_service is not None:
        return _drive_service
    if not DRIVE_ENABLED:
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io

        if SERVICE_ACCOUNT_JSON:
            creds_info = json.loads(SERVICE_ACCOUNT_JSON)
        else:
            # Try file path
            creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/app/secrets/service-account.json")
            if not os.path.exists(creds_path):
                logger.warning(f"Google Drive: no credentials found")
                return None
            with open(creds_path) as f:
                creds_info = json.load(f)

        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        _drive_service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service initialized")
        return _drive_service
    except Exception as e:
        logger.warning(f"Google Drive init failed: {e}")
        return None


# ── Folder Management ─────────────────────────────────────────

def _get_or_create_folder(name: str, parent_id: Optional[str] = None) -> Optional[str]:
    """Get or create a folder in Drive. Returns folder ID."""
    drive = _get_drive_service()
    if not drive:
        return None

    parent = parent_id or DRIVE_FOLDER_ID

    # Search for existing
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
    if parent:
        q += f" and '{parent}' in parents"

    try:
        results = drive.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        # Create
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent] if parent else []
        }
        folder = drive.files().create(body=metadata, fields="id").execute()
        fid = folder.get("id")
        logger.info(f"Created Drive folder '{name}': {fid}")
        return fid
    except Exception as e:
        logger.warning(f"Drive folder error for '{name}': {e}")
        return None


_agent_folder_cache: Dict[str, str] = {}

def _get_agent_folder(agent_id: str) -> Optional[str]:
    """Get or create agent's memory folder."""
    if agent_id in _agent_folder_cache:
        return _agent_folder_cache[agent_id]
    fid = _get_or_create_folder(f"agent_{agent_id}")
    _agent_folder_cache[agent_id] = fid
    return fid


# ── File Read/Write ───────────────────────────────────────────

def _upload_json(filename: str, data: Any, parent_id: str) -> bool:
    """Upload or overwrite a JSON file in Drive."""
    drive = _get_drive_service()
    if not drive:
        return False

    try:
        import io
        # Search for existing
        q = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        results = drive.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])

        body = io.BytesIO(json.dumps(data, indent=2, default=str).encode("utf-8"))
        media = {"mimeType": "application/json", "body": body}

        if files:
            # Update
            drive.files().update(
                fileId=files[0]["id"],
                media_body=media,
                fields="id"
            ).execute()
        else:
            # Create
            metadata = {"name": filename, "parents": [parent_id]}
            drive.files().create(body=metadata, media_body=media, fields="id").execute()
        return True
    except Exception as e:
        logger.warning(f"Drive upload failed for {filename}: {e}")
        return False


def _download_json(filename: str, parent_id: str) -> Optional[Any]:
    """Download and parse a JSON file from Drive."""
    drive = _get_drive_service()
    if not drive:
        return None

    try:
        import io
        q = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        results = drive.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])
        if not files:
            return None

        fid = files[0]["id"]
        request = drive.files().get_media(fileId=fid)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return json.loads(fh.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Drive download failed for {filename}: {e}")
        return None


# ── Agent Memory Sync Interface ─────────────────────────────────

class DriveMemorySync:
    """
    Sync agent memory to Google Drive.
    Each agent gets:
      - episodes.json   (episodic memory)
      - facts.json      (semantic memory)
      - patterns.json   (procedural memory)
      - clients.json    (client-specific memory)
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.folder_id: Optional[str] = None
        if DRIVE_ENABLED:
            self.folder_id = _get_agent_folder(agent_id)

    def is_available(self) -> bool:
        return self.folder_id is not None

    # ── Push (write to Drive) ──────────────────────────────────

    def push_episodes(self, episodes: List[Dict]) -> bool:
        if not self.folder_id:
            return False
        return _upload_json("episodes.json", episodes, self.folder_id)

    def push_facts(self, facts: List[Dict]) -> bool:
        if not self.folder_id:
            return False
        return _upload_json("facts.json", facts, self.folder_id)

    def push_patterns(self, patterns: List[Dict]) -> bool:
        if not self.folder_id:
            return False
        return _upload_json("patterns.json", patterns, self.folder_id)

    def push_client_memories(self, clients: Dict[str, Any]) -> bool:
        if not self.folder_id:
            return False
        return _upload_json("clients.json", clients, self.folder_id)

    # ── Pull (read from Drive) ─────────────────────────────────

    def pull_episodes(self) -> Optional[List[Dict]]:
        if not self.folder_id:
            return None
        return _download_json("episodes.json", self.folder_id)

    def pull_facts(self) -> Optional[List[Dict]]:
        if not self.folder_id:
            return None
        return _download_json("facts.json", self.folder_id)

    def pull_patterns(self) -> Optional[List[Dict]]:
        if not self.folder_id:
            return None
        return _download_json("patterns.json", self.folder_id)

    def pull_client_memories(self) -> Optional[Dict[str, Any]]:
        if not self.folder_id:
            return None
        return _download_json("clients.json", self.folder_id)


# ── Global sync helper ─────────────────────────────────────────

def sync_agent_to_drive(agent_id: str, memory_instance) -> bool:
    """
    One-shot sync: push all memory types for an agent to Drive.
    Called by background jobs.
    """
    sync = DriveMemorySync(agent_id)
    if not sync.is_available():
        return False

    ok = True
    try:
        # Episodes
        episodes = memory_instance.get_all_episodes(limit=1000)
        if not sync.push_episodes(episodes):
            ok = False

        # Facts
        facts = memory_instance.get_all_facts(limit=1000)
        if not sync.push_facts(facts):
            ok = False

        # Patterns
        patterns = memory_instance.get_all_patterns(limit=1000)
        if not sync.push_patterns(patterns):
            ok = False

        # Client memories
        clients = memory_instance.get_all_client_memories()
        if not sync.push_client_memories(clients):
            ok = False

        logger.info(f"Drive sync complete for {agent_id}: ok={ok}")
        return ok
    except Exception as e:
        logger.warning(f"Drive sync failed for {agent_id}: {e}")
        return False


def restore_agent_from_drive(agent_id: str, memory_instance) -> bool:
    """
    One-shot restore: pull all memory from Drive into local DB.
    Called on startup if Drive has newer data.
    """
    sync = DriveMemorySync(agent_id)
    if not sync.is_available():
        return False

    restored = 0
    try:
        episodes = sync.pull_episodes()
        if episodes:
            for ep in episodes:
                memory_instance.record_episode(
                    event_type=ep.get("event_type", "unknown"),
                    description=ep.get("description", ""),
                    client_id=ep.get("client_id"),
                    campaign_id=ep.get("campaign_id"),
                    importance=ep.get("importance", 3),
                )
            restored += len(episodes)

        facts = sync.pull_facts()
        if facts:
            for f in facts:
                memory_instance.learn_fact(
                    category=f.get("category", "general"),
                    fact=f.get("fact", ""),
                    confidence=f.get("confidence", 0.8),
                    source=f.get("source", "drive_restore"),
                )
            restored += len(facts)

        patterns = sync.pull_patterns()
        if patterns:
            for p in patterns:
                memory_instance.learn_pattern(
                    pattern_type=p.get("pattern_type", "general"),
                    description=p.get("description", ""),
                    success_rate=p.get("success_rate", 0.8),
                )
            restored += len(patterns)

        logger.info(f"Drive restore for {agent_id}: {restored} items")
        return restored > 0
    except Exception as e:
        logger.warning(f"Drive restore failed for {agent_id}: {e}")
        return False

