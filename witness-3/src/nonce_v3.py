"""
WITNESS-3 fused "Cosmic Beacon" nonce construction — v3.

The authorization nonce is bound to THREE independent, publicly re-verifiable witnesses:

  1. QPU witness      : raw measurement counts from a CHSH Bell-test job on IBM hardware
                        (+ job_id + deterministic calibration snapshot).
  2. NIST witness     : one pulse from the NIST public Randomness Beacon v2
                        (pulseIndex, timeStamp, outputValue, chain/certificate ids).
  3. Astro witness    : a fixed public LIGO/GWOSC strain data file (SHA-256 of the exact
                        bytes) plus a deterministic strain-sample digest and metadata.

Length-prefixed concatenation (as in WITNESS-2) prevents boundary-collision between the
components, extended here from 3 to 5 length-prefixed segments.

    LP(x) = struct.pack('>I', len(x)) + x            (4-byte big-endian uint32 prefix)

    cosmic_nonce = SHA-256(
        LP(canonical_json(raw_counts))
      ‖ LP(job_id)
      ‖ LP(canonical_json(calibration_snapshot))
      ‖ LP(canonical_json(nist_beacon_record))
      ‖ LP(canonical_json(astro_witness_record))
    )

canonical_json: json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=True)

DESIGN INTENT: no single witness controls the nonce. An adversary would have to
simultaneously forge (a) an IBM provider job record, (b) a signed NIST beacon pulse, and
(c) a byte-exact LIGO public data file — each independently auditable — to forge a nonce.
This is a provenance / freshness construction, NOT a claim of information-theoretic
min-entropy from any one source.
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


def _cj_bytes(obj: object) -> bytes:
    return canonical_json(obj).encode('utf-8')


def compute_cosmic_nonce(
    raw_counts: dict,
    job_id: str,
    calibration_snapshot: dict,
    nist_beacon_record: dict,
    astro_witness_record: dict,
) -> str:
    """SHA-256 over the five length-prefixed witness segments. Returns 64-char hex."""
    stream = (
        lp(_cj_bytes(raw_counts))
        + lp(job_id.encode('utf-8'))
        + lp(_cj_bytes(calibration_snapshot))
        + lp(_cj_bytes(nist_beacon_record))
        + lp(_cj_bytes(astro_witness_record))
    )
    return hashlib.sha256(stream).hexdigest()


def sha256_canonical(obj: object) -> str:
    """SHA-256 of canonical_json(obj) — used for per-witness independent hashes."""
    return hashlib.sha256(_cj_bytes(obj)).hexdigest()


def compute_raw_counts_hash(raw_counts: dict) -> str:
    return sha256_canonical(raw_counts)


def compute_calibration_hash(calibration_snapshot: dict) -> str:
    return sha256_canonical(calibration_snapshot)


def compute_nist_hash(nist_beacon_record: dict) -> str:
    return sha256_canonical(nist_beacon_record)


def compute_astro_hash(astro_witness_record: dict) -> str:
    return sha256_canonical(astro_witness_record)
