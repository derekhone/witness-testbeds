"""
case_w1c3_replay.py — W1-C3: Cross-context replay protection.

Procedure (preregistered):
  Present the valid ProofRecord (context_id="witness-1-primary") to a second
  authorization context (different context_id). Use the ARK-457 replay-protection
  logic (ark457_replay.py) to evaluate the replay.

PASS iff the replay is DENIED (context_id mismatch detected).
The original context must be ALLOWED; the replay context must be DENIED.

Outputs verdict to stdout and writes results/W1-C3-result.json.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from proofrecord import load_proofrecord
from ark457_replay import AuthContext, check_context_replay

RESULTS_DIR = Path(__file__).parent.parent / "results"


def main():
    print("=== W1-C3: Cross-Context Replay Protection ===")

    # --- Load ProofRecord ---
    record = load_proofrecord(str(RESULTS_DIR / "proofrecord.json"))
    original_context_id = record["context_id"]  # "witness-1-primary"
    job_id = record["job_id"]

    print(f"ProofRecord context_id: {original_context_id}")
    print(f"ProofRecord job_id:     {job_id[:16]}...")

    # --- Construct contexts ---
    # Original context: must match the ProofRecord's context_id on the context_id dimension.
    # We model context_id as the "session" dimension in the ARK-457 5-dim tuple.
    original_ctx = AuthContext(
        tenant="remnant-fieldworks",
        session=original_context_id,          # "witness-1-primary"
        resource="witness-1-proofrecord",
        audience="witness-1-verifier",
        environment="experimental",
    )

    # Replay context: same as original except context_id (session) is different.
    replay_ctx = AuthContext(
        tenant="remnant-fieldworks",
        session="witness-1-replay-context",   # DIFFERENT — cross-context replay
        resource="witness-1-proofrecord",
        audience="witness-1-verifier",
        environment="experimental",
    )

    # --- Check original context (should be ALLOW) ---
    print("\nChecking original context (same context_id)...")
    original_verdict = check_context_replay(original_ctx, original_ctx)
    print(f"  decision: {original_verdict.decision}")
    print(f"  reason:   {original_verdict.reason}")

    # --- Check replay context (should be DENY) ---
    print("\nChecking replay context (different context_id)...")
    replay_verdict = check_context_replay(original_ctx, replay_ctx)
    print(f"  decision: {replay_verdict.decision}")
    print(f"  reason:   {replay_verdict.reason}")
    print(f"  mismatched_dims: {replay_verdict.mismatched_dims}")

    # --- Verdict ---
    # PASS iff: original → ALLOW, replay → DENY
    original_correct = original_verdict.decision == "ALLOW"
    replay_denied = replay_verdict.decision == "DENY"
    verdict = "PASS" if (original_correct and replay_denied) else "FAIL"

    print(f"\nW1-C3 VERDICT: {verdict}")
    print(f"  original ALLOW: {original_correct}")
    print(f"  replay DENIED:  {replay_denied}")

    output = {
        "case": "W1-C3",
        "verdict": verdict,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "original_context_decision": original_verdict.decision,
        "replay_context_decision": replay_verdict.decision,
        "original_correct": original_correct,
        "replay_denied": replay_denied,
        "mismatched_dims": replay_verdict.mismatched_dims,
        "original_context": original_ctx._asdict(),
        "replay_context": replay_ctx._asdict(),
        "ark457_replay_reason": replay_verdict.reason,
    }

    out_path = RESULTS_DIR / "W1-C3-result.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Result written to {out_path}")

    return verdict


if __name__ == "__main__":
    v = main()
    sys.exit(0 if v == "PASS" else 1)
