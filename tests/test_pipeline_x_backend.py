"""Tests for pipeline X backend dispatch including xcom_rs."""

import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib import pipeline, schema


class TestRetrieveStreamXcomRs(unittest.TestCase):
    """_retrieve_stream dispatches to xcom_rs when backend is xcom_rs."""

    @mock.patch("lib.xcom_rs_x.search_x")
    @mock.patch("lib.xcom_rs_x.parse_response")
    @mock.patch("lib.env.get_x_source", return_value="xcom_rs")
    def test_xcom_rs_dispatch(self, _env, mock_parse, mock_search):
        mock_search.return_value = {"items": [{"id": "1", "text": "t", "permanent_url": "https://x.com/u/status/1"}]}
        mock_parse.return_value = [{"id": "X1", "text": "t", "url": "https://x.com/u/status/1", "author_handle": "u", "date": "2026-03-15", "engagement": {}, "relevance": 0.8}]

        runtime = schema.ProviderRuntime(
            reasoning_provider="gemini",
            planner_model="m",
            rerank_model="m",
            x_search_backend="xcom_rs",
        )
        subquery = schema.SubQuery(
            label="test",
            search_query="test query",
            ranking_query="test",
            sources=["x"],
        )
        items, artifact = pipeline._retrieve_stream(
            topic="test",
            subquery=subquery,
            source="x",
            config={},
            depth="quick",
            date_range=("2026-03-01", "2026-03-30"),
            runtime=runtime,
            mock=False,
        )
        mock_search.assert_called_once()
        mock_parse.assert_called_once()
        self.assertEqual(1, len(items))

    @mock.patch("lib.bird_x.search_x")
    @mock.patch("lib.bird_x.parse_bird_response")
    @mock.patch("lib.env.get_x_source", return_value="bird")
    def test_bird_dispatch_still_works(self, _env, mock_parse, mock_search):
        mock_search.return_value = {"items": []}
        mock_parse.return_value = []

        runtime = schema.ProviderRuntime(
            reasoning_provider="gemini",
            planner_model="m",
            rerank_model="m",
            x_search_backend="bird",
        )
        subquery = schema.SubQuery(
            label="test",
            search_query="test",
            ranking_query="test",
            sources=["x"],
        )
        items, _ = pipeline._retrieve_stream(
            topic="test",
            subquery=subquery,
            source="x",
            config={},
            depth="quick",
            date_range=("2026-03-01", "2026-03-30"),
            runtime=runtime,
            mock=False,
        )
        mock_search.assert_called_once()


class TestSupplementalSearchXcomRs(unittest.TestCase):
    """_run_supplemental_searches uses xcom_rs when backend is xcom_rs."""

    @mock.patch("lib.xcom_rs_x.search_handles")
    @mock.patch("lib.env.get_x_source", return_value="xcom_rs")
    def test_handle_search_uses_xcom_rs(self, _env, mock_handles):
        mock_handles.return_value = [
            {"id": "X1", "text": "handle tweet", "url": "https://x.com/alice/status/1",
             "author_handle": "alice", "date": "2026-03-15", "engagement": {}, "relevance": 0.8}
        ]

        runtime = schema.ProviderRuntime(
            reasoning_provider="gemini",
            planner_model="m",
            rerank_model="m",
            x_search_backend="xcom_rs",
        )
        plan = schema.QueryPlan(
            intent="test",
            freshness_mode="recent",
            cluster_mode="topic",
            raw_topic="test",
            subqueries=[
                schema.SubQuery(label="primary", search_query="test", ranking_query="test", sources=["x"]),
            ],
            source_weights={"x": 1.0},
        )
        bundle = schema.RetrievalBundle()

        pipeline._run_supplemental_searches(
            topic="test",
            bundle=bundle,
            plan=plan,
            config={},
            depth="default",
            date_range=("2026-03-01", "2026-03-30"),
            runtime=runtime,
            mock=False,
            rate_limited_sources=set(),
            rate_limit_lock=threading.Lock(),
            x_handle="alice",
        )

        mock_handles.assert_called_once()
        # Items should be added to the bundle
        self.assertTrue(bundle.items_by_source.get("x"))


class TestSupplementalSearchBirdFallback(unittest.TestCase):
    """_run_supplemental_searches still uses bird_x when backend is bird."""

    @mock.patch("lib.bird_x.search_handles")
    @mock.patch("lib.env.get_x_source", return_value="bird")
    def test_handle_search_uses_bird(self, _env, mock_handles):
        mock_handles.return_value = [
            {"id": "X1", "text": "handle tweet", "url": "https://x.com/bob/status/1",
             "author_handle": "bob", "date": "2026-03-15", "engagement": {}, "relevance": 0.8}
        ]

        runtime = schema.ProviderRuntime(
            reasoning_provider="gemini",
            planner_model="m",
            rerank_model="m",
            x_search_backend="bird",
        )
        plan = schema.QueryPlan(
            intent="test",
            freshness_mode="recent",
            cluster_mode="topic",
            raw_topic="test",
            subqueries=[
                schema.SubQuery(label="primary", search_query="test", ranking_query="test", sources=["x"]),
            ],
            source_weights={"x": 1.0},
        )
        bundle = schema.RetrievalBundle()

        pipeline._run_supplemental_searches(
            topic="test",
            bundle=bundle,
            plan=plan,
            config={},
            depth="default",
            date_range=("2026-03-01", "2026-03-30"),
            runtime=runtime,
            mock=False,
            rate_limited_sources=set(),
            rate_limit_lock=threading.Lock(),
            x_handle="bob",
        )

        mock_handles.assert_called_once()


class TestSupplementalSearchXaiSkipped(unittest.TestCase):
    """_run_supplemental_searches returns early for xai backend (no handle search)."""

    @mock.patch("lib.env.get_x_source", return_value="xai")
    def test_xai_skips_handle_search(self, _env):
        runtime = schema.ProviderRuntime(
            reasoning_provider="gemini",
            planner_model="m",
            rerank_model="m",
            x_search_backend="xai",
        )
        plan = schema.QueryPlan(
            intent="test",
            freshness_mode="recent",
            cluster_mode="topic",
            raw_topic="test",
            subqueries=[
                schema.SubQuery(label="primary", search_query="test", ranking_query="test", sources=["x"]),
            ],
            source_weights={"x": 1.0},
        )
        bundle = schema.RetrievalBundle()

        pipeline._run_supplemental_searches(
            topic="test",
            bundle=bundle,
            plan=plan,
            config={},
            depth="default",
            date_range=("2026-03-01", "2026-03-30"),
            runtime=runtime,
            mock=False,
            rate_limited_sources=set(),
            rate_limit_lock=threading.Lock(),
            x_handle="alice",
        )

        # No X items should be added
        self.assertFalse(bundle.items_by_source.get("x"))


if __name__ == "__main__":
    unittest.main()
