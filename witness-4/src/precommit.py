"""
WITNESS-4 pre-commitment module.

The pre-commitment is a small, deterministic document that fixes the *entire
experimental design* BEFORE any unpredictable public anchor (the NIST beacon pulse or
the QPU measurement outcomes) is known to the harness. Its SHA-256 is folded into the
fused nonce and stored in the ProofRecord.

Why this matters (the honest, verifiable claim):
  - The pre-commitment fixes: the CHSH circuit spec (angles, qubit pair, shots), the
    declared intent string, the context_id, and the previous ledger link (prev_record_hash).
  - Because the pre-commitment is written and hashed BEFORE the beacon pulse is fetched,
    an auditor can confirm the design was chosen independently of the beacon value.
  - Combined with the NIST pulse's forward-unpredictability (its value did not exist
    before its release timeStamp), this establishes a *not-before* lower time bound on
    the finalized record: the record could not have been produced before the pulse time,
    yet its design was fixed before the pulse value was known.

WHAT THIS IS NOT (preregistered non-claim):
  - This is NOT a trusted timestamping authority and NOT a blockchain. It does not prove
    an absolute wall-clock creation time. It proves a *relative ordering*: design fixed
    before anchor; record finalized at-or-after the anchor's published time. There is no
    upper time bound (a record can always be finalized later). Disclosed honestly.
"""

import hashlib
import json


def canonical_json(obj: object) -> str:
    """Deterministic compact JSON. Keys sorted, no spaces, ensure_ascii (matches nonce_v4)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_precommit(
    circuit_spec: dict,
    intent: str,
    context_id: str,
    prev_record_hash: str,
    precommit_time_utc: str,
) -> dict:
    """
    Build the pre-commitment document. This must be called and its hash persisted
    BEFORE fetching the NIST beacon or submitting the QPU job.
    """
    return {
        "kind": "witness-4-precommit",
        "schema_version": "witness-precommit-4.0",
        "intent": intent,
        "context_id": context_id,
        "prev_record_hash": prev_record_hash,
        "precommit_time_utc": precommit_time_utc,
        "circuit_spec": circuit_spec,
    }


def compute_precommit_hash(precommit_doc: dict) -> str:
    """SHA-256 of the canonical JSON of the pre-commitment document. 64-char hex."""
    return hashlib.sha256(canonical_json(precommit_doc).encode("utf-8")).hexdigest()


def verify_precommit_hash(precommit_doc: dict, expected_hash: str) -> bool:
    return compute_precommit_hash(precommit_doc) == expected_hash


if __name__ == "__main__":
    demo = build_precommit(
        circuit_spec={"bell_state": "phi_plus", "qubits": [0, 1], "shots": 2000,
                      "angles": {"a": 0.0, "a_prime": 1.5707963267948966,
                                 "b": 0.7853981633974483, "b_prime": 2.356194490192345}},
        intent="WITNESS-4 freshness-bracket authorization nonce",
        context_id="rf-witness-4:demo",
        prev_record_hash="0" * 64,
        precommit_time_utc="2026-07-18T00:00:00Z",
    )
    print(json.dumps(demo, indent=2, sort_keys=True))
    print("precommit_hash:", compute_precommit_hash(demo))
