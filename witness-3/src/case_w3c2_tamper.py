"""
W3-C2: Substitution / tamper detection across ALL THREE witnesses (6 sub-trials).

Each sub-trial alters exactly one element and confirms the forgery is detected by the
appropriate layer (fused cosmic_nonce and/or record_hash).

  (a) raw_counts    : swap two count values in one setting  -> cosmic_nonce mismatch
  (b) job_id        : append "_FORGED"                       -> cosmic_nonce AND record_hash
  (c) calibration   : flip one readout_error value           -> cosmic_nonce mismatch
  (d) nist witness  : alter beacon outputValue               -> cosmic_nonce mismatch
  (e) astro witness : alter file_sha256                      -> cosmic_nonce mismatch
  (f) context_id    : alter WITHOUT recomputing record_hash  -> record_hash mismatch

Overall PASS: all 6 sub-trials detect the forgery.
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proofrecord_v3 import verify_record_hash, verify_cosmic_nonce

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"


def _load(p):
    with open(p) as f:
        return json.load(f)


def main():
    raw_counts = _load(RAW_DIR / "raw_counts.json")
    cal = _load(RAW_DIR / "calibration_snapshot.json")
    nist = _load(RAW_DIR / "nist_witness.json")
    astro = _load(RAW_DIR / "astro_witness.json")
    pr = _load(RESULTS_DIR / "proofrecord.json")

    sub = {}

    # (a) raw_counts tamper -> nonce must fail
    rc = copy.deepcopy(raw_counts)
    first_setting = sorted(rc.keys())[0]
    ks = sorted(rc[first_setting].keys())
    if len(ks) >= 2:
        rc[first_setting][ks[0]], rc[first_setting][ks[1]] = (
            rc[first_setting][ks[1]], rc[first_setting][ks[0]])
    else:
        rc[first_setting][ks[0]] += 1
    sub["a_raw_counts"] = {
        "altered": "raw_counts (swap two counts)",
        "forgery_detected": not verify_cosmic_nonce(pr, rc, cal, nist, astro),
    }

    # (b) job_id tamper -> nonce and record_hash must fail
    pr_b = copy.deepcopy(pr)
    pr_b["job_id"] = pr_b["job_id"] + "_FORGED"
    sub["b_job_id"] = {
        "altered": "job_id (append _FORGED)",
        "nonce_detected": not verify_cosmic_nonce(pr_b, raw_counts, cal, nist, astro),
        "record_hash_detected": not verify_record_hash(pr_b),
    }
    sub["b_job_id"]["forgery_detected"] = (
        sub["b_job_id"]["nonce_detected"] and sub["b_job_id"]["record_hash_detected"])

    # (c) calibration tamper -> nonce must fail
    cal_c = copy.deepcopy(cal)
    ro = cal_c.get("readout_error_by_qubit", {})
    if ro:
        k0 = sorted(ro.keys())[0]
        ro[k0] = (ro[k0] + 0.01) if isinstance(ro[k0], (int, float)) else 0.5
    else:
        cal_c["backend_name"] = str(cal_c.get("backend_name")) + "_X"
    sub["c_calibration"] = {
        "altered": "calibration_snapshot (flip one readout_error)",
        "forgery_detected": not verify_cosmic_nonce(pr, raw_counts, cal_c, nist, astro),
    }

    # (d) NIST witness tamper -> nonce must fail
    nist_d = copy.deepcopy(nist)
    ov = nist_d.get("outputValue") or "0"
    nist_d["outputValue"] = ("F" + ov[1:]) if ov[0] != "F" else ("0" + ov[1:])
    sub["d_nist"] = {
        "altered": "nist_witness (alter outputValue)",
        "forgery_detected": not verify_cosmic_nonce(pr, raw_counts, cal, nist_d, astro),
    }

    # (e) astro witness tamper -> nonce must fail
    astro_e = copy.deepcopy(astro)
    fh = astro_e.get("file_sha256") or "0"
    astro_e["file_sha256"] = ("f" + fh[1:]) if fh[0] != "f" else ("0" + fh[1:])
    sub["e_astro"] = {
        "altered": "astro_witness (alter file_sha256)",
        "forgery_detected": not verify_cosmic_nonce(pr, raw_counts, cal, nist, astro_e),
    }

    # (f) context_id tamper WITHOUT recomputing record_hash -> record_hash must fail
    pr_f = copy.deepcopy(pr)
    pr_f["context_id"] = str(pr_f.get("context_id")) + "_FORGED"
    sub["f_context_id"] = {
        "altered": "context_id (record_hash NOT recomputed)",
        "forgery_detected": not verify_record_hash(pr_f),
    }

    all_pass = all(v["forgery_detected"] for v in sub.values())
    verdict = "PASS" if all_pass else "FAIL"
    doc = {"case": "W3-C2",
           "description": "Tamper detection across QPU, NIST, and astro witnesses (6 sub-trials)",
           "verdict": verdict, "sub_trials": sub}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W3-C2-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
