"""
case_w1c2_tamper.py — W1-C2: Substitution / tamper detection.

Three independent sub-trials (preregistered):
  (a) Substitute raw_counts with a different valid-format counts dict.
  (b) Substitute job_id with a different string.
  (c) Substitute calibration_snapshot with a different valid-format dict.

Each substitution is applied to one field only; the others remain as-is from results/raw/.
Verification is re-run against the stored (unmodified) ProofRecord after each substitution.

PASS iff ALL THREE substitutions are detected as forged (nonce mismatch reported for each).

Outputs verdict to stdout and writes results/W1-C2-result.json.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent))

from proofrecord import load_proofrecord, verify_proofrecord

RESULTS_RAW = Path(__file__).parent.parent / "results" / "raw"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def make_substitute_counts(original: dict) -> dict:
    """Create a clearly different counts dict (flip the first bitstring key)."""
    sub = deepcopy(original)
    keys = list(sub.keys())
    if keys:
        # Change the first key's first character to a different bit
        k = keys[0]
        flipped = ("1" if k[0] == "0" else "0") + k[1:]
        # Avoid collision if flipped key already exists
        if flipped in sub:
            flipped = k[:-1] + ("1" if k[-1] == "0" else "0")
        v = sub.pop(k)
        sub[flipped] = v + 1  # also change count to be sure
    return sub


def make_substitute_job_id(original: str) -> str:
    """Return a clearly different job ID string."""
    return original + "_TAMPERED"


def make_substitute_calibration(original: dict) -> dict:
    """Return a clearly different calibration dict."""
    sub = deepcopy(original)
    sub["backend_name"] = sub.get("backend_name", "unknown") + "_TAMPERED"
    sub["num_qubits"] = sub.get("num_qubits", 8) + 1
    return sub


def run_subtrial(label: str, record: dict, raw_counts: dict, job_id: str, calibration: dict) -> dict:
    """Run verification with the supplied (possibly tampered) inputs. PASS = forgery detected."""
    result = verify_proofrecord(
        record=record,
        raw_counts=raw_counts,
        job_id=job_id,
        calibration_snapshot=calibration,
    )
    # PASS for this sub-trial means verification FAILS (forgery detected = nonce mismatch)
    forgery_detected = not result["all_pass"]
    sub_verdict = "PASS" if forgery_detected else "FAIL"
    print(f"  [{label}] nonce_match={result['nonce_match']}  forgery_detected={forgery_detected}  sub_verdict={sub_verdict}")
    return {
        "sub_trial": label,
        "sub_verdict": sub_verdict,
        "forgery_detected": forgery_detected,
        "verification_result": result,
    }


def main():
    print("=== W1-C2: Substitution / Tamper Detection ===")

    # --- Load artifacts ---
    raw_counts = load_json(RESULTS_RAW / "raw_counts.json")
    job_meta = load_json(RESULTS_RAW / "job_meta.json")
    calibration = load_json(RESULTS_RAW / "calibration.json")
    record = load_proofrecord(str(RESULTS_DIR / "proofrecord.json"))

    job_id = job_meta["job_id"]

    sub_results = []

    # --- Sub-trial (a): substitute raw_counts ---
    print("\nSub-trial (a): Substitute raw_counts")
    tampered_counts = make_substitute_counts(raw_counts)
    sa = run_subtrial("a: tampered_counts", record, tampered_counts, job_id, calibration)
    sub_results.append(sa)

    # --- Sub-trial (b): substitute job_id ---
    print("\nSub-trial (b): Substitute job_id")
    tampered_job_id = make_substitute_job_id(job_id)
    sb = run_subtrial("b: tampered_job_id", record, raw_counts, tampered_job_id, calibration)
    sub_results.append(sb)

    # --- Sub-trial (c): substitute calibration_snapshot ---
    print("\nSub-trial (c): Substitute calibration_snapshot")
    tampered_calibration = make_substitute_calibration(calibration)
    sc = run_subtrial("c: tampered_calibration", record, raw_counts, job_id, tampered_calibration)
    sub_results.append(sc)

    # --- Overall verdict ---
    all_pass = all(s["sub_verdict"] == "PASS" for s in sub_results)
    verdict = "PASS" if all_pass else "FAIL"
    print(f"\nW1-C2 VERDICT: {verdict}  (all 3 substitutions detected: {all_pass})")

    output = {
        "case": "W1-C2",
        "verdict": verdict,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "all_substitutions_detected": all_pass,
        "sub_trials": sub_results,
    }

    out_path = RESULTS_DIR / "W1-C2-result.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Result written to {out_path}")

    return verdict


if __name__ == "__main__":
    v = main()
    sys.exit(0 if v == "PASS" else 1)
