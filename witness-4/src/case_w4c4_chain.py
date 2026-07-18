"""
W4-C4: Append-only ledger chain integrity.

WITNESS-4 chains to WITNESS-3's PUBLISHED record_hash (Zenodo DOI 10.5281/zenodo.21434832),
so WITNESS-1..4 form one append-only, third-party-verifiable ledger. This case proves the
link is sound and that breaking it is detected.

Sub-cases:
  (a) HONEST LINK    : record.prev_record_hash resolves to the genuine WITNESS-3
                       record_hash (loaded from the sibling published record when present,
                       else the embedded genesis constant). -> link verified.
  (b) BROKEN LINK    : flip prev_record_hash. Detected THREE ways: chain-link check fails,
                       fused_nonce no longer verifies (prev link is folded into the nonce),
                       and record_hash no longer verifies. -> DETECTED.
  (c) MONOTONIC ORDER: current timestamp_utc >= previous record timestamp (append-only).

PASS: (a) verified AND (b) detected (all three signals) AND (c) monotonic.
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proofrecord_v4 import verify_record_hash, verify_fused_nonce, verify_chain_link
from freshness import parse_iso_utc

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"
W3_RECORD = Path(__file__).parent.parent.parent / "witness-3" / "results" / "proofrecord.json"
GENESIS_PREV_HASH = "858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf"


def _load(p):
    with open(p) as f:
        return json.load(f)


def main():
    pr = _load(RESULTS_DIR / "proofrecord.json")
    raw_counts = _load(RAW_DIR / "raw_counts.json")
    cal = _load(RAW_DIR / "calibration_snapshot.json")
    nist = _load(RAW_DIR / "nist_witness.json")
    astro = _load(RAW_DIR / "astro_witness.json")

    # Resolve the previous ledger record.
    if W3_RECORD.exists():
        prev_record = _load(W3_RECORD)
        prev_source = "witness-3/results/proofrecord.json (published, DOI 10.5281/zenodo.21434832)"
    else:
        prev_record = {"record_hash": GENESIS_PREV_HASH,
                       "timestamp_utc": "2026-07-18T22:31:00Z"}
        prev_source = "embedded genesis constant (WITNESS-3 published record_hash)"

    # (a) honest link
    a_link_ok = verify_chain_link(pr, prev_record) and (pr["prev_record_hash"] == GENESIS_PREV_HASH)

    # (b) broken link
    pr_b = copy.deepcopy(pr)
    ph = pr_b["prev_record_hash"]
    pr_b["prev_record_hash"] = ("0" + ph[1:]) if ph[0] != "0" else ("f" + ph[1:])
    b_chain_detected = not verify_chain_link(pr_b, prev_record)
    b_nonce_detected = not verify_fused_nonce(pr_b, raw_counts, cal, nist, astro)
    b_recordhash_detected = not verify_record_hash(pr_b)
    b_detected = b_chain_detected and b_nonce_detected and b_recordhash_detected

    # (c) monotonic order
    prev_ts = prev_record.get("timestamp_utc")
    if prev_ts:
        c_monotonic = parse_iso_utc(pr["timestamp_utc"]) >= parse_iso_utc(prev_ts)
    else:
        c_monotonic = True

    sub = {
        "a_honest_link": {"prev_source": prev_source,
                          "prev_record_hash": pr["prev_record_hash"],
                          "link_verified": a_link_ok},
        "b_broken_link": {"chain_link_detected": b_chain_detected,
                          "nonce_detected": b_nonce_detected,
                          "record_hash_detected": b_recordhash_detected,
                          "attack_detected": b_detected},
        "c_monotonic_order": {"prev_timestamp_utc": prev_ts,
                              "current_timestamp_utc": pr["timestamp_utc"],
                              "monotonic": c_monotonic},
    }
    all_pass = a_link_ok and b_detected and c_monotonic
    verdict = "PASS" if all_pass else "FAIL"
    doc = {"case": "W4-C4",
           "description": "Append-only ledger chain integrity linking WITNESS-4 to WITNESS-3",
           "verdict": verdict, "sub_cases": sub}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W4-C4-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
