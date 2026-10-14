"""Regression tests for shared vector math and the exact flat index."""
import math

import pytest

from layers.shared.vector_math import cosine_similarity
from layers.layer13_persistence.modules.vector_database_platform.vector_index import VectorIndex


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([1.0, 0.0], [1.0, 0.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([0.0, 0.0], [1.0, 0.0], 0.0),
        ([1.0], [1.0, 2.0], 0.0),
        ([], [], 0.0),
    ],
)
def test_cosine_similarity_handles_normal_and_edge_vectors(left, right, expected):
    assert cosine_similarity(left, right) == pytest.approx(expected)


def test_vector_index_rebuild_refreshes_dimension_and_searches():
    index = VectorIndex()
    index.add(1, [1.0, 0.0, 0.0])
    index.add(2, [0.0, 1.0, 0.0])
    assert index.rebuild() is True
    assert index.stats()["dimensions"] == 3
    assert index.search([1.0, 0.0, 0.0], top_k=1) == [(1, 1.0)]


def test_vector_index_rebuild_rejects_inconsistent_or_nonfinite_vectors():
    mixed = VectorIndex()
    mixed.add(1, [1.0, 0.0])
    mixed.add(2, [1.0, 0.0, 0.0])
    assert mixed.rebuild() is False

    invalid = VectorIndex()
    invalid.add(1, [1.0, float("nan")])
    assert invalid.rebuild() is False
