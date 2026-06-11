"""
Fankaar Studio — free image generation.

Providers (set IMAGE_PROVIDER):
  • "flux"   (default) — NVIDIA NIM FLUX.1-schnell. FREE, ~2s, Apache-2.0, commercial-OK.
                          Needs NVIDIA_API_KEY (free key from build.nvidia.com).
  • "zimage"            — Z-Image (Alibaba Tongyi, Apache-2.0). Wired as an OpenAI-images-
                          compatible call to ZIMAGE_BASE_URL with ZIMAGE_API_KEY + ZIMAGE_MODEL,
                          so it works with DashScope / a self-hosted / any Z-Image endpoint you set.

Returns raw image bytes (JPEG/PNG). No paid APIs.
"""
from __future__ import annotations

import base64
import os
import httpx

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
FLUX_URL = os.getenv(
    "FLUX_URL", "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
)

ZIMAGE_API_KEY = os.getenv("ZIMAGE_API_KEY", "")
ZIMAGE_BASE_URL = os.getenv("ZIMAGE_BASE_URL", "")  # e.g. https://dashscope-intl.aliyuncs.com/compatible-mode/v1
ZIMAGE_MODEL = os.getenv("ZIMAGE_MODEL", "z-image-turbo")

DEFAULT_PROVIDER = os.getenv("IMAGE_PROVIDER", "flux").lower()


class ImageGenError(RuntimeError):
    pass


def available_providers() -> dict:
    """Which image providers are configured right now (for a health panel)."""
    return {
        "flux": bool(NVIDIA_API_KEY),
        "zimage": bool(ZIMAGE_API_KEY and ZIMAGE_BASE_URL),
        "default": DEFAULT_PROVIDER,
    }


async def _flux_nvidia(prompt: str, width: int, height: int) -> bytes:
    if not NVIDIA_API_KEY:
        raise ImageGenError("NVIDIA_API_KEY not set — get a free key at build.nvidia.com")
    payload = {
        "prompt": prompt,
        "mode": "base",
        "width": width,
        "height": height,
        "steps": 4,
        "seed": 0,
    }
    async with httpx.AsyncClient(timeout=90) as http:
        r = await http.post(
            FLUX_URL,
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}",
                     "Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
        )
    if r.status_code != 200:
        raise ImageGenError(f"FLUX/NVIDIA {r.status_code}: {r.text[:200]}")
    arts = r.json().get("artifacts", [])
    if not arts or not arts[0].get("base64"):
        raise ImageGenError("FLUX returned no image")
    return base64.b64decode(arts[0]["base64"])


async def _zimage(prompt: str, width: int, height: int) -> bytes:
    """Z-Image via an OpenAI-images-compatible endpoint (DashScope or self-hosted).
    Set ZIMAGE_BASE_URL + ZIMAGE_API_KEY + ZIMAGE_MODEL to enable."""
    if not (ZIMAGE_API_KEY and ZIMAGE_BASE_URL):
        raise ImageGenError(
            "Z-Image not configured. Set ZIMAGE_BASE_URL, ZIMAGE_API_KEY, ZIMAGE_MODEL "
            "(e.g. DashScope/Model Studio, or a local Z-Image server)."
        )
    url = ZIMAGE_BASE_URL.rstrip("/") + "/images/generations"
    payload = {"model": ZIMAGE_MODEL, "prompt": prompt, "size": f"{width}x{height}", "n": 1}
    async with httpx.AsyncClient(timeout=120) as http:
        r = await http.post(
            url,
            headers={"Authorization": f"Bearer {ZIMAGE_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
    if r.status_code != 200:
        raise ImageGenError(f"Z-Image {r.status_code}: {r.text[:200]}")
    data = (r.json() or {}).get("data", [])
    if not data:
        raise ImageGenError("Z-Image returned no image")
    item = data[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):  # some hosts return a URL
        async with httpx.AsyncClient(timeout=60) as http:
            img = await http.get(item["url"])
        return img.content
    raise ImageGenError("Z-Image response had neither b64_json nor url")


async def generate_image(prompt: str, width: int = 1024, height: int = 1024,
                         provider: str | None = None) -> bytes:
    """Generate one image, returning raw bytes. Falls back flux->zimage / zimage->flux
    only if the chosen provider is unconfigured."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ImageGenError("empty prompt")
    width = max(256, min(int(width), 1536))
    height = max(256, min(int(height), 1536))
    prov = (provider or DEFAULT_PROVIDER).lower()
    av = available_providers()
    if prov == "zimage" and not av["zimage"] and av["flux"]:
        prov = "flux"  # requested Z-Image but it isn't set up — use the working free one
    elif prov == "flux" and not av["flux"] and av["zimage"]:
        prov = "zimage"
    if prov == "zimage":
        return await _zimage(prompt, width, height)
    return await _flux_nvidia(prompt, width, height)
