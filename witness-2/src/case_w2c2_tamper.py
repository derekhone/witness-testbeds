"""
W2-C2: Substitution / tamper detection — 4 sub-trials.

(a) raw_counts altered       -> quantum_nonce mismatch -> DETECT
(b) job_id altered           -> quantum_nonce + record_hash mismatch -> DETECT
(c) calibration altered      -> quantum_nonce mismatch -> DETECT
(d) context_id altered, record_hash NOT recomputed -> record_hash mismatch -> DETECT

PASS criterion: all 4 sub-trials detect the substitution (forgery_detected=True).
"""

import json
import sys
import copy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proofrecord import verify_record_hash, verify_quantum_nonce

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR     = RESULTS_DIR / "raw"


def main():
    with open(RAW_DIR / "raw_counts.json") as f:
        raw_counts = json.load(f)
    with open(RAW_DIR / "calibration_snapshot.json") as f:
        cal = json.load(f)
    with open(RESULTS_DIR / "proofrecord.json") as f:
        pr = json.load(f)

    trials = []

    # (a) Alter raw_counts — swap two count values
    fc = dict(raw_counts)
    keys = list(fc.keys())
    fc[keys[0]], fc[keys[1]] = fc[keys[1]], fc[keys[0]]
    nonce_ok = verify_quantum_nonce(pr, fc, cal)
    detected = not nonce_ok
    trials.append({
        "sub_trial": "a", "substitution": "raw_counts_altered",
        "quantum_nonce_match": nonce_ok, "forgery_detected": detected,
        "detection_layer": "quantum_nonce",
        "sub_verdict": "PASS" if detected else "FAIL",
    })

    # (b) Alter job_id
    fpb = copy.deepcopy(pr)
    fpb["job_id"] = pr["job_id"] + "_FORGED"
    nonce_ok_b = verify_quantum_nonce(fpb, raw_counts, cal)
    rec_ok_b   = verify_record_hash(fpb)
    detected_b = not nonce_ok_b or not rec_ok_b
    trials.append({
        "sub_trial": "b", "substitution": "job_id_altered",
        "quantum_nonce_match": nonce_ok_b, "record_hash_match": rec_ok_b,
        "forgery_detected": detected_b,
        "detection_layer": "quantum_nonce and record_hash",
        "sub_verdict": "PASS" if detected_b else "FAIL",
    })

    # (c) Alter calibration_snapshot — flip one readout_error value
    fc2 = copy.deepcopy(cal)
    k0  = sorted(fc2["readout_error_by_qubit"].keys())[0]
    v0  = fc2["readout_error_by_qubit"][k0]
    fc2["readout_error_by_qubit"][k0] = 0.9999 if v0 != 0.9999 else 0.0001
    nonce_ok_c = verify_quantum_nonce(pr, raw_counts, fc2)
    detected_c = not nonce_ok_c
    trials.append({
        "sub_trial": "c", "substitution": "calibration_snapshot_altered",
        "quantum_nonce_match": nonce_ok_c, "forgery_detected": detected_c,
        "detection_layer": "quantum_nonce",
        "sub_verdict": "PASS" if detected_c else "FAIL",
    })

    # (d) Alter context_id WITHOUT recomputing record_hash
    fpd = copy.deepcopy(pr)
    fpd["context_id"] = "witness-2-FORGED-context"
    rec_ok_d  = verify_record_hash(fpd)
    detected_d = not rec_ok_d
    trials.append({
        "sub_trial": "d", "substitution": "context_id_altered_record_hash_not_updated",
        "record_hash_match": rec_ok_d, "forgery_detected": detected_d,
        "detection_layer": "record_hash",
        "sub_verdict": "PASS" if detected_d else "FAIL",
    })

    verdict = "PASS" if all(t["sub_verdict"] == "PASS" for t in trials) else "FAIL"
    doc = {
        "case": "W2-C2",
        "description": "Substitution / tamper detection (4 sub-trials)",
        "verdict": verdict,
        "sub_trials": trials,
    }
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W2-C2-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
