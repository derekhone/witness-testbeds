"""
proofrecord.py — ProofRecord build, save, load, and verify.

ProofRecord schema (preregistered):
    {
        "nonce":            <hex str, 64 chars>,
        "job_id":           <str>,
        "backend":          <str>,
        "calibration_hash": <hex str, 64 chars>,
        "timestamp_utc":    <ISO-8601 UTC str>,
        "raw_counts_hash":  <hex str, 64 chars>,
        "context_id":       <str>
    }

Verification: recompute nonce from stored raw_counts + job_id + calibration_snapshot;
confirm it matches the ProofRecord nonce.  Provider check is performed separately
(case_w1c1_verify.py) against the IBM Quantum API.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from nonce import derive_nonce, raw_counts_hash, calibration_hash


PROOF_RECORD_VERSION = "witness.proofrecord/v1"


def build_proofrecord(
    raw_counts: dict,
    job_id: str,
    backend: str,
    calibration_snapshot: dict,
    context_id: str,
    timestamp_utc: Optional[str] = None,
) -> dict:
    """
    Build a ProofRecord from QPU execution artifacts.

    Args:
        raw_counts: measurement counts from IBM Quantum job
        job_id: IBM Quantum job ID
        backend: backend name string
        calibration_snapshot: backend calibration properties dict
        context_id: authorization context identifier for this record
        timestamp_utc: ISO-8601 UTC string; defaults to now if not provided

    Returns:
        ProofRecord dict
    """
    if timestamp_utc is None:
        timestamp_utc = datetime.now(timezone.utc).isoformat()

    nonce = derive_nonce(raw_counts, job_id, calibration_snapshot)

    return {
        "schema": PROOF_RECORD_VERSION,
        "nonce": nonce,
        "job_id": job_id,
        "backend": backend,
        "calibration_hash": calibration_hash(calibration_snapshot),
        "timestamp_utc": timestamp_utc,
        "raw_counts_hash": raw_counts_hash(raw_counts),
        "context_id": context_id,
    }


def save_proofrecord(record: dict, path: str) -> None:
    """Write ProofRecord to a JSON file (pretty-printed for readability)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.write("\n")


def load_proofrecord(path: str) -> dict:
    """Load a ProofRecord from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verify_proofrecord(
    record: dict,
    raw_counts: dict,
    job_id: str,
    calibration_snapshot: dict,
) -> dict:
    """
    Verify a ProofRecord by recomputing the nonce and comparing hashes.

    Args:
        record: the ProofRecord dict to verify
        raw_counts: original raw counts (from storage or provider)
        job_id: original job ID (from storage or provider)
        calibration_snapshot: original calibration snapshot (from storage)

    Returns:
        dict with keys:
            nonce_match: bool
            counts_hash_match: bool
            cal_hash_match: bool
            jobid_match: bool
            all_pass: bool
            detail: dict with computed vs stored values
    """
    recomputed_nonce = derive_nonce(raw_counts, job_id, calibration_snapshot)
    recomputed_counts_hash = raw_counts_hash(raw_counts)
    recomputed_cal_hash = calibration_hash(calibration_snapshot)

    nonce_match = recomputed_nonce == record.get("nonce")
    counts_hash_match = recomputed_counts_hash == record.get("raw_counts_hash")
    cal_hash_match = recomputed_cal_hash == record.get("calibration_hash")
    jobid_match = job_id == record.get("job_id")

    return {
        "nonce_match": nonce_match,
        "counts_hash_match": counts_hash_match,
        "cal_hash_match": cal_hash_match,
        "jobid_match": jobid_match,
        "all_pass": nonce_match and counts_hash_match and cal_hash_match and jobid_match,
        "detail": {
            "recomputed_nonce": recomputed_nonce,
            "stored_nonce": record.get("nonce"),
            "recomputed_counts_hash": recomputed_counts_hash,
            "stored_counts_hash": record.get("raw_counts_hash"),
            "recomputed_cal_hash": recomputed_cal_hash,
            "stored_cal_hash": record.get("calibration_hash"),
            "supplied_job_id": job_id,
            "stored_job_id": record.get("job_id"),
        },
    }
