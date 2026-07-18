"""
WITNESS-4 zero-trust reconstruction.

Recomputes the entire ProofRecord (fused nonce, every per-witness hash, freshness bracket,
and record_hash) from the stored public artifacts ALONE — with no trust in any RF-private
state. Every input is a publicly re-fetchable object:

  - raw_counts.json          -> also retrievable from the IBM provider by job_id
  - calibration_snapshot.json-> derived from the IBM backend properties at run time
  - nist_witness.json        -> re-fetchable from the NIST beacon archive by pulseIndex
  - astro_witness.json       -> byte-exact SHA-256 of a fixed public LIGO/GWOSC file
  - precommit.json           -> the pre-commitment document (published in the ledger)

This module is the machine embodiment of Prospect Question #5: "Can an independent
reviewer reconstruct the decision from the ProofRecord?" It answers yes — deterministically
and offline — using only artifacts anyone can obtain from the original public sources.
"""

import json
from pathlib import Path

try:
    from .nonce_v4 import (compute_fused_nonce, compute_raw_counts_hash,
                           compute_calibration_hash, compute_nist_hash, compute_astro_hash)
    from .proofrecord_v4 import build_proofrecord, verify_record_hash, verify_fused_nonce
    from .precommit import compute_precommit_hash
    from .chsh import compute_chsh
except ImportError:
    from nonce_v4 import (compute_fused_nonce, compute_raw_counts_hash,
                          compute_calibration_hash, compute_nist_hash, compute_astro_hash)
    from proofrecord_v4 import build_proofrecord, verify_record_hash, verify_fused_nonce
    from precommit import compute_precommit_hash
    from chsh import compute_chsh


def _load(p):
    with open(p) as f:
        return json.load(f)


def reconstruct_from_artifacts(results_dir: Path) -> dict:
    """
    Deterministically recompute all derived values from the stored public artifacts and
    compare against the stored ProofRecord. Returns a dict with recomputed values and a
    `checks` block of booleans (True == reconstruction matches the published record).
    """
    results_dir = Path(results_dir)
    raw_dir = results_dir / "raw"

    raw_counts = _load(raw_dir / "raw_counts.json")
    cal = _load(raw_dir / "calibration_snapshot.json")
    nist = _load(raw_dir / "nist_witness.json")
    astro = _load(raw_dir / "astro_witness.json")
    precommit = _load(raw_dir / "precommit.json")
    pr = _load(results_dir / "proofrecord.json")

    precommit_hash = compute_precommit_hash(precommit)
    fused = compute_fused_nonce(
        precommit_hash, pr["prev_record_hash"], raw_counts, pr["job_id"], cal, nist, astro,
    )
    chsh = compute_chsh(raw_counts)

    checks = {
        "precommit_hash_match": precommit_hash == pr["precommit_hash"],
        "fused_nonce_match": fused == pr["fused_nonce"],
        "fused_nonce_verify": verify_fused_nonce(pr, raw_counts, cal, nist, astro),
        "raw_counts_hash_match": compute_raw_counts_hash(raw_counts) == pr["raw_counts_hash"],
        "cal_hash_match": compute_calibration_hash(cal) == pr["calibration_hash"],
        "nist_hash_match": compute_nist_hash(nist) == pr["nist_hash"],
        "astro_hash_match": compute_astro_hash(astro) == pr["astro_hash"],
        "record_hash_match": verify_record_hash(pr),
        "chsh_S_reproducible": abs(chsh["S"] - pr["chsh"]["S"]) < 1e-9,
        "nist_pulse_time_match": nist.get("timeStamp") == pr.get("nist_pulse_time"),
        "precommit_prev_link_match": precommit.get("prev_record_hash") == pr.get("prev_record_hash"),
    }
    checks["all_reconstructed"] = all(checks.values())
    return {
        "recomputed_precommit_hash": precommit_hash,
        "recomputed_fused_nonce": fused,
        "recomputed_chsh_S": chsh["S"],
        "checks": checks,
    }


if __name__ == "__main__":
    out = reconstruct_from_artifacts(Path(__file__).parent.parent / "results")
    print(json.dumps(out, indent=2))
