"""
WITNESS-2 nonce construction — v2.
Length-prefixed SHA-256 over (canonical_json(raw_counts), job_id, canonical_json(calibration_snapshot)).

LP(x) = struct.pack('>I', len(x)) + x   (4-byte big-endian uint32 prefix)

This prevents two different component splits from hashing to the same byte stream.
canonical_json: json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=True)
Count keys must be strings; values must be JSON integers.
"""

import hashlib
import json
import struct


def canonical_json(obj: object) -> str:
    """Deterministic compact JSON. Keys sorted, no spaces, ensure_ascii."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def lp(data: bytes) -> bytes:
    """4-byte big-endian uint32 length prefix concatenated with data."""
    if len(data) > 0xFFFFFFFF:
        raise ValueError(f"Component too large for 4-byte prefix: {len(data)} bytes")
    return struct.pack('>I', len(data)) + data


def compute_quantum_nonce(raw_counts: dict, job_id: str, calibration_snapshot: dict) -> str:
    """SHA-256(LP(counts_bytes) || LP(jobid_bytes) || LP(cal_bytes))."""
    counts_bytes = canonical_json(raw_counts).encode('utf-8')
    jobid_bytes  = job_id.encode('utf-8')
    cal_bytes    = canonical_json(calibration_snapshot).encode('utf-8')
    return hashlib.sha256(lp(counts_bytes) + lp(jobid_bytes) + lp(cal_bytes)).hexdigest()


def compute_raw_counts_hash(raw_counts: dict) -> str:
    return hashlib.sha256(canonical_json(raw_counts).encode('utf-8')).hexdigest()


def compute_calibration_hash(calibration_snapshot: dict) -> str:
    return hashlib.sha256(canonical_json(calibration_snapshot).encode('utf-8')).hexdigest()
