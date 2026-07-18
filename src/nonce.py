"""
nonce.py — Canonical JSON serialization and SHA-256 nonce derivation.

Nonce construction (preregistered):
    nonce = SHA-256(canonical_json(raw_counts) || job_id || canonical_json(calibration_snapshot))

Canonical JSON: sorted keys, no whitespace, UTF-8.
Concatenation: byte-level, no separator.
"""

import hashlib
import json


def canonical_json(obj: dict) -> bytes:
    """
    Serialize a dict to canonical JSON: sorted keys, no whitespace, UTF-8.
    Raises ValueError if input is not a dict.
    """
    if not isinstance(obj, dict):
        raise ValueError(f"canonical_json requires a dict, got {type(obj).__name__}")
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return lowercase hex SHA-256 digest of data."""
    return hashlib.sha256(data).hexdigest()


def derive_nonce(raw_counts: dict, job_id: str, calibration_snapshot: dict) -> str:
    """
    Derive the ProofRecord nonce per the preregistered construction:
        nonce = SHA-256(canonical_json(raw_counts) || job_id || canonical_json(calibration_snapshot))

    Args:
        raw_counts: dict mapping bitstring -> int (IBM Quantum measurement counts)
        job_id: IBM Quantum job ID string
        calibration_snapshot: dict of backend calibration properties

    Returns:
        64-char lowercase hex SHA-256 string
    """
    counts_bytes = canonical_json(raw_counts)
    jobid_bytes = job_id.encode("utf-8")
    cal_bytes = canonical_json(calibration_snapshot)
    payload = counts_bytes + jobid_bytes + cal_bytes
    return sha256_hex(payload)


def raw_counts_hash(raw_counts: dict) -> str:
    """Return SHA-256 hex of canonical_json(raw_counts)."""
    return sha256_hex(canonical_json(raw_counts))


def calibration_hash(calibration_snapshot: dict) -> str:
    """Return SHA-256 hex of canonical_json(calibration_snapshot)."""
    return sha256_hex(canonical_json(calibration_snapshot))
