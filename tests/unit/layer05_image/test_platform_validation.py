"""Layer 5 platform validation contract tests."""
import pytest

from layers.layer05_image.modules.carousel_planner.carousel_planner import CarouselPlanner
from layers.layer05_image.modules.image_prompt.image_prompt import ImagePromptBuilder
from layers.layer05_image.modules.thumbnail_engine.thumbnail_engine import ThumbnailEngine


@pytest.mark.parametrize(
    ("planner", "kwargs"),
    [
        (CarouselPlanner(), {"topic": "test", "platform": "unsupported"}),
        (ImagePromptBuilder(), {"description": "test", "platform": "unsupported"}),
        (ThumbnailEngine(), {"topic": "test", "platform": "unsupported"}),
    ],
)
def test_unsupported_platforms_fail_closed(planner, kwargs):
    with pytest.raises(ValueError, match="Unsupported"):
        planner.plan(**kwargs) if isinstance(planner, (CarouselPlanner, ThumbnailEngine)) else planner.build(**kwargs)
