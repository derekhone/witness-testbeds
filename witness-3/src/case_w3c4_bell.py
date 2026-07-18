"""
W3-C4: CHSH Bell-inequality violation certification (the flagship scientific case).

Computes the CHSH statistic S from the stored per-setting QPU counts and applies the
preregistered certification criterion.

Preregistered PASS criterion (ALL must hold):
  1. abs(S) > 2                                  (a Bell-inequality violation is present)
  2. (abs(S) - 2) / sigma_S >= 5.0               (violation is >= 5 standard deviations,
                                                  i.e. statistically decisive, not noise)
  3. abs(S) <= 2*sqrt(2) + 0.10                  (physical sanity: at/under Tsirelson bound
                                                  within tolerance; a value far above would
                                                  indicate a statistics/harness error)

Preregistered KILL condition: if abs(S) <= 2 the run shows NO violation -> W3-C4 = FAIL,
bell_certified = False, published as-is. The fused nonce is still valid as a
provenance/freshness construction; only the device-dependent non-classicality
certification fails.

SCOPE (preregistered Non-Claim): a PASS certifies a Bell-inequality violation on THIS
backend, circuit, qubit pair, calibration, and shot count, under fair-sampling and
no-signalling assumptions. It is NOT a loophole-free / device-independent certification
(locality, detection, and freedom-of-choice loopholes remain open — the qubits are
neighbouring transmons on one chip).
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
    S = result["S"]
    abs_S = result["abs_S"]
    sigma_S = result["sigma_S"]
    sigmas = result["sigmas_above_classical"]

    c1_violation = abs_S > CLASSICAL_BOUND
    c2_significant = sigmas >= SIGMA_THRESHOLD
    c3_physical = abs_S <= (TSIRELSON_BOUND + TSIRELSON_TOLERANCE)

    bell_certified = bool(c1_violation and c2_significant and c3_physical)
    verdict = "PASS" if bell_certified else "FAIL"

    doc = {
        "case": "W3-C4",
        "description": "CHSH Bell-inequality violation certification (device-dependent)",
        "verdict": verdict,
        "bell_certified": bell_certified,
        "criteria": {
            "c1_violation_over_2": c1_violation,
            "c2_at_least_5_sigma": c2_significant,
            "c3_within_tsirelson_tolerance": c3_physical,
            "sigma_threshold": SIGMA_THRESHOLD,
            "tsirelson_tolerance": TSIRELSON_TOLERANCE,
        },
        "chsh": {
            "S": S,
            "abs_S": abs_S,
            "sigma_S": sigma_S,
            "sigmas_above_classical": sigmas,
            "classical_bound": CLASSICAL_BOUND,
            "tsirelson_bound": TSIRELSON_BOUND,
            "correlators": result["correlators"],
            "per_setting": result["per_setting"],
        },
        "scope_note": (
            "Certifies a Bell-inequality violation on the tested backend/circuit/qubits/"
            "calibration/shots under fair-sampling and no-signalling assumptions. NOT a "
            "loophole-free or device-independent certification."
        ),
    }
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W3-C4-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
