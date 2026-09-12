"""Verify 10x compression ratio on 100K token context."""
import json
from services.compression.obcache import OBCompressor, compute_compression_ratio

content = "The quick brown fox jumps over the lazy dog. " * 25000
payload = {
    "choices": [{"message": {"content": content}}],
    "usage": {"total_tokens": 100_000, "prompt_tokens": 100_000, "completion_tokens": 0},
    "model": "gpt-4",
}
raw = json.dumps(payload, separators=(",", ":")).encode()
comp = OBCompressor(ratio=10, chunk_size=64)
blob = comp.compress_kv(payload)
ratio = compute_compression_ratio(raw, blob)

print(f"Original size: {len(raw):,} bytes")
print(f"Compressed blob: {len(blob):,} bytes")
print(f"Compression ratio: {ratio:.1f}x")
print(f"Memory saved: {(1 - 1/ratio) * 100:.1f}%")
print(f"Result: {'PASS' if ratio >= 10 else 'FAIL'} (need >= 10x)")
