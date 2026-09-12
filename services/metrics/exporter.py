"""
Prometheus-compatible metrics collector for InferCache.

Tracks:
- Cache hit rate (hits / total)
- Memory saved (MB) via compression
- Active sessions
- Estimated cost savings (USD)
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock


class MetricsCollector:
    """Thread-safe in-memory metrics store."""

    def __init__(self, window_seconds: int = 3600) -> None:
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._tokens_processed = 0
        self._bytes_saved = 0
        self._active_sessions: dict[str, float] = {}
        self._start_time = time.time()
        self._window = window_seconds

    # --- Recording --------------------------------------------------------

    def record_hit(self, request_size_bytes: int) -> None:
        with self._lock:
            self._hits += 1
            # Estimate memory saved: we returned a cached response instead of
            # recomputing KV cache for request_size_bytes of context.
            self._bytes_saved += request_size_bytes * 0.9  # ~90% savings

    def record_miss(self) -> None:
        with self._lock:
            self._misses += 1

    def record_tokens(self, count: int) -> None:
        with self._lock:
            self._tokens_processed += count

    def session_start(self, session_id: str) -> None:
        with self._lock:
            self._active_sessions[session_id] = time.time()

    def session_end(self, session_id: str) -> None:
        with self._lock:
            self._active_sessions.pop(session_id, None)

    # --- Queries ----------------------------------------------------------

    @property
    def hit_rate(self) -> float:
        with self._lock:
            total = self._hits + self._misses
            if total == 0:
                return 0.0
            return self._hits / total

    @property
    def memory_saved_mb(self) -> float:
        with self._lock:
            return self._bytes_saved / (1024 * 1024)

    @property
    def active_sessions(self) -> int:
        with self._lock:
            return len(self._active_sessions)

    @property
    def cost_savings(self) -> float:
        """Estimate cost savings from cache hits.

        Assumes $0.01 per 1K tokens (conservative average across providers).
        Each hit avoids one full forward pass.
        """
        with self._lock:
            # Each hit saved ~request_size_bytes of context processing
            # Roughly 1 token per 4 bytes
            tokens_saved = self._bytes_saved / 4
            return (tokens_saved / 1000) * 0.01

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus exposition format."""
        lines = [
            "# HELP infercache_cache_hits_total Total cache hits",
            "# TYPE infercache_cache_hits_total counter",
            f"infercache_cache_hits_total {self._hits}",
            "",
            "# HELP infercache_cache_misses_total Total cache misses",
            "# TYPE infercache_cache_misses_total counter",
            f"infercache_cache_misses_total {self._misses}",
            "",
            "# HELP infercache_hit_rate Current cache hit rate",
            "# TYPE infercache_hit_rate gauge",
            f"infercache_hit_rate {self.hit_rate:.4f}",
            "",
            "# HELP infercache_memory_saved_mb Memory saved via compression (MB)",
            "# TYPE infercache_memory_saved_mb gauge",
            f"infercache_memory_saved_mb {self.memory_saved_mb:.2f}",
            "",
            "# HELP infercache_active_sessions Current active sessions",
            "# TYPE infercache_active_sessions gauge",
            f"infercache_active_sessions {self.active_sessions}",
            "",
            "# HELP infercache_cost_savings_usd Estimated cost savings (USD)",
            "# TYPE infercache_cost_savings_usd gauge",
            f"infercache_cost_savings_usd {self.cost_savings:.4f}",
            "",
            "# HELP infercache_tokens_processed_total Total tokens processed",
            "# TYPE infercache_tokens_processed_total counter",
            f"infercache_tokens_processed_total {self._tokens_processed}",
        ]
        return "\n".join(lines) + "\n"
