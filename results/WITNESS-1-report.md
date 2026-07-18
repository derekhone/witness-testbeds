# WITNESS-1 Results Report
## Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Series:** WITNESS (first record)
**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Execution date:** 2026-07-18 (UTC)
**Overall verdict:** ✅ PASS

---

## Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, and stated experimental conditions. This is an experimental
> evidence record, not a universal security proof or production certification."

---

## Harness Fix Disclosure (pre-execution, mandatory per RF protocol)

Two corrections were made to the harness before execution. Neither touches the circuit,
procedure, criteria, thresholds, or oracle:

1. **Channel name:** `ibm_quantum` → `ibm_quantum_platform` (API string changed in
   qiskit-ibm-runtime 0.48.0; old string rejected at connection time).
2. **Execution mode:** `Session` → `Batch` (Session not available on the open plan;
   Batch produces identical circuit execution semantics for single-job submissions).

These fixes are disclosed here and in `results/raw/job_meta.json`. The MANIFEST.sha256
covers the pre-fix code; the corrected files are committed on the results branch with
this disclosure note. The preregistered procedure, criteria, and verdict rules are
unchanged.

---

## QPU Execution Record

| Field | Value |
|-------|-------|
| Backend | ibm_fez (156-qubit Heron r2) |
| Job ID | d9dgp6kjeosc73fhigsg |
| Shots | 4,000 |
| Unique outcomes | 256 (all 2⁸ = 256 bitstrings observed) |
| Submission timestamp (UTC) | 2026-07-18T05:17:54.918200+00:00 |
| Qubits | 8, Hadamard on all, measure all |

---

## ProofRecord

```json
{
  "schema": "witness.proofrecord/v1",
  "nonce": "2a06cecc238ddcf1e8c2774df2074d9bd3d3fdbc7b1a3e6436281648aadad0ec",
  "job_id": "d9dgp6kjeosc73fhigsg",
  "backend": "ibm_fez",
  "calibration_hash": "b46857638b0c70526263589cf7d372a62c59ad9df8eac95c54cc68bf097bab0e",
  "timestamp_utc": "2026-07-18T05:17:54.918200+00:00",
  "raw_counts_hash": "09ec92f3c38a0ec59f30d95cefc7409736d4ccf919686bbc4c7cfa4cad165e71",
  "context_id": "witness-1-primary"
}
```

---

## Case Results

### W1-C1 — Honest Verification

**Verdict: ✅ PASS**

**Procedure:** Recomputed nonce from stored raw counts + job ID + calibration snapshot;
verified against ProofRecord nonce. Independently confirmed job ID and counts against
the IBM Quantum provider API.

| Check | Result |
|-------|--------|
| nonce_match | True |
| counts_hash_match | True |
| cal_hash_match | True |
| jobid_match | True |
| provider job_found | True |
| provider counts_match | True |

Verification succeeded end-to-end. Meets PASS criterion.

---

### W1-C2 — Substitution / Tamper Detection

**Verdict: ✅ PASS**

**Procedure:** Three independent sub-trials, one field substituted each time.

| Sub-trial | Substitution | Forgery detected | Sub-verdict |
|-----------|-------------|-----------------|-------------|
| (a) | raw_counts altered | True (nonce_match=False) | PASS |
| (b) | job_id altered | True (nonce_match=False) | PASS |
| (c) | calibration_snapshot altered | True (nonce_match=False) | PASS |

All three substitutions detected as forged. Meets PASS criterion.

---

### W1-C3 — Cross-Context Replay

**Verdict: ✅ PASS**

**Procedure:** Presented valid ProofRecord (context_id="witness-1-primary") to a second
authorization context (context_id="witness-1-replay-context") using the ARK-457
replay-protection logic (5-dimensional context tuple, exact match required).

| Check | Result |
|-------|--------|
| Original context decision | ALLOW |
| Replay context decision | DENY |
| Mismatched dimension(s) | session |

Replay denied. Meets PASS criterion (DENY = PASS per preregistration).

---

## Overall Verdict: ✅ PASS

All three cases met their preregistered criteria. No deviations from the preregistered
procedure, criteria, or thresholds.

---

## What This Establishes (and Does Not)

**Established within the tested construction:**
- A ProofRecord nonce derived from QPU output (raw counts + job ID + calibration
  snapshot) can be recomputed and verified end-to-end against the provider's job record.
- Substitution of any single input field (counts, job ID, calibration) is detected as
  forgery under this construction.
- The ARK-457 replay-protection logic correctly denies a ProofRecord presented in a
  different authorization context.

**Not established:**
- Quantum randomness superiority over CSPRNG (no Bell test; device bias present).
- Universal security. Results are specific to this circuit, backend (ibm_fez), 8 qubits,
  4,000 shots, calibration snapshot at execution time, and software harness.
- Production certification or cryptographic security guarantee.

---

## Raw Artifact Hashes

| Artifact | SHA-256 |
|----------|---------|
| results/raw/raw_counts.json | 09ec92f3c38a0ec59f30d95cefc7409736d4ccf919686bbc4c7cfa4cad165e71 (raw_counts_hash field) |
| results/raw/calibration.json | b46857638b0c70526263589cf7d372a62c59ad9df8eac95c54cc68bf097bab0e (calibration_hash field) |
| results/proofrecord.json | see nonce field above |

---

## Related Works

- ARK Corpus (ExecutionProof series): https://doi.org/10.5281/zenodo.21398675
  (19 records / 17 IDs / 16 PASS / 2 FAIL / 1 gate-stop)
- ARK-457 (replay logic used in W1-C3): https://doi.org/10.5281/zenodo.21421742

---

*Remnant Fieldworks RF Process. Preregistration-first. Results published as-is.*
*Zenodo DOI: [placeholder — to be populated after Derek publishes the draft deposit]*
