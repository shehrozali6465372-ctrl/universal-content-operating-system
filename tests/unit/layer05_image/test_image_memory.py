"""Production contract tests for Layer 5 image memory."""
from __future__ import annotations

import pytest

from layers.layer05_image.modules.image_memory.image_memory import ImageMemory


def test_image_memory_rejects_invalid_inputs() -> None:
    memory = ImageMemory()
    with pytest.raises(ValueError, match="profile name"):
        memory.set_profile("")
    with pytest.raises(ValueError, match="platform"):
        memory.store_image("", "topic", "asset.png")
    with pytest.raises(ValueError, match="topic"):
        memory.store_image("instagram", "", "asset.png")
    with pytest.raises(ValueError, match="url"):
        memory.store_image("instagram", "topic", "")


def test_image_memory_bounds_history() -> None:
    memory = ImageMemory()
    for index in range(memory.MAX_HISTORY + 5):
        memory.store_image("instagram", f"topic-{index}", f"asset-{index}.png")
    assert memory.history_count == memory.MAX_HISTORY
    assert memory.get_history(limit=1)[0]["topic"] == f"topic-{memory.MAX_HISTORY + 4}"
    with pytest.raises(ValueError, match="between 1"):
        memory.get_history(limit=0)


def test_image_memory_requires_existing_profile_when_named() -> None:
    memory = ImageMemory()
    with pytest.raises(ValueError, match="Unknown visual profile"):
        memory.store_image("instagram", "topic", "asset.png", profile_name="missing")
    memory.set_profile("brand")
    record = memory.store_image("instagram", "topic", "asset.png", profile_name="brand")
    assert record["profile"] == "brand"


def test_image_memory_returns_copies_not_internal_records() -> None:
    memory = ImageMemory()
    memory.store_image("instagram", "topic", "asset.png")
    record = memory.get_history(limit=1)[0]
    record["topic"] = "mutated"
    assert memory.get_history(limit=1)[0]["topic"] == "topic"


def test_image_memory_profile_reads_are_snapshots() -> None:
    memory = ImageMemory()
    memory.set_profile("brand", colors=["#111111"])
    profile = memory.get_profile("brand")
    assert profile is not None
    profile.primary_colors.append("#222222")
    assert memory.get_profile("brand").primary_colors == ["#111111"]


def test_image_memory_rejects_boolean_history_limit() -> None:
    memory = ImageMemory()
    with pytest.raises(ValueError, match="between 1"):
        memory.get_history(limit=True)
