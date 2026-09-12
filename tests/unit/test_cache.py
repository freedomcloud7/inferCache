"""
Unit tests for the CacheManager two-tier cache.

Uses fakeredis and a mock MinIO to avoid external dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestCacheManagerInit(unittest.TestCase):
    """Test CacheManager initialization."""

    def test_init_stores_params(self) -> None:
        from services.cache.manager import CacheManager

        mgr = CacheManager(
            redis_url="redis://localhost:6379/0",
            minio_endpoint="localhost:9000",
            minio_access_key="test",
            minio_secret_key="test",
            minio_bucket="test-bucket",
            ttl=300,
        )
        self.assertEqual(mgr.ttl, 300)
        self.assertEqual(mgr.bucket, "test-bucket")

    def test_hot_key_format(self) -> None:
        from services.cache.manager import CacheManager

        key = CacheManager._hot_key("abc123")
        self.assertEqual(key, "ic:hot:abc123")

    def test_cold_key_format(self) -> None:
        from services.cache.manager import CacheManager

        key = CacheManager._cold_key("abc123")
        self.assertTrue(key.endswith(".bin"))
        self.assertIn("ic/cold/", key)


class TestCacheManagerColdOps(unittest.TestCase):
    """Test cold-tier (MinIO) operations."""

    def test_cold_key_ends_with_bin(self) -> None:
        from services.cache.manager import CacheManager

        mgr = CacheManager(
            redis_url="redis://localhost:6379",
            minio_endpoint="localhost:9000",
            minio_access_key="test",
            minio_secret_key="test",
            minio_bucket="test",
        )
        self.assertTrue(CacheManager._cold_key("key").endswith(".bin"))


class TestMetricsCollector(unittest.TestCase):
    """Tests for the Prometheus-compatible metrics collector."""

    def setUp(self) -> None:
        from services.metrics.exporter import MetricsCollector

        self.metrics = MetricsCollector()

    def test_initial_hit_rate_zero(self) -> None:
        self.assertEqual(self.metrics.hit_rate, 0.0)

    def test_hit_rate_after_hits(self) -> None:
        self.metrics.record_hit(1000)
        self.metrics.record_miss()
        self.assertAlmostEqual(self.metrics.hit_rate, 0.5)

    def test_memory_saved_increases_on_hit(self) -> None:
        initial = self.metrics.memory_saved_mb
        self.metrics.record_hit(1024 * 1024)  # 1MB request
        self.assertGreater(self.metrics.memory_saved_mb, initial)

    def test_active_sessions_tracking(self) -> None:
        self.metrics.session_start("sess-1")
        self.assertEqual(self.metrics.active_sessions, 1)
        self.metrics.session_start("sess-2")
        self.assertEqual(self.metrics.active_sessions, 2)
        self.metrics.session_end("sess-1")
        self.assertEqual(self.metrics.active_sessions, 1)

    def test_cost_savings_positive_after_hits(self) -> None:
        self.metrics.record_hit(4000)  # ~1KB → ~1K tokens saved
        self.assertGreater(self.metrics.cost_savings, 0.0)

    def test_prometheus_output_contains_required_metrics(self) -> None:
        self.metrics.record_hit(1000)
        output = self.metrics.to_prometheus()
        required = [
            "infercache_cache_hits_total",
            "infercache_hit_rate",
            "infercache_memory_saved_mb",
            "infercache_active_sessions",
            "infercache_cost_savings_usd",
        ]
        for metric in required:
            self.assertIn(metric, output)


class TestCompressionIntegration(unittest.TestCase):
    """Integration test: compressor + metrics + cache key."""

    def test_full_pipeline(self) -> None:
        from services.compression.obcache import OBCompressor
        from services.metrics.exporter import MetricsCollector

        compressor = OBCompressor(ratio=10)
        metrics = MetricsCollector()

        payload = {
            "choices": [{"message": {"content": "test"}}],
            "usage": {"total_tokens": 100},
        }

        # Simulate cache miss
        metrics.record_miss()

        # Compress for cold storage
        blob = compressor.compress_kv(payload)
        self.assertIsInstance(blob, bytes)

        # Simulate cache hit next time
        metrics.record_hit(len(json.dumps(payload)))
        self.assertGreater(metrics.hit_rate, 0)


if __name__ == "__main__":
    unittest.main()
