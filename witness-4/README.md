# WITNESS-4 — "The Freshness Bracket"

**Non-backdatable, independently-reconstructable, chain-linked quantum ProofRecord™.**
Fourth record in the WITNESS append-only ledger (W1 → W2 → W3 → **W4**), chained to
WITNESS-3's published record_hash (Zenodo DOI 10.5281/zenodo.21434832).

> Status: **EXECUTED — ALL 5 CASES PASS.**  
> Job `d9e0mjsjeosc73fi6b50`, S=2.595±0.034 (17.5σ), `fresh=True`, `bell_certified=True`.  
> Zenodo publication **HELD** for review and file-first IP-gate decision.

## What it adds over WITNESS-3

WITNESS-3 bound one nonce to three physical witnesses (QPU CHSH, NIST beacon, LIGO/GWOSC).
WITNESS-4 keeps all three and adds a **freshness bracket** and an **append-only ledger link**,
folded into a 7-segment fused nonce:

```
fused_nonce = SHA-256( LP(precommit_hash) ‖ LP(prev_record_hash) ‖ LP(raw_counts)
                       ‖ LP(job_id) ‖ LP(calibration) ‖ LP(nist) ‖ LP(astro) )
```

- **precommit_hash** — the full design (circuit + intent + context + prev link) hashed
  *before* any random anchor is known → *design-before-anchor*.
- **prev_record_hash** — link to the previous ledger record → append-only order.
- The nonce commits to a NIST beacon pulse that did not exist before its published time →
  a *not-before* lower time bound (non-backdatable).

## Freshness bracket

```
precommit_time_utc  <=  nist_pulse_time  <=  timestamp_utc (finalize)
```

**Honest bounds:** this is a *relative-ordering* / *not-before* proof only. It is **not** a
trusted timestamping authority or blockchain, asserts **no upper time bound**, and the CHSH
test is **not** loophole-free / device-independent. See the preregistration for the full
non-claims.

## Cases

| Case | What it proves | PASS criterion |
|------|----------------|----------------|
| W4-C1 | Zero-trust reconstruction from public artifacts + provider confirm | all reconstruction checks match, `fresh==True`, provider confirms job (GATE-STOP if provider unreachable) |
| W4-C2 | Tamper detection (8 sub-trials) | every single-element forgery detected |
| W4-C3 | Backdating / pre-computation detection (flagship) | backdate + pre-compute detected, honest record fresh |
| W4-C4 | Append-only ledger chain integrity | honest link verifies, broken link detected 3 ways, monotonic |
| W4-C5 | CHSH Bell violation (device-dependent) | \|S\|>2, ≥5σ, \|S\|≤2√2+0.10 |

## Layout

```
witness-4/
├── prereg/WITNESS-4-prereg.md (+ .pdf/.docx)   preregistration (locked before QPU)
├── MANIFEST.sha256                              integrity lock of prereg + all src
├── src/                                         v4 modules + 5 case scripts + mock tests
└── results/                                     (empty until the approved QPU run)
```

## Reproduce (offline, zero QPU)

```
python3 src/tests/test_mock.py     # 48 in-memory + simulator checks, zero QPU cost
```

## Harness Fixes

**FIX-W4-1 (NIST polling for freshness):** The NIST `/pulse/last` endpoint has ~3–5 minute propagation delay. To ensure `design_before_anchor_ok = true`, the harness polls with exponential backoff until it fetches a pulse whose `timeStamp` is strictly AFTER the `precommit_time_utc`. This fix was discovered and applied during the first live run (the initial attempt fetched a stale pulse, violating the freshness bracket). The fix is a **harness correction to achieve the preregistered design**, not a post-lock design change.

**Channel note (inherited from WITNESS-3):** `channel="ibm_cloud"` was used from the outset (the correct open-plan channel; this was discovered as FIX-W3-1 in WITNESS-3 and is inherited here, **not** a post-lock WITNESS-4 fix).

---

**Trademarks (common-law / pending):** Remnant Fieldworks™, ExecutionProof™, ProofRecord™,
Proof Before Power™, Verification Before Execution™.
