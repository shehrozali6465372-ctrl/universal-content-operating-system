"""
Hash Utilities Module
Layer 1: Core System — Module 8

SHA-256 hash calculation and verification for file integrity.
"""

import hashlib
import os
import tempfile
from pathlib import Path


def calculate_hash(filepath: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_string_hash(data: str) -> str:
    """Calculate SHA-256 hash of a string."""
    return hashlib.sha256(data.encode()).hexdigest()


def save_hash(filepath: str) -> str:
    """Calculate hash and save to .sha256 sidecar file."""
    h = calculate_hash(filepath)
    # If file is "data.json", hash file is "data.json.sha256"
    hash_file = filepath + ".sha256"
    target = Path(hash_file)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".sha256.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(h + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, hash_file)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return h


def verify_hash(filepath: str) -> tuple:
    """Verify file hash against saved hash. Returns (match, current_hash)."""
    hash_file = filepath + ".sha256"
    if not Path(hash_file).exists():
        return False, None  # Integrity cannot be established without metadata
    saved = Path(hash_file).read_text().strip()
    current = calculate_hash(filepath)
    return saved == current, current
