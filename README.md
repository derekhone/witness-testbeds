# WITNESS-1: Quantum-Sourced Authorization Nonces with Verifiable Provenance

**Series:** WITNESS (first record)
**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Status:** Preregistered / Execution pending

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
