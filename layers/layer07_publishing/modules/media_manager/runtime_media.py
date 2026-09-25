"""Runtime media helpers with account-path isolation."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

_SAFE_ACCOUNT = re.compile(r"[^A-Za-z0-9_.-]+")


class RuntimeMedia:
    """Generate local media only inside the configured account workspace."""

    @staticmethod
    def _safe_account_id(account_id: str) -> str:
        original = account_id.strip()
        if not original:
            raise ValueError("account_id is required")
        safe = _SAFE_ACCOUNT.sub("_", original)[:120] or "account"
        if safe != original or len(original) > 120:
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:12]
            safe = f"{safe[:100]}-{digest}"
        return safe

    @staticmethod
    def image_to_video(image_path: str, account_id: str, seconds: int = 6) -> str:
        if not image_path or not os.path.isfile(image_path):
            raise FileNotFoundError("image artifact is required for video generation")
        if seconds < 1 or seconds > 3600:
            raise ValueError("seconds must be between 1 and 3600")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required for local video generation")

        root = (
            Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces"))
            / RuntimeMedia._safe_account_id(account_id)
            / "media"
            / "video"
        )
        root.mkdir(parents=True, exist_ok=True)
        output = root / f"video_{time.time_ns()}.mp4"
        cmd = [
            ffmpeg, "-y", "-loop", "1", "-i", image_path, "-t", str(seconds),
            "-vf", "scale=1080:1080:force_original_aspect_ratio=decrease,"
                   "pad=1080:1080:(ow-iw)/2:(oh-ih)/2",
            "-r", "30", "-pix_fmt", "yuv420p", str(output),
        ]
        process = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, check=False
        )
        if process.returncode != 0:
            raise RuntimeError(f"video generation failed: {process.stderr[-1000:]}")
        return str(output)

    @staticmethod
    def public_url(path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        base = os.environ.get("UCOS_PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
        if not base:
            return ""
        root = Path(
            os.environ.get("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces")
        ).resolve()
        try:
            relative = Path(path).resolve().relative_to(root)
        except ValueError:
            return ""
        return f"{base}/{relative.as_posix()}"
