# WITNESS-2 Results Report

**Series:** WITNESS (Quantum-Nonce Authorization Provenance Study)  
**Experiment ID:** WITNESS-2  
**Institution:** Remnant Fieldworks Inc.  
**PI:** Derek Adam Hone  
**Date of QPU Execution:** 2026-07-18  
**Preregistration DOI:** (Zenodo deposit pending — see WITNESS-2 deposit)  
**WITNESS Series Concept DOI:** 10.5281/zenodo.21424323  
**WITNESS-1 Reference DOI:** 10.5281/zenodo.21424324  

---

## 1. Executive Summary

WITNESS-2 demonstrates that a quantum-sourced nonce bound to a specific execution context via the ARK-457 five-dimensional authorization boundary can withstand: (a) honest end-to-end verification against the IBM provider record, (b) substitution / tamper detection across four distinct forgery patterns, and (c) cross-context replay rejection through both record-hash integrity and ARK-457 context binding.

All three preregistered cases **PASS**. The experiment ran on **ibm_fez** (IBM Quantum, open plan) using 4000 shots across 8 qubits, producing 256 unique measurement outcomes — covering the full 2⁸ = 256 computational basis states — consistent with a uniform superposition.

Two pre-execution harness fixes (FIX-1, FIX-2) were applied and disclosed before QPU submission, consistent with the ARK-451 / WITNESS-1 harness-fix precedent. Neither fix touched circuit logic, shot count, case definitions, criteria, or the decision procedure.

---

## 2. Preregistration

| Item | Detail |
|------|--------|
| Preregistration document | `witness-2/prereg/WITNESS-2-prereg.md` |
| MANIFEST lock | `witness-2/MANIFEST.sha256` |
| Preregistration format | Markdown + PDF + DOCX |
| Schema version | `witness-proofrecord-1.0` |
| Context ID | `witness-2-primary` |
| Nonce construction | Length-prefixed (LP) SHA-256, v2 |
| CP1 PR | #3 (merged SHA c2d9b3b before QPU submission) |
| FIX-1 commit | 8ae73bf (service.least\_busy → min(pending\_jobs)) |
| FIX-2 commit | 2b6cbc5 (ISA transpilation via qiskit.transpile) |

---

## 3. Harness Fixes (Disclosed, Pre-Execution)

**FIX-1 (commit 8ae73bf):**  
`service.least_busy(backend_list)` raises `TypeError` in qiskit-ibm-runtime 0.48.0 when the internal `qubits` field is a list not an int. Fixed by replacing with `min(eligible, key=lambda b: b.status().pending_jobs)`. Fix does NOT touch circuit, shots, cases, criteria, or decision procedure. MANIFEST.sha256 recomputed and recommitted.

**FIX-2 (commit 2b6cbc5):**  
IBM Quantum API rejects non-ISA circuits as of March 2024. The H gate is not native to ibm\_fez's gate set. Added `transpile(qc, backend=backend, optimization_level=1)` before submission. Logical circuit (uniform 8-qubit H + measure\_all) is unchanged — only gate representation (H → RZ/SX) differs. MANIFEST.sha256 recomputed and recommitted.

Both fixes consistent with ARK-451 / WITNESS-1 harness-fix precedent.

---

## 4. QPU Execution

| Parameter | Value |
|-----------|-------|
| Job ID | `d9di7nkinv1c73ap4ed0` |
| Backend | `ibm_fez` |
| Provider instance | `crn:v1:bluemix:public:quantum-computing:us-east:a/074ad0b4119241ee8fd51258f35aa4a6:97957880-e0cc-4c0e-a07e-f9b8f2da3be4::` |
| Channel | `ibm_quantum_platform` |
| Execution mode | `Batch` |
| Qubits | 8 |
| Shots | 4000 |
| Unique outcomes | 256 (= 2⁸; full basis coverage) |
| Selection time (UTC) | 2026-07-18T06:57:29Z |
| Submission time (UTC) | 2026-07-18T06:57:33Z |
| ISA circuit depth | 4 |
| ISA circuit ops | RZ×16, SX×8, Measure×8, Barrier×1 |

### Backend Calibration (at execution)

| Qubit | Readout Error | T1 (μs) | T2 (μs) |
|-------|---------------|---------|---------|
| 0 | 1.221% | 39.1 | 20.2 |
| 1 | 1.501% | 101.7 | 110.7 |
| 2 | 0.342% | 180.0 | 155.9 |
| 3 | 1.819% | 181.1 | 196.5 |
| 4 | 0.562% | 113.1 | 87.7 |
| 5 | 1.233% | 132.1 | 111.7 |
| 6 | 0.525% | 206.9 | 144.9 |
| 7 | 1.392% | 118.8 | 40.1 |

Backend version: 1.3.37. Calibration captured before submission.

---

## 5. ProofRecord

```json
{
  "schema_version": "witness-proofrecord-1.0",
  "quantum_nonce": "e425dc92c028b344f3f8f46b9c269bf9f8696f87e6b0085d46fad7452770659b",
  "job_id": "d9di7nkinv1c73ap4ed0",
  "backend": "ibm_fez",
  "provider_instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/074ad0b4119241ee8fd51258f35aa4a6:97957880-e0cc-4c0e-a07e-f9b8f2da3be4::",
  "calibration_hash": "1ab5ef208c90ab60ed039c738374c5f51bcc49e2557a3151c23873a4ee1c4f3f",
  "raw_counts_hash": "97bfe36ea8815599d8b11bdbb9ed9cfc0f0946dbf43961e12fe1c42fe1adbcef",
  "context_id": "witness-2-primary",
  "timestamp_utc": "2026-07-18T06:57:33Z",
  "record_hash": "271ff5eae1fdfac85f6fd24ebd919a608804d6f1546a4ca9874f481ce5f97ae1"
}
```

---

## 6. Case Results

### W2-C1 — Honest End-to-End Verification

**Verdict: PASS**

| Check | Result |
|-------|--------|
| record_hash_match | ✅ true |
| quantum_nonce_match | ✅ true |
| raw_counts_hash_match | ✅ true |
| cal_hash_match | ✅ true |
| schema_version_match | ✅ true |
| context_id_present | ✅ true |
| provider_instance_present | ✅ true |
| provider_job_found | ✅ true |
| provider_counts_match | ✅ true |

**Provenance note:** Confirms stored job_id and counts match IBM provider API record at verification time. Does not confirm physical origin or quality of QPU randomness.

---

### W2-C2 — Substitution / Tamper Detection (4 sub-trials)

**Verdict: PASS**

| Sub-trial | Substitution | Detection Layer | Sub-verdict |
|-----------|-------------|-----------------|-------------|
| a | raw_counts_altered | quantum_nonce | ✅ PASS |
| b | job_id_altered | quantum_nonce and record_hash | ✅ PASS |
| c | calibration_snapshot_altered | quantum_nonce | ✅ PASS |
| d | context_id_altered (record_hash not updated) | record_hash | ✅ PASS |

All four forgery patterns detected. No false negative.

---

### W2-C3 — Cross-Context Replay Rejection (2 sub-cases)

**Verdict: PASS**

| Sub-case | Description | Enforcement Layer | Replay Decision | Sub-verdict |
|----------|-------------|-------------------|-----------------|-------------|
| a | context_id changed, record_hash not recomputed | record_hash | DENY | ✅ PASS |
| b | context_id changed, record_hash recomputed — boundary test | ARK-457 context binding | DENY | ✅ PASS |

**Design boundary note (sub-case b):** record_hash is valid because the attacker recomputed it. DENY is enforced by ARK-457 five-dimensional context binding. This confirms the design boundary: record_hash = field integrity only; context_id enforcement requires the separate authorization layer (ARK-457).

---

## 7. Integrity Summary

| Hash | Value |
|------|-------|
| quantum_nonce | `e425dc92c028b344f3f8f46b9c269bf9f8696f87e6b0085d46fad7452770659b` |
| raw_counts_hash | `97bfe36ea8815599d8b11bdbb9ed9cfc0f0946dbf43961e12fe1c42fe1adbcef` |
| calibration_hash | `1ab5ef208c90ab60ed039c738374c5f51bcc49e2557a3151c23873a4ee1c4f3f` |
| record_hash | `271ff5eae1fdfac85f6fd24ebd919a608804d6f1546a4ca9874f481ce5f97ae1` |

All hashes computed deterministically from QPU output. No post-hoc modification.

---

## 8. Artifacts

| Artifact | Path |
|----------|------|
| ProofRecord | `witness-2/results/proofrecord.json` |
| Raw counts | `witness-2/results/raw/raw_counts.json` |
| Job metadata | `witness-2/results/raw/job_meta.json` |
| Calibration snapshot | `witness-2/results/raw/calibration_snapshot.json` |
| W2-C1 result | `witness-2/results/W2-C1-result.json` |
| W2-C2 result | `witness-2/results/W2-C2-result.json` |
| W2-C3 result | `witness-2/results/W2-C3-result.json` |
| Preregistration (MD) | `witness-2/prereg/WITNESS-2-prereg.md` |
| Preregistration (PDF) | `witness-2/prereg/WITNESS-2-prereg.pdf` |
| Preregistration (DOCX) | `witness-2/prereg/WITNESS-2-prereg.docx` |
| MANIFEST | `witness-2/MANIFEST.sha256` |

---

## 9. Scope and Limitations

1. **Provider provenance only.** W2-C1 confirms that the job_id and counts match the IBM provider API at verification time. This confirms provider record integrity, not physical QPU origin or randomness quality.

2. **Harness fixes disclosed.** Two pre-execution harness fixes (FIX-1, FIX-2) were applied and committed before any QPU job was submitted. They did not change the circuit, shot count, eligibility criteria, case definitions, or decision procedure. MANIFEST.sha256 was recomputed and recommitted after each fix.

3. **Open plan budget.** Job was submitted on the IBM Quantum open plan. Budget status confirmed (125s remaining) before submission.

4. **ARK-457 boundary confirmed.** Sub-case W2-C3b demonstrates that record_hash recomputation by an attacker is insufficient for cross-context replay; only ARK-457 context binding blocks it.

---

## 10. WITNESS Series Context

| Experiment | Status | DOI |
|------------|--------|-----|
| WITNESS-1 | ✅ Published | [10.5281/zenodo.21424324](https://doi.org/10.5281/zenodo.21424324) |
| WITNESS-2 | ✅ Complete — Zenodo pending | (this deposit) |

WITNESS series concept DOI: [10.5281/zenodo.21424323](https://doi.org/10.5281/zenodo.21424323)

---

*Report generated: 2026-07-18. All verdicts reflect actual QPU execution output. No synthetic data.*  
*Remnant Fieldworks Inc. — To God be the glory.*
