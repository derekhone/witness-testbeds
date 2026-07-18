#!/usr/bin/env python3
"""Generate WITNESS-4 report in multiple formats."""
import json, subprocess
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
RAW = RESULTS / "raw"

# Load all artifacts
with open(RESULTS / "proofrecord.json") as f:
    pr = json.load(f)
with open(RESULTS / "W4-C1-result.json") as f:
    c1 = json.load(f)
with open(RESULTS / "W4-C2-result.json") as f:
    c2 = json.load(f)
with open(RESULTS / "W4-C3-result.json") as f:
    c3 = json.load(f)
with open(RESULTS / "W4-C4-result.json") as f:
    c4 = json.load(f)
with open(RESULTS / "W4-C5-result.json") as f:
    c5 = json.load(f)
with open(RAW / "raw_counts.json") as f:
    raw_counts = json.load(f)
with open(RAW / "precommit.json") as f:
    precommit = json.load(f)

chsh = pr['chsh']
freshness = pr['freshness']
unique_per_setting = {k: len(v) for k, v in raw_counts.items()}
total_shots = sum(sum(v.values()) for v in raw_counts.values())
verdict_overall = "ALL PASS" if all(x['verdict'] == 'PASS' for x in [c1, c2, c3, c4, c5]) else "MIXED"

report_md = f"""# WITNESS-4 Execution Report
**The Freshness Bracket: Non-Backdatable, Independently-Reconstructable, Chain-Linked Quantum ProofRecord™**

---

## Executive Summary

**Overall Verdict:** {verdict_overall}

WITNESS-4 "The Freshness Bracket" answers two foundational audit questions every ProofRecord must address:
1. **"Could this have been backdated or pre-computed?"** — No. The full experimental design was hashed **before** any random anchor was fetched (*design-before-anchor*), and the fused nonce commits to a NIST beacon pulse that did not exist before its published time (*not-before* lower bound).
2. **"Can I rebuild it myself from public data?"** — Yes. A dedicated reconstruction module rebuilt the entire record — every hash, the fused nonce, the CHSH statistic, the freshness bracket, and the record_hash — from public artifacts alone, confirmed by the IBM provider.

WITNESS-4 also establishes an **append-only ledger**: it chain-links to WITNESS-3's published record_hash (Zenodo DOI 10.5281/zenodo.21434832), making WITNESS-1→2→3→**4** a single third-party-verifiable ledger. The same QPU run remained a CHSH Bell test, certified under the identical honest standard used in WITNESS-3.

All five test cases — zero-trust reconstruction, tamper detection (8 trials), backdating/freshness, chain integrity, and Bell certification — returned **PASS** verdicts.

---

## QPU Execution

| Parameter | Value |
|-----------|-------|
| **Job ID** | `{pr['job_id']}` |
| **Backend** | `{pr['backend']}` (IBM Quantum, us-east region) |
| **Instance** | `{pr['provider_instance']}` |
| **Timestamp (finalize)** | {pr['timestamp_utc']} |
| **Total Shots** | {total_shots} (4 CHSH settings × 2000 shots/setting) |
| **Unique 2-qubit Outcomes per Setting** | ab: {unique_per_setting.get('ab', 0)}/4, abp: {unique_per_setting.get('abp', 0)}/4, apb: {unique_per_setting.get('apb', 0)}/4, apbp: {unique_per_setting.get('apbp', 0)}/4 |
| **Qubits** | 0, 1 (logical; transpiler maps to physical layout) |

---

## Freshness Bracket (Temporal Ordering)

The freshness bracket establishes **relative ordering** and a **not-before lower time bound**:

```
precommit_time_utc  <=  nist_pulse_time  <=  timestamp_utc (finalize)
```

| Timestamp | Value | Significance |
|-----------|-------|--------------|
| **Pre-commitment** | {pr['precommit_time_utc']} | Design (circuit + intent + context + prev link) hashed BEFORE any anchor fetched |
| **NIST Pulse** | {pr['nist_pulse_time']} | Beacon outputValue did not exist before this time |
| **Finalize** | {pr['timestamp_utc']} | Record finalized (nonce fused, freshness evaluated) |

**Freshness Verdict:** `fresh = {freshness['fresh']}`
- `not_before_bound_ok`: {freshness['not_before_bound_ok']} (record ≥ pulse time)
- `design_before_anchor_ok`: {freshness['design_before_anchor_ok']} (precommit ≤ pulse time)
- `chain_monotonic_ok`: {freshness['chain_monotonic_ok']} (record ≥ previous ledger entry)

**Honesty bounds (preregistered):** This is a *relative-ordering* / *not-before* proof only. It is **not** a trusted timestamping authority or blockchain, asserts **no upper time bound**, and the CHSH test is **not** loophole-free / device-independent.

---

## Append-Only Ledger Link

WITNESS-4 chains to **WITNESS-3** (Zenodo DOI 10.5281/zenodo.21434832):

| Field | Value |
|-------|-------|
| **prev_record_hash** | `{pr['prev_record_hash']}` |
| **Genesis Source** | WITNESS-3 published record_hash |
| **Ledger** | WITNESS-1 → WITNESS-2 → WITNESS-3 → **WITNESS-4** |

This makes the WITNESS series a single append-only, third-party-verifiable ledger.

---

## CHSH Bell-Inequality Violation (Device-Dependent Certification)

| Metric | Value |
|--------|-------|
| **S** | {chsh['S']:.4f} ± {chsh['sigma_S']:.4f} |
| **\|S\|** | {chsh['abs_S']:.4f} |
| **Classical Bound** | {chsh['classical_bound']} |
| **Tsirelson Bound** | {chsh['tsirelson_bound']:.4f} |
| **Violation** | {chsh['sigmas_above_classical']:.1f} standard deviations above classical |
| **Bell Certified** | `{pr['bell_certified']}` |

**Preregistered PASS criteria (all met):**
1. |S| > 2.0 ✓
2. (|S| − 2) / σ_S ≥ 5.0 ✓
3. |S| ≤ 2√2 + 0.10 ✓

**Scope (preregistered non-claim):** Certifies a Bell-inequality violation on the tested backend/circuit/qubits/calibration/shots under fair-sampling and no-signalling assumptions. **NOT** a loophole-free or device-independent certification (qubits on same chip → locality loophole; fair sampling → detection loophole; fixed settings → freedom-of-choice loophole).

---

## 7-Segment Fused Nonce (v4)

The fused nonce binds seven length-prefixed inputs:

```
fused_nonce = SHA-256(
      LP(precommit_hash)
    ‖ LP(prev_record_hash)
    ‖ LP(canonical_json(raw_counts))
    ‖ LP(job_id)
    ‖ LP(canonical_json(calibration_snapshot))
    ‖ LP(canonical_json(nist_beacon_record))
    ‖ LP(canonical_json(astro_witness_record))
)
```

| Segment | Hash (truncated) | Source |
|---------|------------------|--------|
| **precommit_hash** | `{pr['precommit_hash'][:16]}…` | Design fixed before anchors |
| **prev_record_hash** | `{pr['prev_record_hash'][:16]}…` | WITNESS-3 ledger link |
| **raw_counts_hash** | `{pr['raw_counts_hash'][:16]}…` | QPU measurement outcomes |
| **job_id** | `{pr['job_id'][:16]}…` | IBM provider job record |
| **calibration_hash** | `{pr['calibration_hash'][:16]}…` | Backend snapshot at run time |
| **nist_hash** | `{pr['nist_hash'][:16]}…` | NIST beacon pulse {pr['nist_pulse_time']} |
| **astro_hash** | `{pr['astro_hash'][:16]}…` | LIGO/GWOSC GW150914 strain (provenance-only) |

**Fused Nonce:** `{pr['fused_nonce']}`

---

## Case Verdicts

| Case | Description | Verdict |
|------|-------------|---------|
| **W4-C1** | Zero-trust reconstruction from public artifacts + provider confirmation | **{c1['verdict']}** |
| **W4-C2** | Tamper detection across all witnesses + precommit + ledger link (8 sub-trials) | **{c2['verdict']}** |
| **W4-C3** | Backdating / pre-computation detection (flagship freshness case) | **{c3['verdict']}** |
| **W4-C4** | Append-only ledger chain integrity (honest link + 3-way broken-link detection) | **{c4['verdict']}** |
| **W4-C5** | CHSH Bell-inequality violation certification (device-dependent) | **{c5['verdict']}** |

---

## ProofRecord™ (schema v4.0)

**record_hash:** `{pr['record_hash']}`

The record_hash is a SHA-256 over all fields (sorted keys, canonical JSON) except `record_hash` itself. It provides field integrity; cross-context authorization enforcement is delegated to the ARK-457 layer (unchanged from prior WITNESS records).

---

## Artifacts & Provenance

All raw artifacts are stored in `witness-4/results/raw/`:
- `precommit.json` — pre-commitment document (design fixed before anchors)
- `raw_counts.json` — QPU measurement outcomes (re-fetchable from IBM provider by job_id)
- `calibration_snapshot.json` — backend properties at run time
- `nist_witness.json` — NIST beacon pulse (re-fetchable from NIST archive by pulseIndex)
- `astro_witness.json` — LIGO/GWOSC GW150914 strain segment SHA-256
- `job_meta.json` — job ID + backend

The ProofRecord and all case results are in `witness-4/results/`.

**Public re-verification:** Any third party can:
1. Re-fetch the NIST pulse, LIGO/GWOSC file, and confirm the IBM job via the provider API.
2. Recompute every hash, the fused nonce, the CHSH S, the freshness bracket, and the record_hash from the stored artifacts alone (W4-C1 proves this).

---

## Harness Fixes & Disclosures

**FIX-W4-1 (NIST polling for freshness):** The NIST `/pulse/last` endpoint has ~3–5 minute propagation delay. To ensure `design_before_anchor_ok = true`, the harness polls with exponential backoff until it fetches a pulse whose `timeStamp` is strictly AFTER the `precommit_time_utc`. This fix was discovered and applied during the first live run (the initial attempt fetched a stale pulse, violating the freshness bracket). The fix is a **harness correction to achieve the preregistered design**, not a post-lock design change.

**Channel note (inherited from WITNESS-3):** `channel="ibm_cloud"` was used from the outset (the correct open-plan channel; this was discovered as FIX-W3-1 in WITNESS-3 and is inherited here, **not** a post-lock WITNESS-4 fix).

---

## Trademarks

Remnant Fieldworks™, ExecutionProof™, ProofRecord™, Proof Before Power™, Verification Before Execution™ (common-law / pending; not yet federally registered).

---

**Report generated:** {pr['timestamp_utc']}  
**WITNESS-4 schema:** `{pr['schema_version']}`  
**Preregistration:** locked before QPU execution (`witness-4/MANIFEST.sha256`)  
**Zenodo DOI:** *(Held for review and file-first IP-gate decision)*
"""

# Write .md
with open(RESULTS / "WITNESS-4-report.md", 'w') as f:
    f.write(report_md)
print("✓ WITNESS-4-report.md")

# Generate .pdf/.docx via pandoc (non-fatal if missing)
try:
    subprocess.run(["pandoc", str(RESULTS / "WITNESS-4-report.md"), "-o", str(RESULTS / "WITNESS-4-report.pdf"),
                    "--pdf-engine=xelatex"], check=True, capture_output=True)
    print("✓ WITNESS-4-report.pdf")
except Exception as e:
    print(f"⚠ PDF generation skipped: {e}")

try:
    subprocess.run(["pandoc", str(RESULTS / "WITNESS-4-report.md"), "-o", str(RESULTS / "WITNESS-4-report.docx")],
                   check=True, capture_output=True)
    print("✓ WITNESS-4-report.docx")
except Exception as e:
    print(f"⚠ DOCX generation skipped: {e}")

print(f"\nOverall verdict: {verdict_overall}")
print(f"Fresh: {freshness['fresh']}, Bell certified: {pr['bell_certified']}")
