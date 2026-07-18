# WITNESS-1 Preregistration
## Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Series:** WITNESS (first record)
**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Preregistration lock date:** 2026-07-18 (UTC)
**Status:** PREREGISTERED — locked before execution

---

## 1. Claim (single, falsifiable)

A ProofRecord whose challenge nonce is derived from measured QPU output, with the IBM
job ID and raw counts embedded, can be:

(a) verified end-to-end against the provider's job record, and
(b) detected as forged when the nonce, job ID, or counts are substituted —

under the tested construction.

---

## 2. Non-Claims (explicit)

- Does NOT prove quantum randomness superiority over CSPRNG. No Bell test is performed;
  device bias is present and acknowledged.
- Does NOT prove universal security. Results apply only within the tested construction,
  circuit model, backend, qubits, calibration snapshot, shot count, and software harness.
- Does NOT constitute a production certification or cryptographic security proof.

---

## 3. Circuit Specification

- **Qubits:** 8
- **Circuit:** Hadamard on all 8 qubits, measure all — one circuit only.
- **Shots:** 4,000, one job submission.
- **Backend selection:** Least-busy available IBM Quantum backend at submission time.
  Backend name, calibration snapshot, timestamp, and job ID recorded in results/raw/.
- **QPU time budget:** Estimated seconds. Account must have sufficient remaining time
  (~2 minutes minimum). If insufficient time remains, STOP — do not purchase time.

---

## 4. Nonce Construction

```
nonce = SHA-256(
    canonical_json(raw_counts) || job_id || canonical_json(calibration_snapshot)
)
```

- **Canonical JSON:** sorted keys, no whitespace, UTF-8 encoding.
- **Concatenation:** byte-level, no separator between fields.

**ProofRecord structure:**
```json
{
  "nonce":              "<hex string, 64 chars>",
  "job_id":             "<IBM Quantum job ID string>",
  "backend":            "<backend name string>",
  "calibration_hash":   "<SHA-256 hex of canonical_json(calibration_snapshot)>",
  "timestamp_utc":      "<ISO-8601 UTC string>",
  "raw_counts_hash":    "<SHA-256 hex of canonical_json(raw_counts)>",
  "context_id":         "<string — execution context identifier>"
}
```

---

## 5. Preregistered Test Cases & Pass/Fail Criteria

### W1-C1 — Honest Verification

**Procedure:** Recompute the nonce from stored raw counts + job ID + calibration
snapshot. Verify the recomputed nonce matches the ProofRecord nonce exactly.
Independently confirm job ID and counts against the IBM provider job record via API.

**PASS criterion:** Recomputed nonce matches; provider job record confirms job ID and
raw counts match stored values. Verification succeeds end-to-end.

**Expected outcome:** PASS.

---

### W1-C2 — Substitution / Tamper Detection

**Procedure:** Three independent sub-trials, each altering exactly one field:

- (a) Substitute raw_counts with a different valid-format counts dict; rerun verification.
- (b) Substitute job_id with a different string; rerun verification.
- (c) Substitute calibration_snapshot with a different valid-format dict; rerun verification.

**PASS criterion:** ALL THREE substitutions are detected as forged (nonce mismatch
reported for each). No substitution passes verification.

**Expected outcome:** PASS (all three tamper attempts detected).

---

### W1-C3 — Cross-Context Replay

**Procedure:** Present the valid nonce/ProofRecord (from W1-C1) to a second
authorization context with a different `context_id`. Use the ARK-457 replay-protection
logic (imported as a library module — `src/ark457_replay.py`) to evaluate the replay.

**PASS criterion:** The replay is DENIED by the replay-protection logic (context_id
mismatch detected). The original context_id is accepted; the replay context is rejected.

**Expected outcome:** DENY (PASS).

---

## 6. Overall Verdict Rule

PASS iff all three cases meet their stated criteria.

Any single case failing its criterion = overall FAIL, published as-is with full
root-cause analysis. A follow-up record (WITNESS-1b) may be registered if warranted.

---

## 7. Related Works

- ARK Corpus (ExecutionProof series): concept DOI 10.5281/zenodo.21398675
  (19 records, 17 experiment IDs, 16 PASS / 2 FAIL / 1 gate-stop)
- ARK-457 (cross-context replay, most directly related):
  DOI 10.5281/zenodo.21421742 — replay-protection logic used here as library.
- WITNESS-1 is an independent record in a new WITNESS series; it is not a fork
  of executionproof-testbeds or uip-phase1-testbeds.

---

## 8. Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, and stated experimental conditions. This is an experimental
> evidence record, not a universal security proof or production certification."

This disclaimer is reproduced verbatim in the README and Zenodo deposit description.

---

## 9. MANIFEST Lock Reference

`MANIFEST.sha256` covers this preregistration document and all files under `src/`.
It is committed before any QPU job is submitted. Post-lock code changes are prohibited;
any pre-execution harness defect triggers gate-stop protocol.

---

*Remnant Fieldworks RF Process. Preregistration-first. No post-hoc changes.*
