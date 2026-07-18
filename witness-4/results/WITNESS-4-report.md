# WITNESS-4 Execution Report
**The Freshness Bracket: Non-Backdatable, Independently-Reconstructable, Chain-Linked Quantum ProofRecord™**

---

## Executive Summary

**Overall Verdict:** ALL PASS

WITNESS-4 "The Freshness Bracket" answers two foundational audit questions every ProofRecord must address:
1. **"Could this have been backdated or pre-computed?"** — No. The full experimental design was hashed **before** any random anchor was fetched (*design-before-anchor*), and the fused nonce commits to a NIST beacon pulse that did not exist before its published time (*not-before* lower bound).
2. **"Can I rebuild it myself from public data?"** — Yes. A dedicated reconstruction module rebuilt the entire record — every hash, the fused nonce, the CHSH statistic, the freshness bracket, and the record_hash — from public artifacts alone, confirmed by the IBM provider.

WITNESS-4 also establishes an **append-only ledger**: it chain-links to WITNESS-3's published record_hash (Zenodo DOI 10.5281/zenodo.21434832), making WITNESS-1→2→3→**4** a single third-party-verifiable ledger. The same QPU run remained a CHSH Bell test, certified under the identical honest standard used in WITNESS-3.

All five test cases — zero-trust reconstruction, tamper detection (8 trials), backdating/freshness, chain integrity, and Bell certification — returned **PASS** verdicts.

---

## QPU Execution

| Parameter | Value |
|-----------|-------|
| **Job ID** | `d9e0mjsjeosc73fi6b50` |
| **Backend** | `ibm_fez` (IBM Quantum, us-east region) |
| **Instance** | `crn:v1:bluemix:public:quantum-computing:us-east:a/074ad0b4119241ee8fd51258f35aa4a6:97957880-e0cc-4c0e-a07e-f9b8f2da3be4::` |
| **Timestamp (finalize)** | 2026-07-18T23:30:09Z |
| **Total Shots** | 8000 (4 CHSH settings × 2000 shots/setting) |
| **Unique 2-qubit Outcomes per Setting** | ab: 4/4, abp: 4/4, apb: 4/4, apbp: 4/4 |
| **Qubits** | 0, 1 (logical; transpiler maps to physical layout) |

---

## Freshness Bracket (Temporal Ordering)

The freshness bracket establishes **relative ordering** and a **not-before lower time bound**:

```
precommit_time_utc  <=  nist_pulse_time  <=  timestamp_utc (finalize)
```

| Timestamp | Value | Significance |
|-----------|-------|--------------|
| **Pre-commitment** | 2026-07-18T23:24:56Z | Design (circuit + intent + context + prev link) hashed BEFORE any anchor fetched |
| **NIST Pulse** | 2026-07-18T23:27:00.000Z | Beacon outputValue did not exist before this time |
| **Finalize** | 2026-07-18T23:30:09Z | Record finalized (nonce fused, freshness evaluated) |

**Freshness Verdict:** `fresh = True`
- `not_before_bound_ok`: True (record ≥ pulse time)
- `design_before_anchor_ok`: True (precommit ≤ pulse time)
- `chain_monotonic_ok`: True (record ≥ previous ledger entry)

**Honesty bounds (preregistered):** This is a *relative-ordering* / *not-before* proof only. It is **not** a trusted timestamping authority or blockchain, asserts **no upper time bound**, and the CHSH test is **not** loophole-free / device-independent.

---

## Append-Only Ledger Link

WITNESS-4 chains to **WITNESS-3** (Zenodo DOI 10.5281/zenodo.21434832):

| Field | Value |
|-------|-------|
| **prev_record_hash** | `858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf` |
| **Genesis Source** | WITNESS-3 published record_hash |
| **Ledger** | WITNESS-1 → WITNESS-2 → WITNESS-3 → **WITNESS-4** |

This makes the WITNESS series a single append-only, third-party-verifiable ledger.

---

## CHSH Bell-Inequality Violation (Device-Dependent Certification)

| Metric | Value |
|--------|-------|
| **S** | 2.5950 ± 0.0340 |
| **\|S\|** | 2.5950 |
| **Classical Bound** | 2.0 |
| **Tsirelson Bound** | 2.8284 |
| **Violation** | 17.5 standard deviations above classical |
| **Bell Certified** | `True` |

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
| **precommit_hash** | `a29de09bef84f459…` | Design fixed before anchors |
| **prev_record_hash** | `858ffd49fd7517fd…` | WITNESS-3 ledger link |
| **raw_counts_hash** | `4c6b7f66fe3c0eea…` | QPU measurement outcomes |
| **job_id** | `d9e0mjsjeosc73fi…` | IBM provider job record |
| **calibration_hash** | `82543204b09b3083…` | Backend snapshot at run time |
| **nist_hash** | `6fb000218c6782b8…` | NIST beacon pulse 2026-07-18T23:27:00.000Z |
| **astro_hash** | `4e9f0a786650a679…` | LIGO/GWOSC GW150914 strain (provenance-only) |

**Fused Nonce:** `01f07fd8f46e40cabf089f7cdbfb0648924732589d09d95d0e39fa9610e13f94`

---

## Case Verdicts

| Case | Description | Verdict |
|------|-------------|---------|
| **W4-C1** | Zero-trust reconstruction from public artifacts + provider confirmation | **PASS** |
| **W4-C2** | Tamper detection across all witnesses + precommit + ledger link (8 sub-trials) | **PASS** |
| **W4-C3** | Backdating / pre-computation detection (flagship freshness case) | **PASS** |
| **W4-C4** | Append-only ledger chain integrity (honest link + 3-way broken-link detection) | **PASS** |
| **W4-C5** | CHSH Bell-inequality violation certification (device-dependent) | **PASS** |

---

## ProofRecord™ (schema v4.0)

**record_hash:** `786ceb9a8bd46713de3b7da11cdb7f95518751381b885506d9c66d60c32e3dae`

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

**Report generated:** 2026-07-18T23:30:09Z  
**WITNESS-4 schema:** `witness-proofrecord-4.0`  
**Preregistration:** locked before QPU execution (`witness-4/MANIFEST.sha256`)  
**Zenodo DOI:** *(Held for review and file-first IP-gate decision)*
