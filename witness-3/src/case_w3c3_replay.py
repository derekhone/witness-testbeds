"""
W3-C3: Cross-context replay (two-layer architecture, 2 sub-cases). Mirrors WITNESS-2.

Sub-case (a): alter context_id WITHOUT recomputing record_hash.
  -> record_hash mismatch -> replay DENIED at the field-integrity layer.

Sub-case (b): alter context_id AND recompute record_hash (attacker knows the schema).
  -> record_hash is valid (this is the design boundary, not a defect).
  -> present to the ARK-457 5-dimensional context binding; session mismatch -> DENY.

PASS (each sub-case): replay is DENIED (regardless of which layer fires).
"""

import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce_v3 import canonical_json
from proofrecord_v3 import verify_record_hash
from ark457_replay import AuthContext, check_context_replay

RESULTS_DIR = Path(__file__).parent.parent / "results"


def _recompute_record_hash(rec: dict) -> str:
    fields = {k: v for k, v in rec.items() if k != "record_hash"}
    return hashlib.sha256(canonical_json(fields).encode("utf-8")).hexdigest()


def main():
    with open(RESULTS_DIR / "proofrecord.json") as f:
        pr = json.load(f)

    orig_ctx = pr["context_id"]
    replay_ctx = orig_ctx + "-REPLAYED"

    # Sub-case (a): change context_id, do NOT recompute record_hash.
    pr_a = copy.deepcopy(pr)
    pr_a["context_id"] = replay_ctx
    a_denied = not verify_record_hash(pr_a)  # mismatch => denied

    # Sub-case (b): change context_id AND recompute record_hash (valid seal).
    pr_b = copy.deepcopy(pr)
    pr_b["context_id"] = replay_ctx
    pr_b["record_hash"] = _recompute_record_hash(pr_b)
    b_record_hash_valid = verify_record_hash(pr_b)  # expected True (design boundary)

    original_context = AuthContext(
        tenant="rf", session=orig_ctx, resource="witness-3",
        audience="rf-auth", environment="prod")
    presented_context = AuthContext(
        tenant="rf", session=replay_ctx, resource="witness-3",
        audience="rf-auth", environment="prod")
    verdict_457 = check_context_replay(original_context, presented_context)
    b_denied = (verdict_457.decision == "DENY")

    sub = {
        "a_no_recompute": {
            "record_hash_detected_mismatch": a_denied,
            "replay_denied": a_denied,
        },
        "b_recompute_then_ark457": {
            "record_hash_valid_after_recompute": b_record_hash_valid,
            "ark457_verdict": verdict_457.decision,
            "ark457_reason": verdict_457.reason,
            "replay_denied": b_denied,
            "design_boundary_note": (
                "record_hash valid after recompute is the expected, correct behaviour: "
                "record_hash is a field-integrity seal, not a context-binding mechanism. "
                "The DENY verdict is produced by the ARK-457 authorization layer."
            ),
        },
    }
    all_denied = sub["a_no_recompute"]["replay_denied"] and sub["b_recompute_then_ark457"]["replay_denied"]
    verdict = "PASS" if all_denied else "FAIL"
    doc = {"case": "W3-C3",
           "description": "Cross-context replay: field-integrity + ARK-457 two-layer defence",
           "verdict": verdict, "sub_cases": sub}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W3-C3-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
