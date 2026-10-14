from __future__ import annotations

import pytest

from layers.shared.vector_math import cosine_similarity, dot_product
from layers.layer13_persistence.modules.vector_database_platform.similarity_search import SimilaritySearch


def test_cosine_similarity_handles_normal_and_invalid_dimensions():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_dot_product_handles_dimension_mismatch():
    assert dot_product([1.0, 2.0], [3.0, 4.0]) == pytest.approx(11.0)
    assert dot_product([1.0], [1.0, 2.0]) == 0.0


def test_similarity_search_unknown_metric_falls_back_to_shared_cosine():
    search = SimilaritySearch()
    search.set_metric("unrecognized")
    results = search.search([1.0, 0.0], [(1, [0.0, 1.0]), (2, [1.0, 0.0])])
    assert results[0][0] == 2
    assert results[0][1] == pytest.approx(1.0)
