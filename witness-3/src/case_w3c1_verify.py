"""
W3-C1: Honest end-to-end verification of the Cosmic Beacon ProofRecord.

Recomputes the fused cosmic_nonce from all three stored witnesses, verifies the
record_hash and every per-witness hash, re-derives the CHSH S from stored counts, and
(when the provider API is reachable) confirms the QPU job and counts against IBM's record.

PASS criterion: all local recomputation checks True AND provider job_found=True AND
provider counts_match=True. Provider API unavailability -> GATE-STOP (not FAIL).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce_v3 import (compute_raw_counts_hash, compute_calibration_hash,
                      compute_nist_hash, compute_astro_hash)
from proofrecord_v3 import verify_record_hash, verify_cosmic_nonce
from chsh import compute_chsh

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"


def _load(p):
    with open(p) as f:
        return json.load(f)


def main():
    raw_counts = _load(RAW_DIR / "raw_counts.json")            # counts_by_setting
    cal = _load(RAW_DIR / "calibration_snapshot.json")
    nist = _load(RAW_DIR / "nist_witness.json")
    astro = _load(RAW_DIR / "astro_witness.json")
    pr = _load(RESULTS_DIR / "proofrecord.json")

    recomputed = compute_chsh(raw_counts)

    checks = {
        "record_hash_match":      verify_record_hash(pr),
        "cosmic_nonce_match":     verify_cosmic_nonce(pr, raw_counts, cal, nist, astro),
        "raw_counts_hash_match":  compute_raw_counts_hash(raw_counts) == pr["raw_counts_hash"],
        "cal_hash_match":         compute_calibration_hash(cal) == pr["calibration_hash"],
        "nist_hash_match":        compute_nist_hash(nist) == pr["nist_hash"],
        "astro_hash_match":       compute_astro_hash(astro) == pr["astro_hash"],
        "chsh_S_reproducible":    abs(recomputed["S"] - pr["chsh"]["S"]) < 1e-9,
        "schema_version_match":   pr.get("schema_version") == "witness-proofrecord-3.0",
        "context_id_present":     bool(pr.get("context_id")),
        "provider_instance_present": bool(pr.get("provider_instance")),
        "nist_witness_present":   bool(nist.get("pulseIndex") is not None),
        "astro_witness_present":  bool(astro.get("file_sha256")),
    }

    # Provider verification (GATE-STOP on network/provider unavailability)
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        with open(Path.home() / ".config" / "abacusai_auth_secrets.json") as f:
            d = json.load(f)
        token = None
        for slot in ['ibm quantum', 'ibm_quantum', 'ibm', 'witness1_ibmq']:
            v = d.get(slot, {}).get('secrets', {}).get('api_token', {}).get('value', '')
            if v:
                token = v
                break
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        job = service.job(pr["job_id"])
        res = job.result()
        # Recover per-setting provider counts and compare to stored (order-independent).
        prov_ok = True
        # Stored raw_counts is keyed by setting label; provider returns per-circuit results.
        # We compare the multiset of counts dicts.
        stored_sets = sorted([json.dumps(v, sort_keys=True) for v in raw_counts.values()])
        provider_sets = []
        for i in range(len(res)):
            c = res[i].data.c.get_counts() if hasattr(res[i].data, "c") else res[i].data.meas.get_counts()
            c = {k.replace(" ", ""): int(v) for k, v in c.items()}
            provider_sets.append(json.dumps(c, sort_keys=True))
        provider_sets = sorted(provider_sets)
        checks["provider_job_found"] = True
        checks["provider_counts_match"] = (stored_sets == provider_sets)
        checks["provenance_note"] = (
            "Confirms: stored job_id and per-setting counts match IBM provider API record "
            "at verification time. Does not confirm physical origin or quality of QPU randomness."
        )
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ['network', 'timeout', 'connect', 'unavailable',
                                  '503', '502', '500', 'disabled', 'token', 'unauthor']):
            doc = {"case": "W3-C1", "verdict": "GATE-STOP",
                   "reason": f"Provider API unavailable/unauthorized: {e}", "checks": checks}
            print(json.dumps(doc, indent=2))
            with open(RESULTS_DIR / "W3-C1-result.json", 'w') as f:
                json.dump(doc, f, indent=2)
            sys.exit(2)
        checks["provider_job_found"] = False
        checks["provider_counts_match"] = False
        checks["provider_error"] = str(e)

    skip = {"provenance_note", "provider_error"}
    all_pass = all(v is True for k, v in checks.items() if k not in skip)
    verdict = "PASS" if all_pass else "FAIL"
    doc = {"case": "W3-C1",
           "description": "Honest end-to-end verification of fused Cosmic Beacon ProofRecord",
           "verdict": verdict, "checks": checks}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W3-C1-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
