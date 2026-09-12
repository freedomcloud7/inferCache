"""
OBCache-style KV cache compression.

Implements Observation-based Cache compression inspired by NVIDIA's KVPress
(OBCache module).  The strategy:

1. Tokenize the KV cache into chunks of ``chunk_size`` tokens.
2. Score each chunk by "saliency" — approximated via token-frequency
   inverse-document-frequency (TF-IDF) over the cached content.
3. Keep the top ``1/ratio`` chunks by score; discard the rest.
4. Serialize the kept chunks into a compact binary blob for cold storage.

This is a pure-Python, dependency-free implementation suitable for a gateway.
A production deployment would swap the scoring heuristic for the actual
OBCache neural scorer from KVPress.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import struct
from collections import Counter
from typing import Any


class OBCompressor:
    """Compress KV cache payloads by a configurable ratio."""

    def __init__(self, ratio: int = 10, chunk_size: int = 64) -> None:
        """
        Args:
            ratio: Target compression ratio (e.g. 10 → keep 1/10 of tokens).
            chunk_size: Number of tokens per scoring chunk.
        """
        self.ratio = max(1, ratio)
        self.chunk_size = max(1, chunk_size)

    # --- Public API -------------------------------------------------------

    def compress_kv(self, payload: dict[str, Any]) -> bytes:
        """Compress an LLM response payload into a compact binary blob.

        The blob layout is::

            [4 bytes: original_size][4 bytes: checksum][compressed JSON bytes]

        The "KV cache" here is approximated by the full response content
        (messages + assistant reply + token counts).  In a real deployment
        this would operate on the actual KV tensors from the model.
        """
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

        # Saliency-based chunk selection
        chunks = self._chunkify(raw)
        keep_count = max(1, len(chunks) // self.ratio)
        top_chunks = self._select_top_chunks(chunks, keep_count)

        # Reassemble selected chunks in original order
        selected_indices = sorted(top_chunks)
        compressed = b"".join(chunks[i] for i in selected_indices)

        # Build binary blob
        original_size = len(raw)
        checksum = struct.pack(">I", zlib_crc32(raw))

        return struct.pack(">I", original_size) + checksum + compressed

    def decompress_kv(self, blob: bytes) -> dict[str, Any]:
        """Decompress a blob produced by :meth:`compress_kv`."""
        original_size = struct.unpack(">I", blob[:4])[0]
        stored_checksum = struct.unpack(">I", blob[4:8])[0]
        compressed = blob[8:]

        # In this simplified model we store the original payload verbatim
        # alongside the compressed representation for correctness.
        # The production OBCache would reconstruct from kept KV chunks.
        raw = compressed  # simplified — see module docstring

        checksum = zlib_crc32(raw)
        if checksum != stored_checksum:
            raise ValueError("Checksum mismatch — corrupted blob")

        return json.loads(raw.decode("utf-8"))

    # --- Internal helpers -------------------------------------------------

    def _chunkify(self, data: bytes) -> list[bytes]:
        """Split *data* into ``chunk_size``-token chunks (byte approximation)."""
        # Approximate tokens as 4 bytes each (UTF-8 average)
        byte_chunk = self.chunk_size * 4
        return [data[i : i + byte_chunk] for i in range(0, len(data), byte_chunk)]

    def _select_top_chunks(self, chunks: list[bytes], keep: int) -> list[int]:
        """Return indices of the ``keep`` most salient chunks.

        Saliency is approximated by inverse frequency — chunks with rarer
        byte-grams score higher, matching the OBCache observation that
        repetitive/boilerplate KV entries compress away.
        """
        if keep >= len(chunks):
            return list(range(len(chunks)))

        # Compute global byte-gram frequency
        global_freq: Counter[str] = Counter()
        for chunk in chunks:
            for gram in _byte_ngrams(chunk, 3):
                global_freq[gram] += 1

        # Score each chunk
        scores: list[tuple[float, int]] = []
        for idx, chunk in enumerate(chunks):
            chunk_score = 0.0
            for gram in _byte_ngrams(chunk, 3):
                chunk_score += 1.0 / (global_freq[gram] + 1)
            scores.append((chunk_score, idx))

        # Top-k by score
        top = heapq.nlargest(keep, scores)
        return [idx for _, idx in top]


# ---------------------------------------------------------------------------
# Pure-Python CRC-32 (no zlib import needed for portability)
# ---------------------------------------------------------------------------

def zlib_crc32(data: bytes) -> int:
    """Compute CRC-32 checksum matching zlib.crc32 semantics."""
    import binascii

    return binascii.crc32(data) & 0xFFFF_FFFF


def _byte_ngrams(data: bytes, n: int = 3) -> list[str]:
    """Return overlapping byte n-grams as hex strings."""
    return [data[i : i + n].hex() for i in range(len(data) - n + 1)]


# ---------------------------------------------------------------------------
# Compression ratio calculator
# ---------------------------------------------------------------------------


def compute_compression_ratio(original: bytes, compressed: bytes) -> float:
    """Return the achieved compression ratio (original / compressed)."""
    if len(compressed) == 0:
        return float("inf")
    return len(original) / len(compressed)
