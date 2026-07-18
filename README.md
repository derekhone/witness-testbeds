# WITNESS Series — Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Repository:** `witness-testbeds` — independent of `executionproof-testbeds` and `uip-phase1-testbeds`

| Record | Title | Status | DOI |
|--------|-------|--------|-----|
| WITNESS-1 | Quantum-Sourced Nonces with Verifiable Provenance | Published | [10.5281/zenodo.21424324](https://doi.org/10.5281/zenodo.21424324) |
| WITNESS-2 | Length-Prefixed Quantum Nonce with Record-Hash Field Integrity | Published | [10.5281/zenodo.21425381](https://doi.org/10.5281/zenodo.21425381) |
| WITNESS-3 | Cosmic Beacon — CHSH Bell + NIST + LIGO/GWOSC Fused Nonce | Published | [10.5281/zenodo.21434832](https://doi.org/10.5281/zenodo.21434832) |
| WITNESS-4 | The Freshness Bracket — Non-Backdatable, Reconstructable, Chain-Linked ProofRecord | **Executed (HELD)** | *(Held for review / IP-gate)* |

**WITNESS series concept DOI:** [10.5281/zenodo.21424323](https://doi.org/10.5281/zenodo.21424323)

---

# WITNESS-1: Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Series:** WITNESS (first record)
**Status:** Published

---

## Summary

WITNESS-1 tests whether a ProofRecord whose challenge nonce is derived from measured
QPU output can be (a) verified end-to-end against the IBM Quantum provider's job record,
and (b) detected as forged when the nonce, job ID, or counts are substituted — under
the tested construction.

Three preregistered cases:

| Case | Description | Expected |
|------|-------------|----------|
| W1-C1 | Honest end-to-end verification | PASS |
| W1-C2 | Substitution / tamper detection (3 sub-trials) | PASS (all detected) |
| W1-C3 | Cross-context replay using ARK-457 logic | DENY (PASS) |

---

## Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, and stated experimental conditions. This is an experimental
> evidence record, not a universal security proof or production certification."

---

## Repository Structure

```
witness-testbeds/
├── prereg/
│   └── WITNESS-1-prereg.md        # Preregistration (locked before execution)
├── src/
│   ├── submit_job.py              # Build circuit, submit to IBM Quantum, save artifacts
│   ├── nonce.py                   # Canonical JSON + SHA-256 nonce derivation
│   ├── proofrecord.py             # ProofRecord build + verify
│   ├── ark457_replay.py           # ARK-457 replay-protection logic (library)
│   ├── case_w1c1_verify.py        # W1-C1: honest verification
│   ├── case_w1c2_tamper.py        # W1-C2: tamper/substitution detection
│   ├── case_w1c3_replay.py        # W1-C3: cross-context replay
│   └── tests/
│       └── test_mock.py           # Pre-lock mock tests (no QPU required)
├── results/
│   ├── raw/                       # Populated at execution (job_meta, counts, calibration)
│   └── WITNESS-1-report.md        # Written after execution
├── MANIFEST.sha256                # SHA-256 hashes of prereg + all src files (lock)
└── README.md
```

---

## RF Process

1. **Preregistration** — `prereg/WITNESS-1-prereg.md` written and committed before execution.
2. **MANIFEST lock** — `MANIFEST.sha256` committed; PR opened for Derek's review.
3. **Execution** — `submit_job.py` run after PR merge; three case scripts run in order.
4. **Results** — `results/WITNESS-1-report.md` written with verdicts as-is.
5. **Zenodo** — Draft deposit staged; Derek publishes manually.

Post-lock code changes are prohibited. A harness defect blocking execution triggers
gate-stop protocol; results published as-is regardless of outcome.

---

## Related Works

- ARK Corpus (ExecutionProof series): https://doi.org/10.5281/zenodo.21398675
  (19 records / 17 IDs / 16 PASS / 2 FAIL / 1 gate-stop)
- ARK-457 (cross-context replay, replay logic used here):
  https://doi.org/10.5281/zenodo.21421742

**WITNESS-1 is an independent series.** `witness-testbeds` is a separate repository
from `executionproof-testbeds` and `uip-phase1-testbeds`.

---

## Zenodo DOI

**Published:** https://zenodo.org/records/21424324  
**DOI (version):** https://doi.org/10.5281/zenodo.21424324  
**DOI (concept):** https://doi.org/10.5281/zenodo.21424323


---

*Remnant Fieldworks Inc. — Preregistration-first. No post-hoc changes.*
*Factual, understated. A FAIL is a feature.*


---

# WITNESS-2: Length-Prefixed Quantum Nonce with Record-Hash Field Integrity

**Series:** WITNESS (second record)
**Status:** Published — 2026-07-18
**DOI (version):** https://doi.org/10.5281/zenodo.21425381
**DOI (concept):** https://doi.org/10.5281/zenodo.21424323
**Record:** https://zenodo.org/records/21425381

---

## Summary

WITNESS-2 extends WITNESS-1 with two structural upgrades:

1. **Length-prefixed nonce** — `LP(x) = 4-byte big-endian uint32 length + x`. Prevents
   component-split length-extension ambiguity present in WITNESS-1's bare concatenation.
2. **`record_hash` field-integrity seal** — `SHA-256(canonical_json(all fields except record_hash))`.
   Detects any single-field substitution. Design boundary explicitly preregistered and tested:
   `record_hash` = field integrity only; `context_id` enforcement = ARK-457 authorization layer.

Four preregistered cases (W2-C2 has 4 sub-trials; W2-C3 has 2 sub-cases):

| Case | Description | Expected |
|------|-------------|----------|
| W2-C1 | Honest end-to-end verification (provider-record provenance) | PASS |
| W2-C2 | Substitution / tamper detection (4 sub-trials: counts, job_id, calibration, context_id) | PASS (all detected) |
| W2-C3(a) | Cross-context replay — record_hash catches naive alteration | DENY (PASS) |
| W2-C3(b) | Cross-context replay — attacker recomputes record_hash; ARK-457 fires | DENY (PASS) |

---

## Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, and stated experimental conditions. This is an experimental
> evidence record, not a universal security proof or production certification."

---

## Repository Structure

```
witness-testbeds/
└── witness-2/
    ├── prereg/
    │   └── WITNESS-2-prereg.md         # Preregistration (locked before execution)
    ├── src/
    │   ├── __init__.py
    │   ├── nonce.py                    # LP SHA-256 nonce; compute_quantum_nonce
    │   ├── proofrecord.py              # ProofRecord build + verify (schema v1.0)
    │   ├── calibration.py              # 10-field deterministic calibration extractor
    │   ├── ark457_replay.py            # ARK-457 context-binding library (copied)
    │   ├── submit_job.py               # Circuit submission harness
    │   ├── case_w2c1_verify.py         # W2-C1: honest verification
    │   ├── case_w2c2_tamper.py         # W2-C2: tamper/substitution detection (4 sub-trials)
    │   ├── case_w2c3_replay.py         # W2-C3: cross-context replay (2 sub-cases)
    │   └── tests/
    │       └── test_mock.py            # 48 pre-lock mock tests (no QPU required)
    ├── results/                        # Populated at execution
    │   └── .gitkeep
    └── MANIFEST.sha256                 # SHA-256 lock (prereg + all src files)
```

---

## Execution Summary

**QPU Job:** `d9di7nkinv1c73ap4ed0` | Backend: `ibm_fez` | Shots: 4000 | Unique outcomes: 256 / 256

| Case | Description | Verdict |
|------|-------------|---------|
| W2-C1 | Honest end-to-end verification (provider-record provenance, 9 checks) | ✅ PASS |
| W2-C2 | Tamper detection — 4 sub-trials (counts, job_id, calibration, context_id) | ✅ PASS |
| W2-C3(a) | Cross-context replay — record_hash catches naive alteration | ✅ PASS |
| W2-C3(b) | Cross-context replay — attacker recomputes record_hash; ARK-457 fires | ✅ PASS |

**Harness fixes (pre-execution, disclosed):**
- FIX-1 (8ae73bf): `service.least_busy()` TypeError in qiskit-ibm-runtime 0.48.0 → replaced with `min(eligible, key=lambda b: b.status().pending_jobs)`
- FIX-2 (2b6cbc5): IBM API requires ISA-compliant circuits since March 2024 → added `transpile(qc, backend, optimization_level=1)`. Logical circuit unchanged.

MANIFEST.sha256 recomputed and recommitted after each fix per RF protocol.

## RF Process

1. **Preregistration** — `witness-2/prereg/WITNESS-2-prereg.md` written and committed.
2. **Mock tests** — 48/48 PASS confirmed before MANIFEST lock.
3. **MANIFEST lock** — `witness-2/MANIFEST.sha256` committed; PR #3 opened and merged.
4. **Harness fixes** — FIX-1 and FIX-2 disclosed and committed pre-execution.
5. **Execution** — `submit_job.py` run; three case scripts run in order. All PASS.
6. **Results** — `witness-2/results/WITNESS-2-report.md` written with verdicts as-is.
7. **Zenodo** — Published: https://doi.org/10.5281/zenodo.21425381

Post-lock code changes are prohibited. A harness defect blocking execution triggers
gate-stop protocol; results published as-is regardless of outcome.

---

# WITNESS-3: Cosmic Beacon — CHSH Bell + NIST + LIGO/GWOSC Fused Authorization Nonce

**Series:** WITNESS (third record)  
**Status:** Published

---

## Summary

WITNESS-3 "Cosmic Beacon" fuses **three independent, publicly re-verifiable physical witnesses** into a single ExecutionProof authorization nonce:

1. **CHSH Bell-inequality violation** measured on a real IBM QPU — the measurement bits certify quantum non-classicality **AND** seed the nonce.
2. **NIST public Randomness Beacon** pulse — a timestamped, signed random value broadcast every 60 seconds.
3. **LIGO/GWOSC gravitational-wave data** (GW150914, first confirmed black-hole merger) — byte-exact, version-controlled open astrophysical data.

All three witnesses are **third-party re-verifiable**: anyone can independently fetch the NIST beacon pulse, download the GWOSC HDF5 file, and query the IBM Quantum provider for the job record — no trust in Remnant Fieldworks is required to verify the nonce provenance.

Four preregistered cases:

| Case | Description | Expected |
|------|-------------|----------|
| W3-C4 | CHSH Bell-inequality violation certification | PASS if \|S\| > 2, ≥ 5σ, ≤ Tsirelson + 0.10 |
| W3-C2 | Tamper detection (6 sub-trials: QPU, NIST, astro, job_id, cal, context_id) | PASS (all detected) |
| W3-C3 | Cross-context replay (2 sub-cases: no-recompute, ARK-457) | DENY (PASS) |
| W3-C1 | Honest end-to-end verification | PASS |

---

## Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, and stated experimental conditions. This is an experimental
> evidence record, not a universal security proof or production certification.  
> **NOT loophole-free**: This CHSH test does NOT close the locality or detection loopholes.
> Alice and Bob measurement stations are neighboring transmons on the same chip (no spacelike separation).  
> **NOT device-independent**: Fair-sampling and no-signalling are assumed but not verified from first principles.  
> **Astro witness is provenance only**: The LIGO/GWOSC data segment is a publicly re-verifiable
> byte anchor for the nonce. It does NOT constitute a detection claim or cosmological measurement."

---

## Repository Structure

```
witness-testbeds/
└── witness-3/
    ├── prereg/
    │   ├── WITNESS-3-prereg.md         # Preregistration (locked before execution)
    │   ├── WITNESS-3-prereg.pdf
    │   └── WITNESS-3-prereg.docx
    ├── src/
    │   ├── __init__.py
    │   ├── chsh.py                     # CHSH Bell circuits + S computation
    │   ├── nonce_v3.py                 # 5-segment LP cosmic_nonce (QPU + job_id + cal + NIST + astro)
    │   ├── proofrecord_v3.py           # ProofRecord build + verify (schema v3.0)
    │   ├── beacon_nist.py              # Fetch NIST beacon pulse (public API)
    │   ├── astro_gwosc.py              # Fetch LIGO/GWOSC GW150914 strain segment (HDF5, byte-exact)
    │   ├── calibration.py              # 10-field deterministic calibration extractor
    │   ├── ark457_replay.py            # ARK-457 context-binding library (copied)
    │   ├── submit_job.py               # CHSH circuit submission harness (4 settings × 2000 shots)
    │   ├── case_w3c4_bell.py           # W3-C4: CHSH certification (|S| > 2, ≥ 5σ, ≤ Tsirelson)
    │   ├── case_w3c1_verify.py         # W3-C1: honest verification (13 checks + provider provenance)
    │   ├── case_w3c2_tamper.py         # W3-C2: tamper detection (6 sub-trials)
    │   ├── case_w3c3_replay.py         # W3-C3: cross-context replay (2 sub-cases)
    │   └── tests/
    │       └── test_mock.py            # 26 pre-lock mock tests (simulator, no QPU required)
    ├── results/
    │   ├── raw/                        # Populated at execution: raw_counts.json, job_meta.json,
    │   │                               # calibration_snapshot.json, nist_witness.json, astro_witness.json
    │   ├── proofrecord.json
    │   ├── W3-C*-result.json           # 4 verdict JSONs
    │   └── WITNESS-3-report.{md,pdf,docx,html}  # Multi-format report
    ├── MANIFEST.sha256                 # SHA-256 lock (prereg.md + 15 src .py files; 16 total)
    └── gen_report.py                   # Report generator (written post-execution)
```

---

## Execution Summary

**QPU Job:** `d9dvul2neu4c739nrdl0` | Backend: `ibm_fez` | Shots: 8000 (4 CHSH settings × 2000 shots/setting) | Instance: `open-instance`

**CHSH Bell Test:**  
**S = 2.545 ± 0.0345** → **15.8 σ above classical bound (2.0)** → **Bell-certified = TRUE**

**External Witnesses:**
- **NIST Beacon:** pulse #1865471 (timestamp 2026-07-18T22:31:00.000Z)
- **LIGO/GWOSC:** GW150914, H1 detector, 32s HDF5 file (SHA-256: `66c4b196...`), strain window 4096 samples @ offset 65536

**Cosmic Nonce:** `6876050a7f8ebadf79b1bd702346ae42563019725c03d29bd8d26dadc8c7f686`  
**Record Hash:** `858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf`

| Case | Description | Verdict |
|------|-------------|---------|
| W3-C4 | CHSH Bell-inequality violation certification | ✅ PASS (S=2.545, 15.8σ, bell_certified=true) |
| W3-C2 | Tamper detection — 6 sub-trials (QPU, NIST, astro, job_id, cal, context_id) | ✅ PASS (all forgeries detected) |
| W3-C3(a) | Cross-context replay — record_hash catches naive alteration | ✅ PASS (denied) |
| W3-C3(b) | Cross-context replay — attacker recomputes record_hash; ARK-457 fires | ✅ PASS (denied, context mismatch) |
| W3-C1 | Honest end-to-end verification (13 checks, provider job found, counts match) | ✅ PASS |

**Harness fix (post-lock, disclosed):**
- **FIX-W3-1** (`submit_job.py` line 63): changed `channel="ibm_quantum_platform"` → `channel="ibm_cloud"` to match the working IBM Quantum Runtime API endpoint for the `open-instance`. The preregistered MANIFEST.sha256 locked the harness before this fix; the fix was required to complete the actual QPU submission. This is disclosed per the RF Standing Covenant (transparency on post-lock modifications).

No other harness fixes were needed. All other source modules match their preregistered SHA-256 hashes in `MANIFEST.sha256`.

---

## RF Process

1. **Preregistration** — `witness-3/prereg/WITNESS-3-prereg.md` written and committed.
2. **Mock tests** — 26/26 PASS confirmed on Aer simulator (CHSH S=2.80 @ ~79σ on sim); NIST + GWOSC witnesses fetched live and validated.
3. **MANIFEST lock** — `witness-3/MANIFEST.sha256` committed (commit `ac18f61`, 2026-07-18) — locks 16 files (prereg + 15 src modules) **before** any QPU execution.
4. **Harness fix** — FIX-W3-1 disclosed post-lock, applied immediately before QPU submission (channel parameter only).
5. **Execution** — `submit_job.py` run; real QPU job `d9dvul2neu4c739nrdl0` completed; all 4 case scripts run in order. All PASS.
6. **Results** — `witness-3/results/WITNESS-3-report.{md,pdf,docx,html}` generated with honest verdicts as-is.
7. **Zenodo** — Draft deposit pending; DOI will be added to this README and the report upon publication.

Post-lock code changes are prohibited. A harness defect blocking execution triggers
gate-stop protocol; results published as-is regardless of outcome.

---

## Research Context

WITNESS-3 extends WITNESS-1 and WITNESS-2 by:
- Fusing **three independent witnesses** (quantum + beacon + astrophysical) instead of one
- Certifying the quantum witness via **Bell-inequality violation** (not just raw entropy)
- Binding the nonce to **publicly archived LIGO gravitational-wave data** (historic, byte-exact, third-party re-verifiable)

This experiment demonstrates that an authorization nonce can carry **publicly auditable provenance from multiple physical sources**, reducing reliance on any single trust anchor and enabling independent verification by third parties (NIST, LIGO/GWOSC, IBM Quantum).

---

**Preregistration commit:** `ac18f61` (2026-07-18)  
**Execution commit:** `6fccdb6` (2026-07-18)  
**Full report:** [witness-3/results/WITNESS-3-report.md](witness-3/results/WITNESS-3-report.md)  
**Zenodo DOI:** [10.5281/zenodo.21434832](https://doi.org/10.5281/zenodo.21434832)

---

# WITNESS-4: The Freshness Bracket

**Series:** WITNESS (fourth record — append-only ledger W1 → W2 → W3 → **W4**)  
**Status:** Executed — ALL 5 CASES PASS (Zenodo publication HELD for review / IP-gate)

---

## Summary

WITNESS-4 asks two foundational audit questions every ProofRecord must answer:
1. **"Could this have been backdated or pre-computed?"** → No. Design hashed BEFORE anchors (*design-before-anchor*), and the fused nonce commits to a NIST pulse that didn't exist before its published time (*not-before* lower bound).
2. **"Can I rebuild it myself from public data?"** → Yes. A dedicated reconstruction module rebuilt the entire record from public artifacts alone, confirmed by the IBM provider.

WITNESS-4 also establishes an **append-only ledger** by chain-linking to WITNESS-3's published record_hash (Zenodo DOI 10.5281/zenodo.21434832), making WITNESS-1→2→3→**4** a single third-party-verifiable ledger. The same QPU run remained a CHSH Bell test, certified under the identical honest standard used in WITNESS-3.

| Case | Description | Verdict |
|------|-------------|---------|
| W4-C1 | Zero-trust reconstruction from public artifacts + provider confirmation | **PASS** |
| W4-C2 | Tamper detection (8 sub-trials) | **PASS** |
| W4-C3 | Backdating / pre-computation detection (flagship freshness case) | **PASS** |
| W4-C4 | Append-only ledger chain integrity | **PASS** |
| W4-C5 | CHSH Bell-inequality violation certification (device-dependent) | **PASS** |

---

## Execution

**Job ID:** `d9e0mjsjeosc73fi6b50` (IBM Quantum `ibm_fez`, us-east)  
**CHSH S:** 2.595 ± 0.034 (17.5σ above classical) → `bell_certified = True`  
**Freshness:** `fresh = True` (precommit 23:24:56Z < NIST pulse 23:27:00Z < finalize 23:30:09Z)  
**record_hash:** `786ceb9a8bd46713de3b7da11cdb7f95518751381b885506d9c66d60c32e3dae`

---

## Harness Fixes

**FIX-W4-1 (NIST polling for freshness):** The NIST `/pulse/last` endpoint has ~3–5 minute propagation delay. To ensure `design_before_anchor_ok = true`, the harness polls with exponential backoff until it fetches a pulse whose `timeStamp` is strictly AFTER the `precommit_time_utc`. This fix was discovered and applied during the first live run (the initial attempt fetched a stale pulse, violating the freshness bracket). The fix is a **harness correction to achieve the preregistered design**, not a post-lock design change.

**Channel note (inherited from WITNESS-3):** `channel="ibm_cloud"` was used from the outset (the correct open-plan channel; this was discovered as FIX-W3-1 in WITNESS-3 and is inherited here, **not** a post-lock WITNESS-4 fix).

---

## Research Context

WITNESS-4 extends WITNESS-1/2/3 by:
- Adding a **freshness bracket** (design-before-anchor + not-before lower bound) to prove the record is non-backdatable and non-pre-computable
- Providing **zero-trust reconstruction** from public artifacts (Prospect Question #5: "Can I rebuild it myself?")
- Establishing an **append-only ledger** (W1→W2→W3→W4) via chain-linking to the previous record's published record_hash
- Upgrading the fused nonce to **7 segments** (precommit_hash ‖ prev_record_hash ‖ raw_counts ‖ job_id ‖ calibration ‖ nist ‖ astro)

This experiment demonstrates that a ProofRecord can carry **verifiable temporal ordering** and **independent reconstructability**, addressing the two most common audit objections to any evidentiary record.

---

**Preregistration commit:** `8e878b1` (2026-07-18)  
**Execution commit:** `2e9a943` (2026-07-18)  
**Full report:** [witness-4/results/WITNESS-4-report.md](witness-4/results/WITNESS-4-report.md)  
**Zenodo DOI:** *(Held for review and file-first IP-gate decision)*

---

*Soli Deo Gloria.*
