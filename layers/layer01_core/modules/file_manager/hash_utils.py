"""
Hash Utilities Module
Layer 1: Core System — Module 8

SHA-256 hash calculation and verification for file integrity.
"""

import hashlib
from pathlib import Path
from typing import Optional


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
    Path(hash_file).write_text(h)
    return h


def verify_hash(filepath: str) -> tuple:
    """Verify file hash against saved hash. Returns (match, current_hash)."""
    hash_file = filepath + ".sha256"
    if not Path(hash_file).exists():
        return True, None  # No hash file = skip check
    saved = Path(hash_file).read_text().strip()
    current = calculate_hash(filepath)
    return saved == current, current
