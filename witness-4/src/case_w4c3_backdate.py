"""
W4-C3: Backdating / pre-computation attack detection (the flagship freshness case).

An adversary holds a genuine ProofRecord and wants to claim it existed EARLIER than it
really did (backdating), or that its design was chosen AFTER seeing the random anchor
(pre-computation). Both are defeated by re-evaluating the freshness bracket independently
from the record's own timestamps — NOT by trusting the stored `freshness` block (a forger
would recompute that too). The not-before bound is meaningful because the fused nonce
commits to a NIST beacon outputValue that did not exist before its published pulse time.

Sub-cases (a forger recomputes record_hash so field integrity passes — that is expected):
  (a) BACKDATE      : set timestamp_utc EARLIER than nist_pulse_time.
                      -> not_before_bound_ok == False -> DETECTED.
  (b) PRE-COMPUTE   : set precommit_time_utc AFTER nist_pulse_time
                      (claim the design was fixed after the anchor was known).
                      -> design_before_anchor_ok == False -> DETECTED.
  (c) HONEST BASELINE: the genuine record must evaluate fresh == True (no false positive).

PASS: (a) and (b) are detected AND (c) is fresh.
"""

import copy
import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from freshness import evaluate_freshness, parse_iso_utc

RESULTS_DIR = Path(__file__).parent.parent / "results"


def _fmt(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    with open(RESULTS_DIR / "proofrecord.json") as f:
        pr = json.load(f)

    nist_pulse_time = pr["nist_pulse_time"]
    precommit_time = pr["precommit_time_utc"]
    genuine_ts = pr["timestamp_utc"]
    t_pulse = parse_iso_utc(nist_pulse_time)

    # (a) BACKDATE: claim an effective time one hour before the beacon pulse.
    backdated_ts = _fmt(t_pulse - timedelta(hours=1))
    fa = evaluate_freshness(record_timestamp_utc=backdated_ts,
                            nist_pulse_time=nist_pulse_time,
                            precommit_time_utc=precommit_time)
    a_detected = (fa["not_before_bound_ok"] is False) and (fa["fresh"] is False)

    # (b) PRE-COMPUTE: claim the design was fixed one hour AFTER the beacon pulse.
    precompute_pre = _fmt(t_pulse + timedelta(hours=1))
    fb = evaluate_freshness(record_timestamp_utc=genuine_ts,
                            nist_pulse_time=nist_pulse_time,
                            precommit_time_utc=precompute_pre)
    b_detected = (fb["design_before_anchor_ok"] is False) and (fb["fresh"] is False)

    # (c) HONEST BASELINE: genuine timestamps must be fresh.
    fc = evaluate_freshness(record_timestamp_utc=genuine_ts,
                            nist_pulse_time=nist_pulse_time,
                            precommit_time_utc=precommit_time)
    c_fresh = fc["fresh"] is True

    sub = {
        "a_backdate": {"forged_timestamp_utc": backdated_ts, "freshness": fa,
                       "attack_detected": a_detected},
        "b_precompute": {"forged_precommit_time_utc": precompute_pre, "freshness": fb,
                         "attack_detected": b_detected},
        "c_honest_baseline": {"freshness": fc, "fresh": c_fresh},
    }
    all_pass = a_detected and b_detected and c_fresh
    verdict = "PASS" if all_pass else "FAIL"
    doc = {"case": "W4-C3",
           "description": "Backdating / pre-computation detection via independent freshness-bracket re-evaluation",
           "verdict": verdict,
           "honesty_note": (
               "Establishes a NOT-BEFORE lower time bound and design-before-anchor ordering "
               "only. No upper time bound is claimed (a record can always be finalized later). "
               "This is a relative-ordering proof rooted in NIST pulse forward-unpredictability, "
               "NOT a trusted timestamping/notarization authority."),
           "sub_cases": sub}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W4-C3-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
