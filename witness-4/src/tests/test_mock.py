"""
WITNESS-4 pre-lock mock tests. Zero QPU cost, zero network dependency.

Validates the FULL Freshness Bracket pipeline in memory, extending the WITNESS-3
Cosmic Beacon checks with the v4 additions:
  - CHSH circuits on the Aer simulator reproduce a Bell violation (|S| > 2, ~2.83 ideal),
  - pre-commitment hash is deterministic and design-before-anchor,
  - 7-segment fused nonce is deterministic and length-prefix sound,
  - v4 ProofRecord build + record_hash + fused_nonce verification,
  - freshness bracket: honest record is FRESH; backdated / design-after-anchor records
    are correctly flagged NOT fresh,
  - append-only chain link: honest link verifies, broken link is rejected (3-way),
  - tamper detection across all witnesses + precommit + prev-link,
  - Bell certification criteria (PASS on simulator, correct FAIL on classical fixture).

Run: python3 witness-4/src/tests/test_mock.py   (exit 0 = all pass)
"""

import copy
import hashlib
import math
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC))

import chsh
from nonce_v4 import (compute_fused_nonce, canonical_json, lp,
                      compute_raw_counts_hash, compute_calibration_hash,
                      compute_nist_hash, compute_astro_hash)
from precommit import build_precommit, compute_precommit_hash, verify_precommit_hash
from freshness import evaluate_freshness
from proofrecord_v4 import (build_proofrecord, verify_record_hash, verify_fused_nonce,
                            verify_chain_link)

PASSED = 0
FAILED = 0


def check(name, cond):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name}")


# ---------------------------------------------------------------- fixtures
GENESIS_PREV_HASH = "858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf"
PREV_TS = "2026-07-18T22:31:00Z"

# The freshness bracket timeline used by the honest fixtures:
#   precommit  <=  nist_pulse  <=  record_finalize
PRECOMMIT_TIME = "2026-07-18T23:40:00Z"
NIST_PULSE_TIME = "2026-07-18T23:45:00.000Z"
RECORD_TIME = "2026-07-18T23:50:00Z"


def simulate_chsh(shots=20000):
    from qiskit_aer import AerSimulator
    from qiskit import transpile
    sim = AerSimulator(seed_simulator=1234)
    counts_by_setting = {}
    for label, qc in chsh.build_chsh_circuits(0, 1):
        tqc = transpile(qc, sim)
        res = sim.run(tqc, shots=shots).result()
        counts = {k.replace(" ", ""): int(v) for k, v in res.get_counts().items()}
        counts_by_setting[label] = counts
    return counts_by_setting


def stub_circuit_spec():
    return {
        "bell_state": "phi_plus", "qubits": [0, 1], "shots": 2000,
        "angles": {"a": chsh.ALICE_ANGLES["a"], "a_prime": chsh.ALICE_ANGLES["a_prime"],
                   "b": chsh.BOB_ANGLES["b"], "b_prime": chsh.BOB_ANGLES["b_prime"]},
        "settings_order": [s[0] for s in chsh.SETTINGS],
    }


def stub_precommit():
    return build_precommit(
        circuit_spec=stub_circuit_spec(),
        intent="WITNESS-4 freshness-bracket authorization nonce",
        context_id="witness-4-freshness-bracket",
        prev_record_hash=GENESIS_PREV_HASH,
        precommit_time_utc=PRECOMMIT_TIME,
    )


def stub_nist():
    return {
        "source": "nist_randomness_beacon_v2", "uri": "https://beacon.nist.gov/beacon/2.0/pulse/1",
        "version": "Version 2.0", "chainIndex": 1, "pulseIndex": 1234567,
        "timeStamp": NIST_PULSE_TIME,
        "outputValue": "A" * 128, "certificateId": "c" * 64,
        "signatureValue_sha256": "d" * 64, "signatureValue_prefix": "e" * 32,
        "raw_pulse_sha256": "f" * 64,
    }


def stub_astro():
    return {
        "source": "ligo_gwosc_open_data", "event": "GW150914", "detector": "H1",
        "gps_start": 1126259446, "duration_s": 32, "sample_rate_hz": 4096,
        "reference": "Abbott et al., PRL 116, 061102 (2016)",
        "url": "https://gwosc.org/s/events/GW150914/H-H1_LOSC_4_V1-1126259446-32.hdf5",
        "file_size_bytes": 1036463, "file_sha256": "1" * 64,
        "strain_sample": {"method": "hdf5_strain_window", "sample_offset": 65536,
                          "sample_count": 4096, "quantize_step": 1e-24,
                          "n_total_samples": 131072, "strain_window_sha256": "2" * 64},
    }


def stub_cal():
    return {"backend_name": "aer_sim", "backend_version": "0", "last_update_utc": None,
            "basis_gates": ["cx", "h", "measure", "ry"], "selected_qubits": [0, 1],
            "readout_error_by_qubit": {"0": 0.01, "1": 0.02},
            "t1_by_qubit": {"0": 1e-4, "1": 1.1e-4}, "t2_by_qubit": {"0": 8e-5, "1": 9e-5},
            "gate_error_for_used_gates": {"h_q0": 1e-4}, "gate_length_for_used_gates": {"h_q0": 3e-8}}


# ---------------------------------------------------------------- tests
def test_lp_and_canonical():
    print("[1] length-prefix + canonical JSON (7-segment)")
    check("lp adds 4-byte prefix", lp(b"abc") == b"\x00\x00\x00\x03abc")
    check("canonical sorts keys", canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}')
    # boundary-collision resistance between adjacent segments
    n1 = compute_fused_nonce("ph", "pv", {"x": 1}, "job", {}, {}, {})
    n2 = compute_fused_nonce("ph", "pv", {}, "x1job", {}, {}, {})
    check("length-prefix prevents boundary collision", n1 != n2)
    # precommit_hash vs prev_record_hash boundary
    n3 = compute_fused_nonce("phpv", "", {}, "j", {}, {}, {})
    n4 = compute_fused_nonce("ph", "pv", {}, "j", {}, {}, {})
    check("precommit/prev boundary distinct", n3 != n4)
    check("nonce is 64-hex", len(n1) == 64 and all(c in "0123456789abcdef" for c in n1))


def test_precommit():
    print("[2] pre-commitment hash determinism + independence")
    pc = stub_precommit()
    h1 = compute_precommit_hash(pc)
    h2 = compute_precommit_hash(copy.deepcopy(pc))
    check("precommit hash deterministic", h1 == h2)
    check("precommit hash is 64-hex", len(h1) == 64)
    check("verify_precommit_hash honest", verify_precommit_hash(pc, h1))
    pc2 = copy.deepcopy(pc); pc2["intent"] += "_CHANGED"
    check("changed intent -> different hash", compute_precommit_hash(pc2) != h1)
    check("verify rejects tampered precommit", not verify_precommit_hash(pc2, h1))
    return pc, h1


def test_chsh_violation():
    print("[3] CHSH Bell violation on simulator")
    cbs = simulate_chsh()
    r = chsh.compute_chsh(cbs)
    print(f"      S = {r['S']:.4f} +/- {r['sigma_S']:.4f}  (|S|={r['abs_S']:.4f}, "
          f"{r['sigmas_above_classical']:.1f} sigma over 2)")
    check("|S| > classical bound 2", r["abs_S"] > 2.0)
    check("|S| near Tsirelson 2.828 (within 0.15)", abs(r["abs_S"] - 2.0 * math.sqrt(2)) < 0.15)
    check("violation is > 5 sigma", r["sigmas_above_classical"] >= 5.0)
    check("|S| <= Tsirelson + tolerance", r["abs_S"] <= 2.0 * math.sqrt(2) + 0.10)
    check("four correlators present", len(r["correlators"]) == 4)
    return cbs, r


def test_no_violation_fixture():
    print("[4] classical fixture must NOT certify (kill-condition sanity)")
    flat = {"00": 5000, "01": 5000, "10": 5000, "11": 5000}
    cbs = {lab: dict(flat) for lab, _a, _b, _s in chsh.SETTINGS}
    r = chsh.compute_chsh(cbs)
    check("classical |S| <= 2", r["abs_S"] <= 2.0)
    check("classical fixture not >5sigma over 2", not (r["sigmas_above_classical"] >= 5.0))


def test_freshness_bracket():
    print("[5] freshness bracket: honest FRESH; backdate / design-after-anchor caught")
    ok = evaluate_freshness(RECORD_TIME, NIST_PULSE_TIME, PRECOMMIT_TIME, PREV_TS)
    check("honest record: not_before_bound_ok", ok["not_before_bound_ok"])
    check("honest record: design_before_anchor_ok", ok["design_before_anchor_ok"])
    check("honest record: chain_monotonic_ok", ok["chain_monotonic_ok"])
    check("honest record: fresh == True", ok["fresh"])
    # backdated: record claims a finalize time BEFORE the beacon pulse
    bad = evaluate_freshness("2026-07-18T23:00:00Z", NIST_PULSE_TIME, PRECOMMIT_TIME, PREV_TS)
    check("backdated record: not_before FAILS", not bad["not_before_bound_ok"])
    check("backdated record: fresh == False", not bad["fresh"])
    # design-after-anchor: precommit claimed AFTER the pulse (pre-computation forgery)
    daa = evaluate_freshness(RECORD_TIME, NIST_PULSE_TIME, "2026-07-18T23:46:00Z", PREV_TS)
    check("design-after-anchor: design_before FAILS", not daa["design_before_anchor_ok"])
    check("design-after-anchor: fresh == False", not daa["fresh"])
    # non-monotonic chain: record older than previous ledger entry
    nm = evaluate_freshness(RECORD_TIME, NIST_PULSE_TIME, PRECOMMIT_TIME, "2026-07-19T00:00:00Z")
    check("non-monotonic chain: chain_monotonic FAILS", not nm["chain_monotonic_ok"])
    check("non-monotonic chain: fresh == False", not nm["fresh"])


def test_proofrecord_and_verify(cbs, r, precommit, precommit_hash):
    print("[6] v4 ProofRecord build + honest verification + freshness embed")
    nist, astro, cal = stub_nist(), stub_astro(), stub_cal()
    job_id = "mock_job_0001"
    nonce = compute_fused_nonce(precommit_hash, GENESIS_PREV_HASH, cbs, job_id, cal, nist, astro)
    pr = build_proofrecord(
        fused_nonce=nonce, precommit_hash=precommit_hash, prev_record_hash=GENESIS_PREV_HASH,
        job_id=job_id, backend="aer_sim", provider_instance="mock-crn",
        calibration_hash=compute_calibration_hash(cal), raw_counts_hash=compute_raw_counts_hash(cbs),
        nist_hash=compute_nist_hash(nist), astro_hash=compute_astro_hash(astro),
        chsh_result=r, bell_certified=True, context_id="witness-4-freshness-bracket",
        nist_pulse_time=NIST_PULSE_TIME, precommit_time_utc=PRECOMMIT_TIME,
        timestamp_utc=RECORD_TIME, prev_record_timestamp_utc=PREV_TS)
    check("record_hash verifies", verify_record_hash(pr))
    check("fused_nonce verifies", verify_fused_nonce(pr, cbs, cal, nist, astro))
    check("schema is 4.0", pr["schema_version"] == "witness-proofrecord-4.0")
    check("precommit_hash stored", pr["precommit_hash"] == precommit_hash)
    check("prev_record_hash stored", pr["prev_record_hash"] == GENESIS_PREV_HASH)
    check("freshness block embedded + fresh", pr["freshness"]["fresh"])
    check("chsh S stored in record", abs(pr["chsh"]["S"] - r["S"]) < 1e-9)
    return pr, nist, astro, cal


def test_tamper(pr, cbs, cal, nist, astro, precommit):
    print("[7] tamper detection across witnesses + precommit + prev-link (8 sub-trials)")
    # (a) raw_counts
    rc = copy.deepcopy(cbs); lab0 = sorted(rc)[0]; ks = sorted(rc[lab0]); rc[lab0][ks[0]] += 1
    check("a raw_counts tamper detected", not verify_fused_nonce(pr, rc, cal, nist, astro))
    # (b) job_id
    pb = copy.deepcopy(pr); pb["job_id"] += "_FORGED"
    check("b job_id tamper -> nonce", not verify_fused_nonce(pb, cbs, cal, nist, astro))
    check("b job_id tamper -> record_hash", not verify_record_hash(pb))
    # (c) calibration
    calc = copy.deepcopy(cal); calc["readout_error_by_qubit"]["0"] += 0.05
    check("c calibration tamper detected", not verify_fused_nonce(pr, cbs, calc, nist, astro))
    # (d) nist
    nd = copy.deepcopy(nist); nd["outputValue"] = "B" + nd["outputValue"][1:]
    check("d nist tamper detected", not verify_fused_nonce(pr, cbs, cal, nd, astro))
    # (e) astro
    ae = copy.deepcopy(astro); ae["file_sha256"] = "0" + ae["file_sha256"][1:]
    check("e astro tamper detected", not verify_fused_nonce(pr, cbs, cal, nist, ae))
    # (f) context_id without recompute
    pf = copy.deepcopy(pr); pf["context_id"] += "_FORGED"
    check("f context_id tamper -> record_hash", not verify_record_hash(pf))
    # (g) precommit_hash tamper
    pg = copy.deepcopy(pr); pg["precommit_hash"] = "0" + pg["precommit_hash"][1:]
    check("g precommit_hash tamper -> nonce", not verify_fused_nonce(pg, cbs, cal, nist, astro))
    check("g precommit_hash tamper -> record_hash", not verify_record_hash(pg))
    # (h) prev_record_hash tamper
    ph = copy.deepcopy(pr); ph["prev_record_hash"] = "0" + ph["prev_record_hash"][1:]
    check("h prev_record_hash tamper -> nonce", not verify_fused_nonce(ph, cbs, cal, nist, astro))
    check("h prev_record_hash tamper -> record_hash", not verify_record_hash(ph))


def test_chain_link(pr):
    print("[8] append-only chain link (3-way)")
    # honest: a synthetic previous record whose record_hash == GENESIS_PREV_HASH
    prev = {"record_hash": GENESIS_PREV_HASH}
    check("honest link verifies", verify_chain_link(pr, prev))
    # broken: previous record hash differs
    broken = {"record_hash": "9" * 64}
    check("broken link rejected", not verify_chain_link(pr, broken))
    # missing: no previous record
    check("missing prev rejected", not verify_chain_link(pr, None))


def main():
    print("=" * 64)
    print("WITNESS-4 mock test suite (simulator + in-memory, zero QPU)")
    print("=" * 64)
    test_lp_and_canonical()
    precommit, precommit_hash = test_precommit()
    cbs, r = test_chsh_violation()
    test_no_violation_fixture()
    test_freshness_bracket()
    pr, nist, astro, cal = test_proofrecord_and_verify(cbs, r, precommit, precommit_hash)
    test_tamper(pr, cbs, cal, nist, astro, precommit)
    test_chain_link(pr)
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
