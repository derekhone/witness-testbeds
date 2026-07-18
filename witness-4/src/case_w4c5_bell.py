"""
W4-C5: CHSH Bell-inequality violation certification (device-dependent).

Identical criterion to WITNESS-3 W3-C4, carried forward so WITNESS-4's quantum anchor is
certified under the same preregistered, honest standard.

Preregistered PASS criterion (ALL must hold):
  1. abs(S) > 2                        (a Bell-inequality violation is present)
  2. (abs(S) - 2) / sigma_S >= 5.0     (>= 5 sigma; statistically decisive)
  3. abs(S) <= 2*sqrt(2) + 0.10        (physical sanity; at/under Tsirelson within tolerance)

KILL condition: abs(S) <= 2 -> W4-C5 = FAIL, bell_certified = False, published as-is. The
fused nonce and the freshness bracket remain valid as provenance/freshness/ordering
constructions regardless; only the device-dependent non-classicality flag fails.

SCOPE (preregistered Non-Claim): a PASS certifies a violation on THIS backend/circuit/
qubit-pair/calibration/shots under fair-sampling and no-signalling assumptions. NOT a
loophole-free / device-independent certification.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chsh import compute_chsh, CLASSICAL_BOUND, TSIRELSON_BOUND

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"
SIGMA_THRESHOLD = 5.0
TSIRELSON_TOLERANCE = 0.10


def main():
    with open(RAW_DIR / "raw_counts.json") as f:
        counts_by_setting = json.load(f)

    result = compute_chsh(counts_by_setting)
    abs_S = result["abs_S"]
    sigmas = result["sigmas_above_classical"]

    c1 = abs_S > CLASSICAL_BOUND
    c2 = sigmas >= SIGMA_THRESHOLD
    c3 = abs_S <= (TSIRELSON_BOUND + TSIRELSON_TOLERANCE)
    bell_certified = bool(c1 and c2 and c3)
    verdict = "PASS" if bell_certified else "FAIL"

    doc = {"case": "W4-C5",
           "description": "CHSH Bell-inequality violation certification (device-dependent)",
           "verdict": verdict, "bell_certified": bell_certified,
           "criteria": {"c1_violation_over_2": c1, "c2_at_least_5_sigma": c2,
                        "c3_within_tsirelson_tolerance": c3,
                        "sigma_threshold": SIGMA_THRESHOLD,
                        "tsirelson_tolerance": TSIRELSON_TOLERANCE},
           "chsh": {"S": result["S"], "abs_S": abs_S, "sigma_S": result["sigma_S"],
                    "sigmas_above_classical": sigmas, "classical_bound": CLASSICAL_BOUND,
                    "tsirelson_bound": TSIRELSON_BOUND, "correlators": result["correlators"],
                    "per_setting": result["per_setting"]},
           "scope_note": (
               "Certifies a Bell-inequality violation on the tested backend/circuit/qubits/"
               "calibration/shots under fair-sampling and no-signalling assumptions. NOT a "
               "loophole-free or device-independent certification.")}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W4-C5-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
