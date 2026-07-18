# WITNESS-4 Preregistration
## "The Freshness Bracket" — Non-Backdatable, Independently-Reconstructable, Chain-Linked Quantum ProofRecord

**Series:** WITNESS (fourth record — append-only ledger W1 → W2 → W3 → W4)
**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Preregistration lock date:** 2026-07-18 (UTC)
**Status:** PREREGISTERED — locked before QPU execution

---

## 0. One-paragraph summary

WITNESS-4 asks a narrow, high-value question that an auditor or independent reviewer would
actually raise about any ProofRecord™: *"Could this record have been backdated or
pre-computed, and can I rebuild it myself from public data alone?"* WITNESS-4 answers both
by constructing a **freshness bracket** around the record. First, the entire experimental
design (CHSH circuit spec, declared intent, context id, and the previous ledger link) is
written into a **pre-commitment document and hashed BEFORE any unpredictable public anchor
is fetched** — establishing *design-before-anchor*. Second, the fused nonce commits to a
**NIST public Randomness Beacon** pulse whose value did not exist before its published
pulse time — establishing a *not-before* lower time bound (the record could not have been
finalized earlier). Third, the record is **chain-linked to WITNESS-3's published
record_hash** (Zenodo DOI 10.5281/zenodo.21434832), making WITNESS-1..4 a single
append-only, third-party-verifiable ledger. Fourth, a dedicated reconstruction module
rebuilds the *entire* record — every hash, the fused nonce, the CHSH statistic, the
freshness bracket, and the record_hash — from the stored public artifacts alone, with zero
trust in any RF-private state. The same QPU run remains a CHSH Bell test, certified under
the identical honest standard used in WITNESS-3.

---

## 1. Claim (single, falsifiable)

A ProofRecord constructed with a length-prefixed **7-segment fused nonce** — binding a
pre-commitment hash, the previous ledger link, QPU CHSH counts, the provider job id, the
backend calibration, a NIST beacon pulse, and a byte-exact LIGO/GWOSC strain segment — can
be:

(a) **fully reconstructed** from the stored public artifacts alone by an independent party,
    with the provider job record confirming the QPU counts when the provider API is
    reachable (W4-C1);
(b) detected as tampered when **any single element** of any witness, the pre-commitment, or
    the ledger link is substituted (W4-C2);
(c) shown to be **non-backdatable and non-pre-computable** by re-evaluating the freshness
    bracket independently of the record's own stored freshness block (W4-C3);
(d) shown to be a sound **append-only ledger link** to WITNESS-3, with any broken link
    detected three independent ways (W4-C4); and
(e) accompanied by a **CHSH Bell-inequality violation** certified at ≥ 5σ above the
    classical bound on the tested backend (W4-C5),

under the tested construction, circuit, backend, qubits, calibration, and shot count.

---

## 2. Commercial motivation (why this record, for RF Inc.)

WITNESS-4 directly answers **Prospect Question #5** — *"Can an independent reviewer
reconstruct the decision from the ProofRecord?"* — with a machine that does exactly that,
offline, from public artifacts. It also answers the single most common audit/compliance
objection to any evidentiary record: **"How do I know it wasn't backdated or pre-computed
after the fact?"** By making the freshness bracket and the append-only ledger link part of
the nonce itself, WITNESS-4 strengthens the utility case for the **ProofRecord™** construction
and supports the record-integrity posture of the RF-100 program. This is a
provenance / freshness / ordering advance, not a new physics claim.

---

## 3. The freshness bracket (precise definition)

All timestamps are ISO-8601 UTC. The bracket is:

```
    precommit_time_utc   <=   nist_pulse_time   <=   timestamp_utc (finalize)
```

and the verifier checks three invariants:

1. **NOT-BEFORE bound** — `timestamp_utc >= nist_pulse_time`. The fused nonce commits to a
   NIST beacon `outputValue` that was not published before `nist_pulse_time`; a record
   claiming an effective time earlier than the pulse is a backdating forgery.
2. **DESIGN-BEFORE-ANCHOR** — `precommit_time_utc <= nist_pulse_time`. The pre-commitment
   (circuit + intent + context + prev link) was hashed before the beacon value was known; a
   `precommit_time` after the pulse would indicate the design could have been chosen with
   knowledge of the anchor (pre-computation).
3. **CHAIN MONOTONIC** (advisory) — `timestamp_utc >= previous ledger record's timestamp`.

---

## 4. Experimental cases and PASS criteria

### W4-C1 — Zero-trust independent reconstruction (+ provider confirmation)
Rebuild the entire record from the public artifacts (`raw_counts`, `calibration_snapshot`,
`nist_witness`, `astro_witness`, `precommit`) and compare to the stored ProofRecord.
**PASS:** every reconstruction check matches AND `freshness.fresh == True` AND the provider
API confirms the `job_id` and per-setting counts. **GATE-STOP** (not FAIL) if the provider
API is unreachable/unauthorized at verification time (the offline reconstruction still runs
and is reported).

### W4-C2 — Tamper detection (8 sub-trials)
Alter exactly one element and confirm detection: (a) raw_counts, (b) job_id, (c)
calibration, (d) NIST pulse, (e) astro file hash, (f) context_id without record_hash
recompute, (g) pre-commitment document, (h) previous ledger link.
**PASS:** all 8 forgeries detected.

### W4-C3 — Backdating / pre-computation detection (flagship)
Independently re-evaluate the freshness bracket from the record's timestamps (not the
stored freshness block). **PASS:** a backdated `timestamp_utc` (earlier than the pulse) is
detected, a pre-computed `precommit_time_utc` (later than the pulse) is detected, AND the
genuine record evaluates `fresh == True` (no false positive).

### W4-C4 — Append-only ledger chain integrity
Verify the link to WITNESS-3's published record_hash. **PASS:** the honest link verifies,
a broken link is detected three ways (chain-link check, fused-nonce mismatch, record_hash
mismatch), and the timestamps are monotonic.

### W4-C5 — CHSH Bell-inequality violation certification (device-dependent)
Identical criterion to WITNESS-3 W3-C4. **PASS (all must hold):** (1) |S| > 2; (2)
(|S| − 2)/σ_S ≥ 5.0; (3) |S| ≤ 2√2 + 0.10. **KILL condition:** |S| ≤ 2 → W4-C5 = FAIL,
`bell_certified = False`, published as-is; the fused nonce and freshness bracket remain
valid as provenance/freshness/ordering constructions regardless.

---

## 5. Fused nonce construction

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

`LP(x) = struct.pack('>I', len(x)) + x` (4-byte big-endian length prefix; boundary-collision
safe). `canonical_json` = sorted keys, compact separators, ASCII. No single input controls
the nonce, and the nonce is inseparable from both the pre-commitment and the previous
ledger link.

---

## 6. Preregistered non-claims (honesty bounds)

The following are stated in advance and will NOT be claimed regardless of outcome:

- **Not a trusted timestamping / notarization authority and not a blockchain.** The
  freshness bracket establishes a **relative ordering** — design fixed before anchor, record
  finalized at-or-after the anchor's published pulse time — and a **not-before lower time
  bound only.** There is **no upper time bound**: a record can always be finalized later.
- **Not a loophole-free or device-independent Bell test.** The two qubits are neighbouring
  transmons on one chip (locality/communication loophole open), outcomes use fair sampling
  (detection loophole open), and settings are fixed by the harness (freedom-of-choice
  loophole open). A violation is consistent with non-classical correlations on the tested
  device under no-signalling and fair-sampling assumptions; it is not a device-independent
  certification.
- **Astro data is provenance-only.** The LIGO/GWOSC segment binds a fixed, public,
  byte-exact artifact into the nonce; it contributes no physical randomness claim.
- **No min-entropy claim from any single source.** The nonce is a provenance / freshness /
  ordering construction, not an information-theoretic randomness extractor.
- **No legal, security-certification, production-readiness, or RF-100-certification claims.**
  All claims are bounded to the tested construction and conditions.
- **record_hash provides field integrity only;** cross-context authorization enforcement is
  delegated to the ARK-457 layer, unchanged from prior records.

---

## 7. Method summary (load-bearing step order)

1. Build and hash the **pre-commitment** (`precommit.json`, `precommit_hash`) — BEFORE any
   anchor is fetched.
2. Submit the CHSH Batch job to IBM Quantum (channel `ibm_cloud`, 4 settings, qubits 0 & 1,
   2000 shots/setting, transpile opt_level=1). Capture `raw_counts`, `calibration_snapshot`,
   `job_meta`.
3. **After** results return, fetch the NIST beacon pulse and the LIGO/GWOSC strain witness.
4. Compute the fused nonce, evaluate the freshness bracket, and build the v4 ProofRecord
   (schema `witness-proofrecord-4.0`), chain-linked to WITNESS-3's published record_hash.
5. Run W4-C1..C5 and record honest verdicts (PASS / FAIL / GATE-STOP).

Genesis ledger link (WITNESS-3 published record_hash):
`858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf`

---

## 8. Integrity lock

This preregistration and all `witness-4/src/*.py` source files are hashed into
`witness-4/MANIFEST.sha256` and committed **before** QPU execution. The QPU run is performed
only after this lock and only with the author's explicit approval.

**Trademarks (common-law / pending; not yet registered):** Remnant Fieldworks™,
ExecutionProof™, ProofRecord™, Proof Before Power™, Verification Before Execution™.
