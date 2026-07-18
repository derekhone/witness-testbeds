"""
WITNESS-3 ProofRecord — schema_version: witness-proofrecord-3.0 (Cosmic Beacon).

Extends witness-proofrecord-1.0 with:
  - three independent witness hashes (qpu raw_counts, NIST beacon, LIGO/GWOSC astro),
  - the CHSH result block (S, sigma_S, correlators, violation significance),
  - a bell_certified boolean (the preregistered device-dependent certification flag).

record_hash = SHA-256(canonical_json(all fields except record_hash, sorted keys)).

Design boundary (unchanged from WITNESS-2): record_hash provides field integrity only.
context_id enforcement is delegated to the ARK-457 authorization layer and tested in W3-C3.
"""

import hashlib

try:
    from .nonce_v3 import canonical_json
except ImportError:
    from nonce_v3 import canonical_json

SCHEMA_VERSION = "witness-proofrecord-3.0"


def build_proofrecord(
    cosmic_nonce: str,
    job_id: str,
    backend: str,
    provider_instance: str,
    calibration_hash: str,
    raw_counts_hash: str,
    nist_hash: str,
    astro_hash: str,
    chsh_result: dict,
    bell_certified: bool,
    context_id: str,
    timestamp_utc: str,
) -> dict:
    # Store a compact, deterministic CHSH summary inside the record.
    chsh_summary = {
        "S": chsh_result["S"],
        "abs_S": chsh_result["abs_S"],
        "sigma_S": chsh_result["sigma_S"],
        "classical_bound": chsh_result["classical_bound"],
        "tsirelson_bound": chsh_result["tsirelson_bound"],
        "sigmas_above_classical": chsh_result["sigmas_above_classical"],
        "correlators": chsh_result["correlators"],
    }
    fields = {
        "schema_version": SCHEMA_VERSION,
        "cosmic_nonce": cosmic_nonce,
        "job_id": job_id,
        "backend": backend,
        "provider_instance": provider_instance,
        "calibration_hash": calibration_hash,
        "raw_counts_hash": raw_counts_hash,
        "nist_hash": nist_hash,
        "astro_hash": astro_hash,
        "chsh": chsh_summary,
        "bell_certified": bool(bell_certified),
        "context_id": context_id,
        "timestamp_utc": timestamp_utc,
    }
    record_hash = hashlib.sha256(canonical_json(fields).encode("utf-8")).hexdigest()
    return {**fields, "record_hash": record_hash}


def verify_record_hash(record: dict) -> bool:
    fields = {k: v for k, v in record.items() if k != "record_hash"}
    expected = hashlib.sha256(canonical_json(fields).encode("utf-8")).hexdigest()
    return expected == record.get("record_hash", "")


def verify_cosmic_nonce(
    record: dict,
    raw_counts: dict,
    calibration_snapshot: dict,
    nist_beacon_record: dict,
    astro_witness_record: dict,
) -> bool:
    try:
        from .nonce_v3 import compute_cosmic_nonce
    except ImportError:
        from nonce_v3 import compute_cosmic_nonce
    expected = compute_cosmic_nonce(
        raw_counts, record["job_id"], calibration_snapshot,
        nist_beacon_record, astro_witness_record,
    )
    return expected == record.get("cosmic_nonce", "")
