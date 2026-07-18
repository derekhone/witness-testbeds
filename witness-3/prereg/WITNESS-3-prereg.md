# WITNESS-3 Preregistration
## "Cosmic Beacon" — Bell-Certified, Universe-Witnessed Authorization Nonce

**Series:** WITNESS (third record)
**Author:** Derek Adam Hone / Remnant Fieldworks Inc.
**Preregistration lock date:** 2026-07-18 (UTC)
**Status:** PREREGISTERED — locked before QPU execution

---

## 0. One-paragraph summary

WITNESS-3 binds a single ExecutionProof authorization nonce to **three independent,
publicly re-verifiable physical witnesses**: (1) a **CHSH Bell-test** measured on IBM
quantum hardware, (2) a pulse from the **NIST public Randomness Beacon**, and (3) a
byte-exact segment of **LIGO/GWOSC open gravitational-wave data** from GW150914 — the
first direct detection of gravitational waves, the merger of two black holes ~1.3 billion
light-years away. The same QPU measurement that seeds the nonce is a Bell test, so the run
also certifies (device-dependently, with all loopholes disclosed) that the quantum
correlations violate the classical bound |S| ≤ 2. To our knowledge this is the first
authorization ProofRecord whose freshness is jointly witnessed by a Bell-inequality
violation, a national metrology beacon, and real astrophysical detector data — every byte
of which any third party can independently re-download and re-hash.

---

## 1. Claim (single, falsifiable)

A ProofRecord constructed with a length-prefixed **fused "cosmic" nonce** over three
independent witnesses (QPU CHSH counts, NIST beacon pulse, LIGO/GWOSC strain file) can be:

(a) verified end-to-end against all three witness sources and the provider job record (W3-C1),
(b) detected as tampered when **any single element of any witness** is substituted (W3-C2),
(c) rejected as a cross-context replay by the two-layer (record_hash + ARK-457) defence (W3-C3), and
(d) accompanied by a **CHSH Bell-inequality violation** certified at ≥ 5σ above the
    classical bound on the tested backend (W3-C4),

under the tested construction, circuit, backend, qubits, calibration, and shot count.

---

## 2. Non-Claims (explicit — these protect the credibility of the claim)

- **NOT a loophole-free / device-independent Bell test.** The two qubits are neighbouring
  transmons on a single chip: there is **no space-like separation** (locality /
  communication loophole open), readout assumes **fair sampling** (detection loophole
  open), and measurement settings are fixed by the harness (freedom-of-choice loophole
  open). A violation here is consistent with non-classical correlations on the tested
  device under no-signalling and fair-sampling assumptions. It is **not** a device-
  independent randomness certification in the loophole-free sense.
- **Does NOT detect gravitational waves and makes NO cosmological claim.** The LIGO/GWOSC
  strain file is used purely as a **public, re-verifiable provenance witness** — real,
  published detector bytes that anyone can re-download and hash. WITNESS-3 does not
  re-derive any astrophysical parameter.
- **Does NOT re-run NIST's signature chain.** The beacon pulse's signature and certificate
  id are recorded so any auditor can verify them against NIST's published certificate.
- **Does NOT prove quantum randomness superiority, universal security, production
  readiness, or RF-100 conformance.** Results apply only within the tested conditions.
- `record_hash` is a **field-integrity seal, not a context-binding mechanism** (see §7,
  W3-C3(b)); context enforcement is delegated to the ARK-457 authorization layer.
- The fused nonce is a **provenance / freshness construction**, not a claim of
  information-theoretic min-entropy from any single witness.

---

## 3. CHSH Circuit & Measurement Specification

- **State:** Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2 via H on Alice + CNOT(Alice→Bob).
- **Qubits:** 2 logical (Alice = q0, Bob = q1); physical mapping by transpiler.
- **Settings (preregistered optimal angles for |Φ+⟩, where E(α,β) = cos(α−β)):**
  - Alice: a = 0, a′ = π/2
  - Bob:   b = π/4, b′ = 3π/4
- **Four measurement circuits** (one per setting pair), in fixed order:
  `ab (+E)`, `abp (−E)`, `apb (+E)`, `apbp (+E)`.
- **Measurement realisation:** to measure cos(θ)Z + sin(θ)X, append `ry(−θ)` then measure
  in the Z basis. Sign convention validated on the Aer simulator (must reproduce S ≈ +2.83).
- **CHSH statistic:** S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′). Classical bound |S| ≤ 2;
  Tsirelson bound |S| ≤ 2√2 ≈ 2.8284.
- **Correlator:** E = [N(00) + N(11) − N(01) − N(10)] / N_total.
- **Shots:** 2,000 per setting (8,000 total), one Batch job.
- **Channel:** `ibm_quantum_platform`. **Execution mode:** Batch.
- **Backend selection:** operational, non-simulator, ≥ 2 qubits, open-plan accessible;
  minimum pending jobs among {ibm_fez, ibm_marrakesh, ibm_kingston}. Name, calibration
  snapshot, timestamps, job id, and provider instance recorded in `results/raw/`.
- **QPU budget gate:** `usage_remaining_seconds ≥ 20`, else GATE-STOP (do not purchase time).
- **Provider/network unavailability at any fetch or verification step:** GATE-STOP, not FAIL.

---

## 4. Witness Sources (all publicly re-verifiable)

### 4.1 QPU witness
Raw per-setting counts from the CHSH job + job_id + 10-field deterministic calibration
snapshot (schema identical to WITNESS-2 `calibration.py`).

### 4.2 NIST witness (`beacon_nist.py`)
One pulse from the NIST Randomness Beacon v2 (`/beacon/2.0/pulse/last`), fetched at
execution time. Recorded fields: uri, version, chainIndex, pulseIndex, timeStamp,
outputValue, certificateId, signatureValue (sha256 + 32-char prefix), and the sha256 of
the exact raw pulse bytes.

### 4.3 Astro witness (`astro_gwosc.py`)
The public GWOSC strain file for GW150914 (H1, 32 s, 4096 Hz;
`https://gwosc.org/s/events/GW150914/H-H1_LOSC_4_V1-1126259446-32.hdf5`). Recorded:
url, file size, **SHA-256 of the exact file bytes**, event/detector/GPS/duration/sample-rate,
and a deterministic digest over a fixed strain-sample window (offset 65536, 4096 samples,
quantised at 1e-24) so the record binds to the actual physical strain time-series.

---

## 5. Fused Nonce Construction (length-prefixed, 5 segments)

```
LP(x) = struct.pack('>I', len(x)) + x        (4-byte big-endian uint32 length prefix)

cosmic_nonce = SHA-256(
    LP(canonical_json(raw_counts))            # per-setting CHSH counts
  ‖ LP(job_id)
  ‖ LP(canonical_json(calibration_snapshot))
  ‖ LP(canonical_json(nist_beacon_record))
  ‖ LP(canonical_json(astro_witness_record))
)
```

`canonical_json = json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=True)`.
Length prefixing prevents boundary-collision across the five segments. Result: 64-char
lowercase hex. Each witness also carries an independent SHA-256 (`raw_counts_hash`,
`calibration_hash`, `nist_hash`, `astro_hash`).

---

## 6. ProofRecord Schema (`witness-proofrecord-3.0`)

```json
{
  "schema_version":    "witness-proofrecord-3.0",
  "cosmic_nonce":      "<64-hex fused nonce>",
  "job_id":            "<IBM Quantum job id>",
  "backend":           "<backend name>",
  "provider_instance": "<CRN / provider instance>",
  "calibration_hash":  "<sha256>",
  "raw_counts_hash":   "<sha256>",
  "nist_hash":         "<sha256>",
  "astro_hash":        "<sha256>",
  "chsh":              { "S", "abs_S", "sigma_S", "classical_bound",
                         "tsirelson_bound", "sigmas_above_classical", "correlators" },
  "bell_certified":    true,
  "context_id":        "witness-3-cosmic-beacon",
  "timestamp_utc":     "<ISO-8601 UTC, second precision>",
  "record_hash":       "<sha256 of canonical_json(all fields above)>"
}
```

`record_hash` provides field integrity only; it cannot enforce `context_id` binding
(tested in W3-C3(b)).

---

## 7. Preregistered Test Cases & Pass/Fail Criteria

### W3-C1 — Honest End-to-End Verification
Recompute cosmic_nonce from all three stored witnesses; verify record_hash and every
per-witness hash; re-derive CHSH S from stored counts; via the IBM provider API confirm
the job id exists and per-setting counts match. **PASS:** all local checks True AND
provider job found AND counts match. Provider/network/token unavailability → **GATE-STOP**.

### W3-C2 — Tamper Detection (6 sub-trials)
Alter exactly one element per sub-trial and confirm detection:
(a) raw_counts, (b) job_id [nonce + record_hash], (c) calibration, (d) NIST outputValue,
(e) astro file_sha256, (f) context_id without record_hash recompute [record_hash].
**PASS:** all 6 forgeries detected.

### W3-C3 — Cross-Context Replay (2 sub-cases)
(a) change context_id without recomputing record_hash → record_hash denies.
(b) change context_id and recompute record_hash (valid seal — design boundary) → ARK-457
5-dimensional context binding denies (session mismatch). **PASS:** both replays DENIED.

### W3-C4 — CHSH Bell-Violation Certification (flagship)
Compute S from stored counts. **PASS iff ALL:** (1) |S| > 2; (2) (|S|−2)/σ_S ≥ 5.0;
(3) |S| ≤ 2√2 + 0.10. **KILL condition:** if |S| ≤ 2 → W3-C4 = FAIL, `bell_certified =
false`, published as-is (the fused nonce remains valid as a provenance construction; only
the non-classicality certification fails). σ_S from Var(E) = (1−E²)/N summed over the four
independent correlators.

---

## 8. Overall Verdict Rule

PASS iff all four cases (W3-C1..C4) meet their stated criteria and every sub-trial/sub-case
within each meets its criterion. Any single failure = overall FAIL, published as-is with
full root-cause analysis. GATE-STOP (provider/network/budget) is neither PASS nor FAIL and
is logged with reason; the experiment may be re-run once conditions permit, without editing
locked code.

---

## 9. Related Works

- ARK Corpus (ExecutionProof) concept DOI: 10.5281/zenodo.21398675
- ARK-457 (cross-context replay; library reused here): DOI 10.5281/zenodo.21421742
- WITNESS-1: DOI 10.5281/zenodo.21424324 · WITNESS-2: DOI 10.5281/zenodo.21425381
- WITNESS series concept DOI: 10.5281/zenodo.21424323
- BELLWETHER series (CHSH Bell-violation entropy witness): prior RF quantum series —
  WITNESS-3 differs by **fusing** the Bell test with NIST + astrophysical witnesses in a
  single authorization ProofRecord.
- NIST Randomness Beacon: NIST IR 8213; https://beacon.nist.gov/
- GW150914: B. P. Abbott et al. (LIGO/Virgo), Phys. Rev. Lett. 116, 061102 (2016);
  data via GWOSC, https://gwosc.org/

---

## 10. Mandatory Scope Disclaimer

> "Results apply within the tested circuit model, backend, qubits, calibration, shot
> counts, software harnesses, witness sources, and stated experimental conditions. The
> Bell-violation certification is device-dependent and not loophole-free. The astrophysical
> data is used only as a public provenance witness, not as a detection or cosmological
> claim. This is an experimental evidence record, not a universal security proof or
> production certification."

Reproduced verbatim in the README and Zenodo deposit description.

---

## 11. MANIFEST Lock Reference

`witness-3/MANIFEST.sha256` covers this preregistration document and all files under
`witness-3/src/`. It is committed before any QPU job is submitted. Post-lock code changes
are prohibited; any pre-execution harness defect triggers the gate-stop protocol and a
disclosed, re-hashed fix consistent with WITNESS-1/2 precedent.

---

*Remnant Fieldworks RF Process. Preregistration-first. No post-hoc changes. Soli Deo Gloria.*
