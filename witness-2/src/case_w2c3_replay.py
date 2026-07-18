"""
W2-C3: Cross-context replay — 2 sub-cases.

Sub-case (a): context_id changed, record_hash NOT recomputed.
  -> Caught by record_hash mismatch.
  -> DENY. Expected: PASS.

Sub-case (b): context_id changed, record_hash RECOMPUTED with new context_id.
  -> record_hash is valid (attacker recomputed it). Expected — record_hash provides
     field integrity only, not context_id enforcement.
  -> Caught by ARK-457 5-dimensional context-binding library.
  -> DENY. Expected: PASS.

Design boundary note: record_hash provides field integrity; context_id enforcement
requires a separate authorization layer (ARK-457). Both layers present and tested.

PASS criterion: both sub-cases result in DENY (regardless of which layer fires).
"""

import json
import sys
import copy
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proofrecord import verify_record_hash
from nonce import canonical_json
from ark457_replay import AuthContext, check_context_replay

RESULTS_DIR = Path(__file__).parent.parent / "results"


def main():
    with open(RESULTS_DIR / "proofrecord.json") as f:
        pr = json.load(f)

    orig_ctx_id   = pr["context_id"]        # "witness-2-primary"
    replay_ctx_id = "witness-2-replay-context"

    sub_cases = []

    # --- Sub-case (a): context_id changed, record_hash NOT recomputed ---
    fa = copy.deepcopy(pr)
    fa["context_id"] = replay_ctx_id
    rec_valid_a = verify_record_hash(fa)
    denied_a    = not rec_valid_a
    sub_cases.append({
        "sub_case": "a",
        "description": "context_id changed, record_hash not recomputed",
        "record_hash_valid": rec_valid_a,
        "enforcement_layer": "record_hash",
        "replay_decision": "DENY" if denied_a else "ALLOW",
        "sub_verdict": "PASS" if denied_a else "FAIL",
    })

    # --- Sub-case (b): context_id changed, record_hash RECOMPUTED ---
    fb_fields = {k: v for k, v in pr.items() if k != "record_hash"}
    fb_fields["context_id"] = replay_ctx_id
    new_rh = hashlib.sha256(canonical_json(fb_fields).encode('utf-8')).hexdigest()
    fb = {**fb_fields, "record_hash": new_rh}

    rec_valid_b = verify_record_hash(fb)    # True — attacker recomputed it (expected)

    # Apply ARK-457 5-dim context binding
    orig_auth_ctx   = AuthContext(
        tenant="remnant-fieldworks", session=orig_ctx_id,
        resource="witness-2-nonce", audience="verifier", environment="production",
    )
    replay_auth_ctx = AuthContext(
        tenant="remnant-fieldworks", session=replay_ctx_id,  # session differs
        resource="witness-2-nonce", audience="verifier", environment="production",
    )

    orig_verdict   = check_context_replay(orig_auth_ctx,   orig_auth_ctx)
    replay_verdict = check_context_replay(orig_auth_ctx, replay_auth_ctx)

    denied_b = replay_verdict.decision == "DENY"
    sub_cases.append({
        "sub_case": "b",
        "description": "context_id changed, record_hash recomputed — boundary test",
        "record_hash_valid": rec_valid_b,
        "enforcement_layer": "ark457_context_binding",
        "original_decision": orig_verdict.decision,
        "replay_decision": replay_verdict.decision,
        "mismatched_dimensions": replay_verdict.mismatched_dims,
        "design_boundary_note": (
            "record_hash valid because attacker recomputed it. "
            "DENY enforced by ARK-457 5-dim context binding. "
            "Confirms: record_hash = field integrity only; "
            "context_id enforcement requires separate authorization layer."
        ),
        "sub_verdict": "PASS" if denied_b else "FAIL",
    })

    verdict = "PASS" if all(sc["sub_verdict"] == "PASS" for sc in sub_cases) else "FAIL"
    doc = {
        "case": "W2-C3",
        "description": "Cross-context replay — record_hash integrity and ARK-457 boundary",
        "verdict": verdict,
        "sub_cases": sub_cases,
    }
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W2-C3-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
