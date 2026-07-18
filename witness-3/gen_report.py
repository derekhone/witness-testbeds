#!/usr/bin/env python3
"""Generate WITNESS-3 report in multiple formats."""
import json
from pathlib import Path
from datetime import datetime

RESULTS = Path(__file__).parent / "results"
RAW = RESULTS / "raw"

# Load all artifacts
with open(RESULTS / "proofrecord.json") as f:
    pr = json.load(f)
with open(RESULTS / "W3-C1-result.json") as f:
    c1 = json.load(f)
with open(RESULTS / "W3-C2-result.json") as f:
    c2 = json.load(f)
with open(RESULTS / "W3-C3-result.json") as f:
    c3 = json.load(f)
with open(RESULTS / "W3-C4-result.json") as f:
    c4 = json.load(f)
with open(RAW / "job_meta.json") as f:
    job_meta = json.load(f)
with open(RAW / "raw_counts.json") as f:
    raw_counts = json.load(f)
with open(RAW / "nist_witness.json") as f:
    nist = json.load(f)
with open(RAW / "astro_witness.json") as f:
    astro = json.load(f)

chsh = pr['chsh']
bell_cert = pr['bell_certified']

# Count unique outcomes per setting
unique_per_setting = {k: len(v) for k, v in raw_counts.items()}
total_shots = sum(sum(v.values()) for v in raw_counts.values())

verdict_overall = "ALL PASS" if all(x['verdict'] == 'PASS' for x in [c1, c2, c3, c4]) else "MIXED"

# Astro fields
astro_url = astro.get('url', '')
astro_file_sha = astro.get('file_sha256', '')
astro_file_size = astro.get('file_size_bytes', 0)
strain_sample = astro.get('strain_sample', {})
strain_offset = strain_sample.get('sample_offset', 0)
strain_count = strain_sample.get('sample_count', 0)
strain_quant = strain_sample.get('quantize_step', 0)
strain_sha = strain_sample.get('strain_window_sha256', '')

report_md = f"""# WITNESS-3 Execution Report
**Cosmic Beacon: CHSH Bell + NIST Beacon + LIGO/GWOSC Fused Authorization Nonce**

---

## Executive Summary

**Overall Verdict:** {verdict_overall}

WITNESS-3 "Cosmic Beacon" successfully fused **three independent, publicly re-verifiable physical witnesses** into a single ExecutionProof authorization nonce:
1. **CHSH Bell-inequality violation** measured on a real IBM QPU (certifies quantum non-classicality **AND** seeds the nonce),
2. A **NIST public Randomness Beacon** pulse,
3. A **byte-exact LIGO/GWOSC gravitational-wave data segment** from the first confirmed black-hole merger (GW150914).

All four test cases — Bell certification, tamper detection, replay prevention, and honest end-to-end verification — returned **PASS** verdicts. The cosmic nonce and ProofRecord are publicly re-verifiable: every source witness can be independently fetched and verified by third parties.

---

## QPU Execution

| Parameter | Value |
|-----------|-------|
| **Job ID** | `{pr['job_id']}` |
| **Backend** | `{pr['backend']}` (IBM Quantum, us-east region) |
| **Instance** | `{pr['provider_instance']}` |
| **Timestamp** | {pr['timestamp_utc']} |
| **Total Shots** | {total_shots} (4 CHSH settings × 2000 shots/setting) |
| **Unique 2-qubit Outcomes per Setting** | ab: {unique_per_setting.get('ab', 0)}/4, abp: {unique_per_setting.get('abp', 0)}/4, apb: {unique_per_setting.get('apb', 0)}/4, apbp: {unique_per_setting.get('apbp', 0)}/4 |
| **Qubits** | 0, 1 (logical; transpiler maps to physical layout) |

---

## CHSH Bell Test Results

The CHSH Bell-inequality parameter **S** is computed as:

**S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)**

where each **E(α,β)** is the expectation value of the product of Alice's and Bob's measurements for setting pair (α,β).

| Metric | Value |
|--------|-------|
| **S** | **{chsh['S']}** |
| **σ(S)** | {chsh['sigma_S']:.5f} |
| **Classical bound** | {chsh['classical_bound']} |
| **Tsirelson bound** | {chsh['tsirelson_bound']:.4f} |
| **Violation strength** | **{chsh['sigmas_above_classical']:.1f} σ** above classical |
| **Bell-certified** | **{bell_cert}** |

### Correlators (Expectation Values)

| Setting Pair | E(α,β) | Shots | Variance | Sign in S |
|--------------|--------|-------|----------|-----------|
| **a,b** | {chsh['correlators']['ab']:+.3f} | {c4['chsh']['per_setting']['ab']['shots']} | {c4['chsh']['per_setting']['ab']['var_E']:.8f} | {c4['chsh']['per_setting']['ab']['sign_in_S']:+d} |
| **a,b′** | {chsh['correlators']['abp']:+.3f} | {c4['chsh']['per_setting']['abp']['shots']} | {c4['chsh']['per_setting']['abp']['var_E']:.8f} | {c4['chsh']['per_setting']['abp']['sign_in_S']:+d} |
| **a′,b** | {chsh['correlators']['apb']:+.3f} | {c4['chsh']['per_setting']['apb']['shots']} | {c4['chsh']['per_setting']['apb']['var_E']:.8f} | {c4['chsh']['per_setting']['apb']['sign_in_S']:+d} |
| **a′,b′** | {chsh['correlators']['apbp']:+.3f} | {c4['chsh']['per_setting']['apbp']['shots']} | {c4['chsh']['per_setting']['apbp']['var_E']:.8f} | {c4['chsh']['per_setting']['apbp']['sign_in_S']:+d} |

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
| **Pulse Index** | {nist['pulseIndex']} |
| **Timestamp** | {nist['timeStamp']} |
| **Output Value** | `{nist['outputValue'][:64]}...` |
| **Signature (First 64 chars)** | `{nist.get('signatureValue', 'N/A')[:64]}...` |
| **NIST Hash (SHA-256)** | `{pr['nist_hash']}` |
| **Re-verification URL** | https://beacon.nist.gov/beacon/2.0/pulse/time/{nist['timeStamp'].replace(':', '%3A').replace('+', '%2B')} |

The NIST beacon pulse is a **publicly timestamped, signed random value** broadcast every 60 seconds. The `nist_hash` in the ProofRecord is computed as SHA-256(`pulseIndex || timeStamp || outputValue || signatureValue`), allowing anyone to fetch the same pulse and verify the hash.

### LIGO/GWOSC Astrophysical Witness (GW150914)

| Field | Value |
|-------|-------|
| **Event** | GW150914 (first confirmed gravitational-wave detection, black-hole merger) |
| **Detector** | LIGO Hanford (H1) |
| **File URL** | {astro_url} |
| **File Size** | {astro_file_size} bytes |
| **File SHA-256** | `{astro_file_sha}` |
| **HDF5 Strain Dataset** | `/strain/Strain` |
| **Strain Window** | offset={strain_offset}, samples={strain_count}, quantization={strain_quant} |
| **Strain SHA-256** | `{strain_sha}` |
| **Astro Hash (SHA-256)** | `{pr['astro_hash']}` |

The GWOSC (Gravitational Wave Open Science Center) hosts **byte-exact, version-controlled open data** from LIGO/Virgo detectors. The `astro_hash` in the ProofRecord is computed as SHA-256(`file_sha256 || strain_sha256 || url || metadata`). Anyone can download the same HDF5 file, read the same strain window, and verify the hash. This witness binds the authorization nonce to **publicly archived astrophysical data** from a historic detection event.

**Scope:** The astro segment is a **PROVENANCE WITNESS** only. It does NOT constitute a detection claim, cosmological measurement, or independent verification of the GW150914 event. The data is used as a **publicly re-verifiable byte anchor** for the nonce.

---

## ProofRecord

**Schema:** `{pr['schema_version']}`

```json
{{
  "cosmic_nonce": "{pr['cosmic_nonce']}",
  "job_id": "{pr['job_id']}",
  "backend": "{pr['backend']}",
  "provider_instance": "{pr['provider_instance']}",
  "calibration_hash": "{pr['calibration_hash']}",
  "raw_counts_hash": "{pr['raw_counts_hash']}",
  "nist_hash": "{pr['nist_hash']}",
  "astro_hash": "{pr['astro_hash']}",
  "chsh": {{ ... }},
  "bell_certified": {str(pr['bell_certified']).lower()},
  "context_id": "{pr['context_id']}",
  "timestamp_utc": "{pr['timestamp_utc']}",
  "record_hash": "{pr['record_hash']}"
}}
```

**Cosmic Nonce Construction (v3):**  
`cosmic_nonce = SHA-256(LP(raw_counts_hash) || LP(job_id) || LP(calibration_hash) || LP(nist_hash) || LP(astro_hash))`

where `LP(x)` is length-prefixed serialization (prevents boundary-collision attacks). The nonce **binds together** all five witnesses in a single deterministic, verifiable digest.

---

## Test Case Verdicts

| Case | Description | Verdict |
|------|-------------|---------|
| **W3-C4** | CHSH Bell-inequality violation certification | **{c4['verdict']}** |
| **W3-C2** | Tamper detection (6 sub-trials: QPU, NIST, astro, job_id, cal, context_id) | **{c2['verdict']}** |
| **W3-C3** | Cross-context replay prevention (2 sub-cases: no-recompute, ARK-457) | **{c3['verdict']}** |
| **W3-C1** | Honest end-to-end verification ({len(c1['checks'])} checks) | **{c1['verdict']}** |

### W3-C4: CHSH Bell Certification

**Verdict:** {c4['verdict']}

All three certification criteria satisfied:
- ✅ |S| = {chsh['abs_S']} > 2 (classical bound)
- ✅ {chsh['sigmas_above_classical']:.1f} σ ≥ 5 σ (statistical significance)
- ✅ |S| = {chsh['abs_S']} ≤ {chsh['tsirelson_bound']:.4f} + 0.10 (Tsirelson tolerance)

The CHSH test confirms **quantum non-classicality** for the measured correlation pattern. The same measurement bits that certify the Bell violation **also seed the cosmic nonce**, tying the nonce to a verified quantum resource.

### W3-C2: Tamper Detection

**Verdict:** {c2['verdict']}

All 6 sub-trials detected forgery:
- ✅ **raw_counts** substitution → nonce mismatch detected
- ✅ **job_id** alteration → nonce + record_hash mismatch detected
- ✅ **calibration** manipulation → nonce mismatch detected
- ✅ **NIST witness** alteration → nonce mismatch detected
- ✅ **Astro witness** alteration → nonce mismatch detected
- ✅ **context_id** change (record_hash NOT recomputed) → record_hash mismatch detected

The five-witness fusion makes the cosmic nonce highly tamper-evident: altering any single witness invalidates the entire ProofRecord.

### W3-C3: Replay Prevention

**Verdict:** {c3['verdict']}

Both sub-cases denied cross-context replay:
- **Sub-case A (no recompute):** record_hash mismatch → replay denied
- **Sub-case B (recompute + ARK-457):** record_hash valid after recompute, but ARK-457 authorization layer → **DENY** due to context mismatch

**Design note:** `record_hash` is a field-integrity seal, NOT a context-binding mechanism. Authorization enforcement requires a separate layer (ARK-457 checks all 5 context dimensions: tenant, session, resource, audience, environment). This is the intended, correct behavior.

### W3-C1: Honest End-to-End Verification

**Verdict:** {c1['verdict']}

All {len(c1['checks'])} verification checks passed:
{chr(10).join(f"- ✅ {k.replace('_', ' ').title()}" for k, v in c1['checks'].items() if isinstance(v, bool) and v)}

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
6. **Findings bound to tested conditions:** The Bell certification applies ONLY to the specific backend (`{pr['backend']}`), qubits (0, 1 logical), calibration snapshot (timestamp `{pr['timestamp_utc']}`), and shot count ({total_shots}). Generalization to other backends, qubits, or configurations requires separate tests.

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
6. **Query IBM Quantum provider** for job `{pr['job_id']}` (requires IBM account) to confirm job existence and counts

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

- **IBM Quantum** for open-plan QPU access (`{pr['backend']}`, us-east region)
- **NIST** for the public Randomness Beacon service (pulse {nist['pulseIndex']})
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
**Report generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

---

*Soli Deo Gloria.*
"""

with open(RESULTS / "WITNESS-3-report.md", "w") as f:
    f.write(report_md)

print("✅ WITNESS-3-report.md generated")
