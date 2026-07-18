# WITNESS-3 Execution Report
**Cosmic Beacon: CHSH Bell + NIST Beacon + LIGO/GWOSC Fused Authorization Nonce**

---

## Executive Summary

**Overall Verdict:** ALL PASS

WITNESS-3 "Cosmic Beacon" successfully fused **three independent, publicly re-verifiable physical witnesses** into a single ExecutionProof authorization nonce:
1. **CHSH Bell-inequality violation** measured on a real IBM QPU (certifies quantum non-classicality **AND** seeds the nonce),
2. A **NIST public Randomness Beacon** pulse,
3. A **byte-exact LIGO/GWOSC gravitational-wave data segment** from the first confirmed black-hole merger (GW150914).

All four test cases — Bell certification, tamper detection, replay prevention, and honest end-to-end verification — returned **PASS** verdicts. The cosmic nonce and ProofRecord are publicly re-verifiable: every source witness can be independently fetched and verified by third parties.

---

## QPU Execution

| Parameter | Value |
|-----------|-------|
| **Job ID** | `d9dvul2neu4c739nrdl0` |
| **Backend** | `ibm_fez` (IBM Quantum, us-east region) |
| **Instance** | `crn:v1:bluemix:public:quantum-computing:us-east:a/074ad0b4119241ee8fd51258f35aa4a6:97957880-e0cc-4c0e-a07e-f9b8f2da3be4::` |
| **Timestamp** | 2026-07-18T22:33:56Z |
| **Total Shots** | 8000 (4 CHSH settings × 2000 shots/setting) |
| **Unique 2-qubit Outcomes per Setting** | ab: 4/4, abp: 4/4, apb: 4/4, apbp: 4/4 |
| **Qubits** | 0, 1 (logical; transpiler maps to physical layout) |

---

## CHSH Bell Test Results

The CHSH Bell-inequality parameter **S** is computed as:

**S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)**

where each **E(α,β)** is the expectation value of the product of Alice's and Bob's measurements for setting pair (α,β).

| Metric | Value |
|--------|-------|
| **S** | **2.545** |
| **σ(S)** | 0.03449 |
| **Classical bound** | 2.0 |
| **Tsirelson bound** | 2.8284 |
| **Violation strength** | **15.8 σ** above classical |
| **Bell-certified** | **True** |

### Correlators (Expectation Values)

| Setting Pair | E(α,β) | Shots | Variance | Sign in S |
|--------------|--------|-------|----------|-----------|
| **a,b** | +0.621 | 2000 | 0.00030718 | +1 |
| **a,b′** | -0.641 | 2000 | 0.00029456 | -1 |
| **a′,b** | +0.618 | 2000 | 0.00030904 | +1 |
| **a′,b′** | +0.665 | 2000 | 0.00027889 | +1 |

**Measurement angles:**
- Alice: **a = 0**, **a′ = π/2**
- Bob: **b = π/4**, **b′ = 3π/4**

**Certification criteria (all must hold for PASS):**
1. ✅ |S| > 2 (violation of classical bound)
2. ✅ Violation ≥ 5σ statistical significance
3. ✅ |S| ≤ Tsirelson + 0.10 tolerance (consistency with quantum theory)

**Scope:** This certifies a Bell-inequality violation on the tested backend/circuit/qubits/calibration/shots under **fair-sampling** and **no-signalling** assumptions. It is **NOT** a loophole-free or device-independent certification.

---

## External Witnesses (Third-Party Re-verifiable)

### NIST Randomness Beacon

| Field | Value |
|-------|-------|
| **Pulse Index** | 1865471 |
| **Timestamp** | 2026-07-18T22:31:00.000Z |
| **Output Value** | `18665602CA473D9F1962128AB8AAF1BF8C239C581DC2AA3F17FC6E69199E2D0B...` |
| **Signature (First 64 chars)** | `N/A...` |
| **NIST Hash (SHA-256)** | `f6f2d192f2b897cdff35e7da53f83dd7c9b5288aaf69fd2eabb4b21fd5043937` |
| **Re-verification URL** | https://beacon.nist.gov/beacon/2.0/pulse/time/2026-07-18T22%3A31%3A00.000Z |

The NIST beacon pulse is a **publicly timestamped, signed random value** broadcast every 60 seconds. The `nist_hash` in the ProofRecord is computed as SHA-256(`pulseIndex || timeStamp || outputValue || signatureValue`), allowing anyone to fetch the same pulse and verify the hash.

### LIGO/GWOSC Astrophysical Witness (GW150914)

| Field | Value |
|-------|-------|
| **Event** | GW150914 (first confirmed gravitational-wave detection, black-hole merger) |
| **Detector** | LIGO Hanford (H1) |
| **File URL** | https://gwosc.org/s/events/GW150914/H-H1_LOSC_4_V1-1126259446-32.hdf5 |
| **File Size** | 1036463 bytes |
| **File SHA-256** | `66c4b196d8b9e4d6be99c5a73173ad7a8285e6457ef55dc7710a6ebc057db669` |
| **HDF5 Strain Dataset** | `/strain/Strain` |
| **Strain Window** | offset=65536, samples=4096, quantization=1e-24 |
| **Strain SHA-256** | `5c628ac3804475ad7fa8e6bb997f165934eda83644f518a2006e712b98406e9b` |
| **Astro Hash (SHA-256)** | `4e9f0a786650a67913f866971a756113ed080dfd90e231710654ff0c80ffeb40` |

The GWOSC (Gravitational Wave Open Science Center) hosts **byte-exact, version-controlled open data** from LIGO/Virgo detectors. The `astro_hash` in the ProofRecord is computed as SHA-256(`file_sha256 || strain_sha256 || url || metadata`). Anyone can download the same HDF5 file, read the same strain window, and verify the hash. This witness binds the authorization nonce to **publicly archived astrophysical data** from a historic detection event.

**Scope:** The astro segment is a **PROVENANCE WITNESS** only. It does NOT constitute a detection claim, cosmological measurement, or independent verification of the GW150914 event. The data is used as a **publicly re-verifiable byte anchor** for the nonce.

---

## ProofRecord

**Schema:** `witness-proofrecord-3.0`

```json
{
  "cosmic_nonce": "6876050a7f8ebadf79b1bd702346ae42563019725c03d29bd8d26dadc8c7f686",
  "job_id": "d9dvul2neu4c739nrdl0",
  "backend": "ibm_fez",
  "provider_instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/074ad0b4119241ee8fd51258f35aa4a6:97957880-e0cc-4c0e-a07e-f9b8f2da3be4::",
  "calibration_hash": "dc4f3463a3812377225a2fd6ba91dd8e94eca99b244cc7fa6ff2d3cc9adf7a9e",
  "raw_counts_hash": "6c98687097c328004c4263da1d2e526173359d301fef328ab1ff9fb8bc40e1a1",
  "nist_hash": "f6f2d192f2b897cdff35e7da53f83dd7c9b5288aaf69fd2eabb4b21fd5043937",
  "astro_hash": "4e9f0a786650a67913f866971a756113ed080dfd90e231710654ff0c80ffeb40",
  "chsh": { ... },
  "bell_certified": true,
  "context_id": "witness-3-cosmic-beacon",
  "timestamp_utc": "2026-07-18T22:33:56Z",
  "record_hash": "858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf"
}
```

**Cosmic Nonce Construction (v3):**  
`cosmic_nonce = SHA-256(LP(raw_counts_hash) || LP(job_id) || LP(calibration_hash) || LP(nist_hash) || LP(astro_hash))`

where `LP(x)` is length-prefixed serialization (prevents boundary-collision attacks). The nonce **binds together** all five witnesses in a single deterministic, verifiable digest.

---

## Test Case Verdicts

| Case | Description | Verdict |
|------|-------------|---------|
| **W3-C4** | CHSH Bell-inequality violation certification | **PASS** |
| **W3-C2** | Tamper detection (6 sub-trials: QPU, NIST, astro, job_id, cal, context_id) | **PASS** |
| **W3-C3** | Cross-context replay prevention (2 sub-cases: no-recompute, ARK-457) | **PASS** |
| **W3-C1** | Honest end-to-end verification (15 checks) | **PASS** |

### W3-C4: CHSH Bell Certification

**Verdict:** PASS

All three certification criteria satisfied:
- ✅ |S| = 2.545 > 2 (classical bound)
- ✅ 15.8 σ ≥ 5 σ (statistical significance)
- ✅ |S| = 2.545 ≤ 2.8284 + 0.10 (Tsirelson tolerance)

The CHSH test confirms **quantum non-classicality** for the measured correlation pattern. The same measurement bits that certify the Bell violation **also seed the cosmic nonce**, tying the nonce to a verified quantum resource.

### W3-C2: Tamper Detection

**Verdict:** PASS

All 6 sub-trials detected forgery:
- ✅ **raw_counts** substitution → nonce mismatch detected
- ✅ **job_id** alteration → nonce + record_hash mismatch detected
- ✅ **calibration** manipulation → nonce mismatch detected
- ✅ **NIST witness** alteration → nonce mismatch detected
- ✅ **Astro witness** alteration → nonce mismatch detected
- ✅ **context_id** change (record_hash NOT recomputed) → record_hash mismatch detected

The five-witness fusion makes the cosmic nonce highly tamper-evident: altering any single witness invalidates the entire ProofRecord.

### W3-C3: Replay Prevention

**Verdict:** PASS

Both sub-cases denied cross-context replay:
- **Sub-case A (no recompute):** record_hash mismatch → replay denied
- **Sub-case B (recompute + ARK-457):** record_hash valid after recompute, but ARK-457 authorization layer → **DENY** due to context mismatch

**Design note:** `record_hash` is a field-integrity seal, NOT a context-binding mechanism. Authorization enforcement requires a separate layer (ARK-457 checks all 5 context dimensions: tenant, session, resource, audience, environment). This is the intended, correct behavior.

### W3-C1: Honest End-to-End Verification

**Verdict:** PASS

All 15 verification checks passed:
- ✅ Record Hash Match
- ✅ Cosmic Nonce Match
- ✅ Raw Counts Hash Match
- ✅ Cal Hash Match
- ✅ Nist Hash Match
- ✅ Astro Hash Match
- ✅ Chsh S Reproducible
- ✅ Schema Version Match
- ✅ Context Id Present
- ✅ Provider Instance Present
- ✅ Nist Witness Present
- ✅ Astro Witness Present
- ✅ Provider Job Found
- ✅ Provider Counts Match

**Provider provenance:** The `provider_job_found` and `provider_counts_match` checks confirm that the stored `job_id` and per-setting measurement counts match the IBM Quantum provider's API record at verification time. This does NOT confirm the physical origin or quality of QPU randomness, but it does establish that the claimed job exists and the counts were not fabricated post-hoc.

---

## Harness Fix Disclosure

**Post-lock fix applied:**

**FIX-W3-1 (channel parameter):**  
`submit_job.py` line 63: changed `channel="ibm_quantum_platform"` → `channel="ibm_cloud"` to match the working IBM Quantum Runtime API endpoint for the open-plan instance. The preregistered MANIFEST.sha256 locked the harness before this fix; the fix was required to complete the actual QPU submission. This is disclosed per the RF Standing Covenant (transparency on post-lock modifications).

No other harness fixes were needed. All other source modules match their preregistered SHA-256 hashes in `MANIFEST.sha256`.

---

## Honesty Bounds (per RF Standing Covenant)

1. **NOT loophole-free:** This CHSH test does NOT close the locality or detection loopholes. Alice and Bob measurement stations are neighboring transmons on the same chip (no spacelike separation).
2. **NOT device-independent:** The test assumes fair-sampling (no post-selection bias) and no-signalling (no communication between qubits during measurement), but does NOT verify these from first principles.
3. **Fixed measurement settings:** The four CHSH setting pairs were preregistered and fixed before execution (no adaptive measurement choices).
4. **Astro witness is provenance only:** The LIGO/GWOSC data segment is used as a **publicly re-verifiable byte anchor** for the nonce. It does NOT constitute an independent detection, cosmological measurement, or claim about the GW150914 event.
5. **No legal/security/production guarantee:** This is a research experiment demonstrating quantum-sourced nonce provenance. It does NOT claim legal enforceability, cryptographic security against all adversaries, production readiness, or RF-100 compliance.
6. **Findings bound to tested conditions:** The Bell certification applies ONLY to the specific backend (`ibm_fez`), qubits (0, 1 logical), calibration snapshot (timestamp `2026-07-18T22:33:56Z`), and shot count (8000). Generalization to other backends, qubits, or configurations requires separate tests.

---

## Re-verification Instructions

To independently re-verify this ProofRecord:

1. **Fetch raw artifacts** from `witness-testbeds` GitHub repo: `witness-3/results/raw/*.json`
2. **Recompute hashes:**
   - `raw_counts_hash = SHA-256(canonical_json(raw_counts))`
   - `calibration_hash = SHA-256(canonical_json(calibration_snapshot))`
   - `nist_hash = SHA-256(pulseIndex || timeStamp || outputValue || signatureValue)` (fetch from NIST beacon API)
   - `astro_hash = SHA-256(file_sha256 || strain_sha256 || url || metadata)` (download GWOSC HDF5 file)
3. **Recompute cosmic_nonce** using the v3 construction (see `nonce_v3.py`)
4. **Recompute record_hash** (SHA-256 of all other ProofRecord fields in canonical order)
5. **Verify CHSH S** from raw counts (see `chsh.py`)
6. **Query IBM Quantum provider** for job `d9dvul2neu4c739nrdl0` (requires IBM account) to confirm job existence and counts

All source code and raw data are public. The NIST beacon pulse and GWOSC strain file are third-party, timestamped, signed/archived resources — no trust in Remnant Fieldworks is required to verify those witnesses.

---

## Research Context

WITNESS-3 is part of the **Remnant Fieldworks ExecutionProof research program**, exploring verifiable-provenance quantum-sourced nonces for high-consequence authorization boundaries. It extends WITNESS-1 and WITNESS-2 by:
- Fusing **three independent witnesses** (quantum + beacon + astrophysical) instead of one
- Certifying the quantum witness via **Bell-inequality violation** (not just raw entropy)
- Binding the nonce to **publicly archived LIGO gravitational-wave data** (historic, byte-exact, third-party re-verifiable)

This experiment demonstrates that an authorization nonce can carry **publicly auditable provenance from multiple physical sources**, reducing reliance on any single trust anchor.

---

## Acknowledgments

- **IBM Quantum** for open-plan QPU access (`ibm_fez`, us-east region)
- **NIST** for the public Randomness Beacon service (pulse 1865471)
- **LIGO/GWOSC** for open gravitational-wave data (GW150914, H1 detector)

---

## References

- WITNESS concept DOI: [10.5281/zenodo.21424323](https://doi.org/10.5281/zenodo.21424323)
- WITNESS-1 DOI: [10.5281/zenodo.21424324](https://doi.org/10.5281/zenodo.21424324)
- WITNESS-2 DOI: [10.5281/zenodo.21425381](https://doi.org/10.5281/zenodo.21425381)
- ARK concept DOI: [10.5281/zenodo.21398675](https://doi.org/10.5281/zenodo.21398675)
- NIST Randomness Beacon: https://beacon.nist.gov/
- LIGO/GWOSC: https://gwosc.org/
- Remnant Fieldworks GitHub: https://github.com/derekhone/

---

**Preregistration commit:** `ac18f61` (2026-07-18, `witness-testbeds` repo)  
**Report generated:** 2026-07-18 22:40:20 UTC

---

*Soli Deo Gloria.*
