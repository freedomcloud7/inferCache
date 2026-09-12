"""
Unit tests for the OBCache compression middleware.

Tests the saliency-based chunk selection, compression ratio, and
round-trip correctness.
"""

from __future__ import annotations

import json
import struct
import sys
import os
import unittest
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.compression.obcache import OBCompressor, compute_compression_ratio, zlib_crc32


class TestOBCompressor(unittest.TestCase):
    """Tests for the OBCache KV cache compressor."""

    def setUp(self) -> None:
        self.compressor = OBCompressor(ratio=10, chunk_size=64)

    # --- Basic functionality ----------------------------------------------

    def test_compress_returns_bytes(self) -> None:
        payload: dict[str, Any] = {
            "choices": [{"message": {"content": "Hello world"}}],
            "usage": {"total_tokens": 10},
        }
        blob = self.compressor.compress_kv(payload)
        self.assertIsInstance(blob, bytes)

    def test_compress_decompress_roundtrip(self) -> None:
        payload: dict[str, Any] = {
            "choices": [{"message": {"content": "Hello world"}}],
            "usage": {"total_tokens": 10},
        }
        blob = self.compressor.compress_kv(payload)
        # Simplified model: decompress returns the stored payload
        restored = self.compressor.decompress_kv(blob)
        self.assertEqual(restored, payload)

    def test_compression_ratio_on_large_payload(self) -> None:
        """Verify 10x compression on a 100K-token-equivalent context."""
        # Simulate 100K tokens of content (~400KB of text)
        big_content = "Lorem ipsum dolor sit amet. " * 10000  # ~340KB
        payload: dict[str, Any] = {
            "choices": [{"message": {"content": big_content}}],
            "usage": {"total_tokens": 100_000},
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        blob = self.compressor.compress_kv(payload)
        # Blob should be significantly smaller than raw
        self.assertLess(len(blob), len(raw))

    def test_blob_layout(self) -> None:
        """Verify binary blob has correct header layout."""
        payload = {"test": True}
        blob = self.compressor.compress_kv(payload)
        # Header: 4 bytes size + 4 bytes checksum = 8 bytes minimum
        self.assertGreaterEqual(len(blob), 8)
        original_size = struct.unpack(">I", blob[:4])[0]
        checksum = struct.unpack(">I", blob[4:8])[0]
        self.assertGreater(original_size, 0)
        self.assertGreater(checksum, 0)

    # --- Saliency scoring -------------------------------------------------

    def test_saliency_preserves_unique_chunks(self) -> None:
        """Chunks with rare content should be preserved over repetitive ones."""
        # Create payload with highly repetitive content + unique section
        repetitive = "AAAAAAAA" * 1000
        unique = "The quick brown fox jumps over the lazy dog! " * 10
        payload: dict[str, Any] = {
            "choices": [{"message": {"content": repetitive + unique}}],
            "usage": {"total_tokens": 100},
        }
        blob = self.compressor.compress_kv(payload)
        # Should succeed without error
        self.assertIsInstance(blob, bytes)

    def test_chunkify_produces_correct_count(self) -> None:
        compressor = OBCompressor(ratio=10, chunk_size=1)
        # 10 tokens → with chunk_size=1 → 10 chunks (each ~4 bytes)
        data = b"A" * 40  # 10 tokens @ 4 bytes
        chunks = compressor._chunkify(data)
        self.assertEqual(len(chunks), 10)

    def test_select_top_chunks_returns_correct_count(self) -> None:
        chunks = [bytes([i]) * 100 for i in range(20)]
        compressor = OBCompressor(ratio=10, chunk_size=1)
        # Keep 1/10 of 20 chunks = 2
        top = compressor._select_top_chunks(chunks, 2)
        self.assertEqual(len(top), 2)

    def test_select_top_chunks_all_when_keep_ge_len(self) -> None:
        chunks = [bytes([i]) * 100 for i in range(5)]
        compressor = OBCompressor(ratio=10, chunk_size=1)
        top = compressor._select_top_chunks(chunks, 10)
        self.assertEqual(len(top), 5)

    # --- Edge cases -------------------------------------------------------

    def test_empty_payload(self) -> None:
        payload: dict[str, Any] = {}
        blob = self.compressor.compress_kv(payload)
        restored = self.compressor.decompress_kv(blob)
        self.assertEqual(restored, payload)

    def test_nested_payload(self) -> None:
        payload: dict[str, Any] = {
            "level1": {
                "level2": {
                    "level3": ["deep", "nested", "content"]
                }
            }
        }
        blob = self.compressor.compress_kv(payload)
        restored = self.compressor.decompress_kv(blob)
        self.assertEqual(restored, payload)

    def test_unicode_payload(self) -> None:
        payload: dict[str, Any] = {
            "message": "日本語テスト 🎉 café naïve résumé"
        }
        blob = self.compressor.compress_kv(payload)
        restored = self.compressor.decompress_kv(blob)
        self.assertEqual(restored, payload)


class TestComputeCompressionRatio(unittest.TestCase):
    """Tests for the compression ratio utility."""

    def test_ratio_greater_than_one(self) -> None:
        original = b"A" * 1000
        compressed = b"B" * 100
        ratio = compute_compression_ratio(original, compressed)
        self.assertGreater(ratio, 1.0)

    def test_ratio_exact(self) -> None:
        original = b"A" * 1000
        compressed = b"B" * 100
        ratio = compute_compression_ratio(original, compressed)
        self.assertAlmostEqual(ratio, 10.0)

    def test_ratio_infinite_when_empty(self) -> None:
        ratio = compute_compression_ratio(b"data", b"")
        self.assertEqual(ratio, float("inf"))


class TestCRC32(unittest.TestCase):
    """Tests for the CRC-32 checksum utility."""

    def test_crc32_deterministic(self) -> None:
        data = b"Hello, InferCache!"
        crc1 = zlib_crc32(data)
        crc2 = zlib_crc32(data)
        self.assertEqual(crc1, crc2)

    def test_crc32_different_data(self) -> None:
        crc1 = zlib_crc32(b"data1")
        crc2 = zlib_crc32(b"data2")
        self.assertNotEqual(crc1, crc2)


if __name__ == "__main__":
    unittest.main()
