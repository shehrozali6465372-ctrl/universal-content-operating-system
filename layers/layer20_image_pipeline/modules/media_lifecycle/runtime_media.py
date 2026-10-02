"""Canonical L20 media semantics and public-media lifecycle.

L20 owns local asset validation, normalization and public-media identity.
L11 remains responsible for provider transport.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict


class MediaLifecycleError(RuntimeError):
    """Raised when a media artifact cannot satisfy the L20 contract."""


class RuntimeMedia:
    """L20 asset transformation and canonical public-media URL semantics."""

    @staticmethod
    def _workspace_root() -> Path:
        return Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces")).resolve()

    @classmethod
    def _account_root(cls, account_id: str) -> Path:
        account = str(account_id or "").strip()
        if not account:
            raise ValueError("account_id is required for account-scoped media")
        root = (cls._workspace_root() / account).resolve()
        try:
            root.relative_to(cls._workspace_root())
        except ValueError as exc:
            raise MediaLifecycleError("account media path escapes canonical workspace root") from exc
        return root

    @staticmethod
    def checksum(path: str) -> str:
        target = Path(path)
        if not target.is_file():
            raise FileNotFoundError("media artifact does not exist")
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def validate_local_artifact(cls, path: str, *, account_id: str = "") -> Dict[str, Any]:
        target = Path(path)
        if not target.is_file() or target.stat().st_size <= 0:
            raise MediaLifecycleError("media artifact must be a non-empty local file")
        root = cls._account_root(account_id) if account_id else cls._workspace_root()
        try:
            resolved = target.resolve()
            resolved.relative_to(root)
        except ValueError as exc:
            raise MediaLifecycleError("media artifact is outside the permitted workspace") from exc
        return {
            "path": str(resolved),
            "size_bytes": resolved.stat().st_size,
            "sha256": cls.checksum(str(resolved)),
            "file_name": resolved.name,
        }

    @classmethod
    def image_to_video(cls, image_path: str, account_id: str, seconds: int = 6) -> str:
        meta = cls.validate_local_artifact(image_path, account_id=account_id)
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise MediaLifecycleError("ffmpeg is required for local video generation")
        root = cls._account_root(account_id) / "media" / "video"
        root.mkdir(parents=True, exist_ok=True)
        output = root / f"video_{int(time.time() * 1000)}_{meta['sha256'][:12]}.mp4"
        command = [
            ffmpeg, "-y", "-loop", "1", "-i", meta["path"], "-t", str(seconds),
            "-vf", "scale=1080:1080:force_original_aspect_ratio=decrease,"
                   "pad=1080:1080:(ow-iw)/2:(oh-ih)/2",
            "-r", "30", "-pix_fmt", "yuv420p", str(output),
        ]
        process = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if process.returncode != 0:
            raise MediaLifecycleError(f"video generation failed: {process.stderr[-1000:]}")
        return str(output)

    @classmethod
    def public_url(cls, path: str, *, account_id: str = "") -> str:
        value = str(path or "").strip()
        if value.startswith("https://"):
            return value
        if value.startswith("http://"):
            return ""
        base = os.environ.get("UCOS_PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
        if not base:
            return ""
        if account_id:
            cls.validate_local_artifact(value, account_id=account_id)
        root = cls._workspace_root()
        try:
            relative = Path(value).resolve().relative_to(root)
        except ValueError:
            return ""
        return f"{base}/{relative.as_posix()}"

    @classmethod
    def build_asset_ref(cls, path: str, *, account_id: str, media_type: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        validated = cls.validate_local_artifact(path, account_id=account_id)
        return {
            "asset_id": f"asset_{validated['sha256']}",
            "account_id": account_id,
            "media_type": media_type,
            "file_name": validated["file_name"],
            "size_bytes": validated["size_bytes"],
            "sha256": validated["sha256"],
            "source_path": validated["path"],
            "public_url": cls.public_url(validated["path"], account_id=account_id),
            "metadata": dict(metadata or {}),
        }
