"""
W2-C1: Honest end-to-end verification.

PASS criterion: all local recomputation checks True AND
                provider job_found=True AND provider counts_match=True.

Provenance note: confirms provider-record provenance only.
  "Stored job_id and counts match IBM provider API record at verification time.
   Does not confirm physical origin or quality of QPU randomness."

Provider API unavailability -> GATE-STOP, not FAIL.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce import compute_raw_counts_hash, compute_calibration_hash
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

    checks = {
        "record_hash_match":          verify_record_hash(pr),
        "quantum_nonce_match":        verify_quantum_nonce(pr, raw_counts, cal),
        "raw_counts_hash_match":      compute_raw_counts_hash(raw_counts) == pr["raw_counts_hash"],
        "cal_hash_match":             compute_calibration_hash(cal) == pr["calibration_hash"],
        "schema_version_match":       pr.get("schema_version") == "witness-proofrecord-1.0",
        "context_id_present":         bool(pr.get("context_id")),
        "provider_instance_present":  bool(pr.get("provider_instance")),
    }

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        with open(Path.home() / ".config" / "abacusai_auth_secrets.json") as f:
            d = json.load(f)
        token = None
        for slot in ['witness1_ibmq', 'ibm_quantum', 'ibm']:
            v = d.get(slot, {}).get('secrets', {}).get('api_token', {}).get('value', '')
            if v:
                token = v
                break
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        job = service.job(pr["job_id"])
        provider_counts_raw = job.result()[0].data.meas.get_counts()
        provider_counts = {k.replace(' ', ''): int(v) for k, v in provider_counts_raw.items()}
        checks["provider_job_found"]    = True
        checks["provider_counts_match"] = provider_counts == raw_counts
        checks["provenance_note"] = (
            "Confirms: stored job_id and counts match IBM provider API record at verification time. "
            "Does not confirm physical origin or quality of QPU randomness."
        )
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ['network', 'timeout', 'connect', 'unavailable', '503', '502', '500']):
            doc = {"verdict": "GATE-STOP", "reason": f"Provider API unavailable: {e}", "checks": checks}
            print(json.dumps(doc, indent=2))
            with open(RESULTS_DIR / "W2-C1-result.json", 'w') as f:
                json.dump(doc, f, indent=2)
            sys.exit(2)
        checks["provider_job_found"]    = False
        checks["provider_counts_match"] = False
        checks["provider_error"]        = str(e)

    skip_keys = {"provenance_note", "provider_error"}
    all_pass = all(v is True for k, v in checks.items() if k not in skip_keys)
    verdict = "PASS" if all_pass else "FAIL"

    doc = {
        "case": "W2-C1",
        "description": "Honest end-to-end verification (provider-record provenance)",
        "verdict": verdict,
        "checks": checks,
    }
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W2-C1-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
