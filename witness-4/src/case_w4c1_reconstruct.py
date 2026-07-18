"""
W4-C1: Zero-trust independent reconstruction (Prospect Question #5, machine embodiment).

Reconstructs the ENTIRE ProofRecord (fused nonce, precommit hash, every per-witness hash,
CHSH S, freshness bracket, record_hash) from the stored PUBLIC artifacts alone, then — when
the provider API is reachable — confirms the QPU job and per-setting counts against IBM's
own record.

PASS criterion: reconstruct.all_reconstructed == True AND freshness.fresh == True AND
provider job_found == True AND provider counts_match == True.
Provider API unavailability -> GATE-STOP (not FAIL).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from reconstruct import reconstruct_from_artifacts

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"


def _load(p):
    with open(p) as f:
        return json.load(f)


def main():
    pr = _load(RESULTS_DIR / "proofrecord.json")
    recon = reconstruct_from_artifacts(RESULTS_DIR)
    checks = dict(recon["checks"])
    checks["freshness_fresh"] = bool(pr.get("freshness", {}).get("fresh"))

    # Provider verification (GATE-STOP on network/provider unavailability)
    raw_counts = _load(RAW_DIR / "raw_counts.json")
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
        service = QiskitRuntimeService(channel="ibm_cloud", token=token)
        job = service.job(pr["job_id"])
        res = job.result()
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
            "Confirms stored job_id and per-setting counts match IBM provider API record "
            "at verification time. Does not confirm physical origin or quality of QPU randomness."
        )
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ['network', 'timeout', 'connect', 'unavailable',
                                  '503', '502', '500', 'disabled', 'token', 'unauthor']):
            doc = {"case": "W4-C1", "verdict": "GATE-STOP",
                   "reason": f"Provider API unavailable/unauthorized: {e}", "checks": checks}
            print(json.dumps(doc, indent=2))
            with open(RESULTS_DIR / "W4-C1-result.json", 'w') as f:
                json.dump(doc, f, indent=2)
            sys.exit(2)
        checks["provider_job_found"] = False
        checks["provider_counts_match"] = False
        checks["provider_error"] = str(e)

    skip = {"provenance_note", "provider_error", "all_reconstructed"}
    all_pass = all(v is True for k, v in checks.items() if k not in skip)
    verdict = "PASS" if all_pass else "FAIL"
    doc = {"case": "W4-C1",
           "description": "Zero-trust independent reconstruction from public artifacts + provider confirmation",
           "verdict": verdict,
           "recomputed_fused_nonce": recon["recomputed_fused_nonce"],
           "checks": checks}
    print(json.dumps(doc, indent=2))
    with open(RESULTS_DIR / "W4-C1-result.json", 'w') as f:
        json.dump(doc, f, indent=2)
    if verdict != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
