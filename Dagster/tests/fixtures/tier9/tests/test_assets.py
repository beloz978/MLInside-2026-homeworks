"""Фикстура чекера: pytest для ассетов (чекер ищет materialize в tests/test_*.py). Сам pytest Dagster/tests её не собирает."""
import dagster as dg

from t9_proj import marts, raw, staging


def test_graph_materializes():
    assert dg.materialize([*raw, *staging, *marts]).success
