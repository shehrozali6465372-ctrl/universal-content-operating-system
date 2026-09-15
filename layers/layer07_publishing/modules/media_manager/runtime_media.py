"""Runtime media helpers used by the canonical account-aware pipeline."""
from __future__ import annotations
import os, shutil, subprocess, time
from pathlib import Path

class RuntimeMedia:
    @staticmethod
    def image_to_video(image_path: str, account_id: str, seconds: int = 6) -> str:
        if not image_path or not os.path.isfile(image_path):
            raise FileNotFoundError("image artifact is required for video generation")
        ffmpeg=shutil.which("ffmpeg")
        if not ffmpeg: raise RuntimeError("ffmpeg is required for local video generation")
        root=Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES","./data/accounts/workspaces"))/account_id/"media"/"video"
        root.mkdir(parents=True,exist_ok=True)
        output=root/f"video_{int(time.time()*1000)}.mp4"
        cmd=[ffmpeg,"-y","-loop","1","-i",image_path,"-t",str(seconds),"-vf","scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2","-r","30","-pix_fmt","yuv420p",str(output)]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        if p.returncode!=0: raise RuntimeError(f"video generation failed: {p.stderr[-1000:]}")
        return str(output)
    @staticmethod
    def public_url(path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"): return path
        base=os.environ.get("UCOS_PUBLIC_MEDIA_BASE_URL","").rstrip("/")
        if not base: return ""
        root=Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES","./data/accounts/workspaces")).resolve()
        try: rel=Path(path).resolve().relative_to(root)
        except ValueError: return ""
        return f"{base}/{rel.as_posix()}"
