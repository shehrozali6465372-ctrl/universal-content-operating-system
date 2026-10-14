"""Shared image-size parser contract tests."""
import pytest

from layers.layer05_image.modules.image_provider.image_provider import parse_image_size


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("256x256", (256, 256)),
        ("1024x1024", (1024, 1024)),
        ("4096x256", (4096, 256)),
        ("1536X1024", (1536, 1024)),
    ],
)
def test_parse_image_size_accepts_valid_dimensions(value, expected):
    assert parse_image_size(value) == expected


@pytest.mark.parametrize("value", ["", "1024", "1024x", "widextall", "128x1024", "1024x5000", None])
def test_parse_image_size_rejects_invalid_dimensions(value):
    with pytest.raises(ValueError):
        parse_image_size(value)
