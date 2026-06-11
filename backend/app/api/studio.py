"""
Fankaar Studio — image & reel generation endpoints.

  GET  /api/studio/health         which image providers are configured
  POST /api/studio/image          prompt -> image (base64 data URI)
  POST /api/studio/reel           scenes -> images -> 9:16 reel (local reel-studio)

Free, built on FLUX-schnell (NVIDIA NIM) by default, with Z-Image as a configurable
provider. Reels use the local reel-studio toolkit when available.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.image_gen import generate_image, available_providers, ImageGenError

studio_router = APIRouter(prefix="/api/studio", tags=["Studio"])

REEL_STUDIO_DIR = os.getenv("REEL_STUDIO_DIR", os.path.expanduser("~/claude skills/reel-studio"))


class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    provider: Optional[str] = None  # "flux" | "zimage" | None=default


class Scene(BaseModel):
    text: str = Field(..., description="caption shown on screen")
    image_prompt: Optional[str] = Field(None, description="what to generate for this scene")


class ReelRequest(BaseModel):
    title: str = "Fankaar Reel"
    scenes: List[Scene]
    voice: str = "Daniel"
    provider: Optional[str] = None


@studio_router.get("/health")
async def studio_health():
    prov = available_providers()
    return {
        "ok": True,
        "providers": prov,
        "reel_studio": os.path.isdir(REEL_STUDIO_DIR),
    }


@studio_router.post("/image")
async def studio_image(req: ImageRequest):
    """Generate a single image. Returns a base64 data URI the browser can show/download."""
    try:
        img = await generate_image(req.prompt, req.width, req.height, req.provider)
    except ImageGenError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"image generation failed: {e}")
    b64 = base64.b64encode(img).decode()
    return {
        "ok": True,
        "provider": (req.provider or available_providers()["default"]),
        "bytes": len(img),
        "image": f"data:image/jpeg;base64,{b64}",
    }


@studio_router.post("/reel")
async def studio_reel(req: ReelRequest):
    """Generate one image per scene, then assemble a 9:16 reel via the local reel-studio
    toolkit (voiceover + captions). Local/macOS only — if reel-studio isn't present,
    returns the generated scene images so they can be assembled elsewhere."""
    if not req.scenes:
        raise HTTPException(status_code=400, detail="no scenes")

    workdir = tempfile.mkdtemp(prefix="fankaar_reel_")
    images_b64: List[str] = []
    scene_json = []
    try:
        for i, sc in enumerate(req.scenes):
            prompt = sc.image_prompt or sc.text
            img = await generate_image(prompt, 1024, 1024, req.provider)
            path = os.path.join(workdir, f"{i+1}.jpg")
            with open(path, "wb") as f:
                f.write(img)
            images_b64.append("data:image/jpeg;base64," + base64.b64encode(img).decode())
            scene_json.append({"text": sc.text, "image": path})
    except ImageGenError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # No local reel-studio (e.g. cloud deploy) → hand back the scene images.
    if not os.path.isdir(REEL_STUDIO_DIR):
        return {"ok": True, "mode": "storyboard",
                "note": "reel-studio not found on this host; returning scene images",
                "images": images_b64}

    script = {
        "title": req.title, "style": "slideshow", "theme": "jarvis",
        "voice": req.voice, "scenes": scene_json,
    }
    script_path = os.path.join(workdir, "reel.json")
    with open(script_path, "w") as f:
        json.dump(script, f)

    try:
        proc = subprocess.run(
            ["uv", "run", "python", "render.py", script_path],
            cwd=REEL_STUDIO_DIR, capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        return {"ok": True, "mode": "storyboard",
                "note": "`uv` not available to run reel-studio; returning scene images",
                "images": images_b64}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="reel render timed out")

    out_mp4 = os.path.join(REEL_STUDIO_DIR, "out", f"{req.title}.mp4")
    if proc.returncode == 0 and os.path.isfile(out_mp4):
        return {"ok": True, "mode": "reel", "mp4_path": out_mp4, "images": images_b64}
    return {"ok": True, "mode": "storyboard",
            "note": f"reel render exited {proc.returncode}; returning scene images. {proc.stderr[-300:]}",
            "images": images_b64}
