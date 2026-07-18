# WITNESS Series — Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Repository:** `witness-testbeds` — independent of `executionproof-testbeds` and `uip-phase1-testbeds`

| Record | Title | Status | DOI |
|--------|-------|--------|-----|
| WITNESS-1 | Quantum-Sourced Nonces with Verifiable Provenance | Published | [10.5281/zenodo.21424324](https://doi.org/10.5281/zenodo.21424324) |
| WITNESS-2 | Length-Prefixed Quantum Nonce with Record-Hash Field Integrity | Published | [10.5281/zenodo.21425381](https://doi.org/10.5281/zenodo.21425381) |

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
