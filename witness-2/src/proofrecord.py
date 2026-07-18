"""
WITNESS-2 ProofRecord — schema_version: witness-proofrecord-1.0

record_hash = SHA-256(canonical_json(all fields except record_hash, sorted keys))

Design boundary: record_hash provides field integrity. An attacker who changes context_id
AND recomputes record_hash produces a valid record_hash — context_id enforcement therefore
requires a separate authorization layer (ARK-457 context-binding library). Explicitly
tested in W2-C3 sub-case (b).
"""

import hashlib

try:
    # Package-relative import (when imported as src.proofrecord)
    from .nonce import canonical_json
except ImportError:
    # Flat import fallback (when src is on sys.path and imported as `proofrecord`)
    from nonce import canonical_json

SCHEMA_VERSION = "witness-proofrecord-1.0"


def build_proofrecord(
    quantum_nonce: str,
    job_id: str,
    backend: str,
    provider_instance: str,
    calibration_hash: str,
    raw_counts_hash: str,
    context_id: str,
    timestamp_utc: str,
) -> dict:
    fields = {
        "schema_version": SCHEMA_VERSION,
        "quantum_nonce": quantum_nonce,
        "job_id": job_id,
        "backend": backend,
        "provider_instance": provider_instance,
        "calibration_hash": calibration_hash,
        "raw_counts_hash": raw_counts_hash,
        "context_id": context_id,
        "timestamp_utc": timestamp_utc,
    }
    record_hash = hashlib.sha256(canonical_json(fields).encode('utf-8')).hexdigest()
    return {**fields, "record_hash": record_hash}


def verify_record_hash(record: dict) -> bool:
    fields = {k: v for k, v in record.items() if k != "record_hash"}
    expected = hashlib.sha256(canonical_json(fields).encode('utf-8')).hexdigest()
    return expected == record.get("record_hash", "")


def verify_quantum_nonce(record: dict, raw_counts: dict, calibration_snapshot: dict) -> bool:
    try:
        from .nonce import compute_quantum_nonce
    except ImportError:
        from nonce import compute_quantum_nonce
    expected = compute_quantum_nonce(raw_counts, record["job_id"], calibration_snapshot)
    return expected == record.get("quantum_nonce", "")
