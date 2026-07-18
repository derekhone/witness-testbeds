"""
WITNESS-4 ProofRecord — schema_version: witness-proofrecord-4.0 (Freshness Bracket).

Extends witness-proofrecord-3.0 with:
  - precommit_hash       : SHA-256 of the pre-commitment document (design-before-anchor).
  - prev_record_hash     : previous ledger link (genesis = WITNESS-3 record_hash).
  - freshness            : the evaluated temporal-bracket check block.
  - nist_pulse_time / precommit_time_utc echoed for direct auditability.

record_hash = SHA-256(canonical_json(all fields except record_hash, sorted keys)).

Design boundary (unchanged): record_hash provides field integrity only; cross-context
authorization enforcement is delegated to the ARK-457 layer. The freshness bracket
establishes a *lower* time bound (not-before) and design-before-anchor ordering only — it
is NOT a trusted timestamping/notarization authority and asserts no upper time bound.
"""

import hashlib

try:
    from .nonce_v4 import canonical_json
    from .freshness import evaluate_freshness
except ImportError:
    from nonce_v4 import canonical_json
    from freshness import evaluate_freshness

SCHEMA_VERSION = "witness-proofrecord-4.0"


def build_proofrecord(
    fused_nonce: str,
    precommit_hash: str,
    prev_record_hash: str,
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
    nist_pulse_time: str,
    precommit_time_utc: str,
    timestamp_utc: str,
    prev_record_timestamp_utc: str | None = None,
) -> dict:
    chsh_summary = {
        "S": chsh_result["S"],
        "abs_S": chsh_result["abs_S"],
        "sigma_S": chsh_result["sigma_S"],
        "classical_bound": chsh_result["classical_bound"],
        "tsirelson_bound": chsh_result["tsirelson_bound"],
        "sigmas_above_classical": chsh_result["sigmas_above_classical"],
        "correlators": chsh_result["correlators"],
    }
    freshness = evaluate_freshness(
        record_timestamp_utc=timestamp_utc,
        nist_pulse_time=nist_pulse_time,
        precommit_time_utc=precommit_time_utc,
        prev_record_timestamp_utc=prev_record_timestamp_utc,
    )
    fields = {
        "schema_version": SCHEMA_VERSION,
        "fused_nonce": fused_nonce,
        "precommit_hash": precommit_hash,
        "prev_record_hash": prev_record_hash,
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
        "nist_pulse_time": nist_pulse_time,
        "precommit_time_utc": precommit_time_utc,
        "freshness": freshness,
        "timestamp_utc": timestamp_utc,
    }
    record_hash = hashlib.sha256(canonical_json(fields).encode("utf-8")).hexdigest()
    return {**fields, "record_hash": record_hash}


def verify_record_hash(record: dict) -> bool:
    fields = {k: v for k, v in record.items() if k != "record_hash"}
    expected = hashlib.sha256(canonical_json(fields).encode("utf-8")).hexdigest()
    return expected == record.get("record_hash", "")


def verify_fused_nonce(
    record: dict,
    raw_counts: dict,
    calibration_snapshot: dict,
    nist_beacon_record: dict,
    astro_witness_record: dict,
) -> bool:
    try:
        from .nonce_v4 import compute_fused_nonce
    except ImportError:
        from nonce_v4 import compute_fused_nonce
    expected = compute_fused_nonce(
        record["precommit_hash"], record["prev_record_hash"],
        raw_counts, record["job_id"], calibration_snapshot,
        nist_beacon_record, astro_witness_record,
    )
    return expected == record.get("fused_nonce", "")


def verify_chain_link(record: dict, prev_record: dict | None) -> bool:
    """The current record must reference the previous record's record_hash."""
    if prev_record is None:
        return False
    return record.get("prev_record_hash", "") == prev_record.get("record_hash", "__none__")
