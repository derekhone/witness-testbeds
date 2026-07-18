"""
WITNESS-4 fused nonce construction — v4 (Freshness Bracket).

Extends the WITNESS-3 "Cosmic Beacon" 5-segment nonce (QPU counts, job_id, calibration,
NIST beacon, LIGO/GWOSC astro) with TWO additional length-prefixed segments that bind the
temporal bracket and the append-only ledger link into the nonce itself:

  6. precommit_hash      : SHA-256 of the pre-commitment doc (design fixed before anchors).
  7. prev_record_hash    : record_hash of the previous WITNESS ledger entry
                           (genesis = WITNESS-3 published record_hash).

    fused_nonce = SHA-256(
        LP(precommit_hash)
      ‖ LP(prev_record_hash)
      ‖ LP(canonical_json(raw_counts))
      ‖ LP(job_id)
      ‖ LP(canonical_json(calibration_snapshot))
      ‖ LP(canonical_json(nist_beacon_record))
      ‖ LP(canonical_json(astro_witness_record))
    )

LP(x) = struct.pack('>I', len(x)) + x  (4-byte big-endian length prefix; boundary-collision safe).

DESIGN INTENT: no single input controls the nonce, and the nonce is inseparable from BOTH
the pre-commitment (proving design preceded the random anchors) and the previous ledger
link (proving append-only order). Forging it requires simultaneously forging an IBM
provider job record, a signed NIST pulse, a byte-exact LIGO file, AND a consistent
pre-commitment + chain link. This is a provenance / freshness / ordering construction, NOT
a claim of information-theoretic min-entropy from any one source.
"""

import hashlib
import json
import struct


def canonical_json(obj: object) -> str:
    """Deterministic compact JSON. Keys sorted, no spaces, ensure_ascii."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def lp(data: bytes) -> bytes:
    if len(data) > 0xFFFFFFFF:
        raise ValueError(f"Component too large for 4-byte prefix: {len(data)} bytes")
    return struct.pack(">I", len(data)) + data


def _cj(obj: object) -> bytes:
    return canonical_json(obj).encode("utf-8")


def compute_fused_nonce(
    precommit_hash: str,
    prev_record_hash: str,
    raw_counts: dict,
    job_id: str,
    calibration_snapshot: dict,
    nist_beacon_record: dict,
    astro_witness_record: dict,
) -> str:
    """SHA-256 over the seven length-prefixed segments. Returns 64-char hex."""
    stream = (
        lp(precommit_hash.encode("utf-8"))
        + lp(prev_record_hash.encode("utf-8"))
        + lp(_cj(raw_counts))
        + lp(job_id.encode("utf-8"))
        + lp(_cj(calibration_snapshot))
        + lp(_cj(nist_beacon_record))
        + lp(_cj(astro_witness_record))
    )
    return hashlib.sha256(stream).hexdigest()


def sha256_canonical(obj: object) -> str:
    return hashlib.sha256(_cj(obj)).hexdigest()


def compute_raw_counts_hash(raw_counts: dict) -> str:
    return sha256_canonical(raw_counts)


def compute_calibration_hash(calibration_snapshot: dict) -> str:
    return sha256_canonical(calibration_snapshot)


def compute_nist_hash(nist_beacon_record: dict) -> str:
    return sha256_canonical(nist_beacon_record)


def compute_astro_hash(astro_witness_record: dict) -> str:
    return sha256_canonical(astro_witness_record)
