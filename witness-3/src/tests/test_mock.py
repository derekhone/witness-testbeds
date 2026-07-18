"""
WITNESS-3 pre-lock mock tests. Zero QPU cost, zero network dependency.

Validates the FULL Cosmic Beacon pipeline in memory:
  - CHSH circuits on the Aer simulator reproduce a Bell violation (|S| > 2, ~2.83 ideal),
  - the sign convention is correct,
  - fused cosmic_nonce is deterministic and length-prefix sound,
  - ProofRecord build + record_hash + cosmic_nonce verification,
  - tamper detection across all three witnesses (6 sub-trials),
  - cross-context replay two-layer defence (2 sub-cases),
  - Bell certification criteria (PASS on simulator, and correct FAIL on a classical/no-violation fixture).

Run: python3 witness-3/src/tests/test_mock.py   (exit 0 = all pass)
"""

import copy
import hashlib
import math
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC))

import chsh
from nonce_v3 import (compute_cosmic_nonce, canonical_json, lp,
                      compute_raw_counts_hash, compute_calibration_hash,
                      compute_nist_hash, compute_astro_hash)
from proofrecord_v3 import (build_proofrecord, verify_record_hash, verify_cosmic_nonce)
from ark457_replay import AuthContext, check_context_replay

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
def simulate_chsh(shots=20000):
    """Run the 4 CHSH circuits on the Aer simulator; return counts_by_setting."""
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


def stub_nist():
    return {
        "source": "nist_randomness_beacon_v2", "uri": "https://beacon.nist.gov/beacon/2.0/pulse/1",
        "version": "Version 2.0", "chainIndex": 1, "pulseIndex": 1234567,
        "timeStamp": "2026-07-18T22:13:00.000Z",
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
    print("[1] length-prefix + canonical JSON")
    check("lp adds 4-byte prefix", lp(b"abc") == b"\x00\x00\x00\x03abc")
    check("canonical sorts keys", canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}')
    # boundary-collision resistance: two different splits must differ
    n1 = compute_cosmic_nonce({"x": 1}, "job", {}, {}, {})
    n2 = compute_cosmic_nonce({}, "x1job", {}, {}, {})
    check("length-prefix prevents boundary collision", n1 != n2)
    check("nonce is 64-hex", len(n1) == 64 and all(c in "0123456789abcdef" for c in n1))


def test_chsh_violation():
    print("[2] CHSH Bell violation on simulator")
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
    print("[3] classical fixture must NOT certify (kill-condition sanity)")
    # perfectly uncorrelated counts -> E ~ 0 for every setting -> S ~ 0
    flat = {"00": 5000, "01": 5000, "10": 5000, "11": 5000}
    cbs = {lab: dict(flat) for lab, _a, _b, _s in chsh.SETTINGS}
    r = chsh.compute_chsh(cbs)
    check("classical |S| <= 2", r["abs_S"] <= 2.0)
    check("classical fixture not >5sigma over 2", not (r["sigmas_above_classical"] >= 5.0))


def test_proofrecord_and_verify(cbs, r):
    print("[4] ProofRecord build + honest verification")
    nist, astro, cal = stub_nist(), stub_astro(), stub_cal()
    job_id = "mock_job_0001"
    nonce = compute_cosmic_nonce(cbs, job_id, cal, nist, astro)
    pr = build_proofrecord(
        cosmic_nonce=nonce, job_id=job_id, backend="aer_sim",
        provider_instance="mock-crn", calibration_hash=compute_calibration_hash(cal),
        raw_counts_hash=compute_raw_counts_hash(cbs), nist_hash=compute_nist_hash(nist),
        astro_hash=compute_astro_hash(astro), chsh_result=r, bell_certified=True,
        context_id="witness-3-cosmic-beacon", timestamp_utc="2026-07-18T22:20:00Z")
    check("record_hash verifies", verify_record_hash(pr))
    check("cosmic_nonce verifies", verify_cosmic_nonce(pr, cbs, cal, nist, astro))
    check("schema is 3.0", pr["schema_version"] == "witness-proofrecord-3.0")
    check("all 3 witness hashes present",
          all(pr.get(k) for k in ["raw_counts_hash", "nist_hash", "astro_hash"]))
    check("chsh S stored in record", abs(pr["chsh"]["S"] - r["S"]) < 1e-9)
    return pr, nist, astro, cal


def test_tamper(pr, cbs, cal, nist, astro):
    print("[5] tamper detection across all 3 witnesses (6 sub-trials)")
    # (a) raw_counts
    rc = copy.deepcopy(cbs); lab0 = sorted(rc)[0]; ks = sorted(rc[lab0]); rc[lab0][ks[0]] += 1
    check("a raw_counts tamper detected", not verify_cosmic_nonce(pr, rc, cal, nist, astro))
    # (b) job_id
    pb = copy.deepcopy(pr); pb["job_id"] += "_FORGED"
    check("b job_id tamper -> nonce", not verify_cosmic_nonce(pb, cbs, cal, nist, astro))
    check("b job_id tamper -> record_hash", not verify_record_hash(pb))
    # (c) calibration
    calc = copy.deepcopy(cal); calc["readout_error_by_qubit"]["0"] += 0.05
    check("c calibration tamper detected", not verify_cosmic_nonce(pr, cbs, calc, nist, astro))
    # (d) nist
    nd = copy.deepcopy(nist); nd["outputValue"] = "B" + nd["outputValue"][1:]
    check("d nist tamper detected", not verify_cosmic_nonce(pr, cbs, cal, nd, astro))
    # (e) astro
    ae = copy.deepcopy(astro); ae["file_sha256"] = "0" + ae["file_sha256"][1:]
    check("e astro tamper detected", not verify_cosmic_nonce(pr, cbs, cal, nist, ae))
    # (f) context_id without recompute
    pf = copy.deepcopy(pr); pf["context_id"] += "_FORGED"
    check("f context_id tamper -> record_hash", not verify_record_hash(pf))


def test_replay(pr):
    print("[6] cross-context replay two-layer defence")
    orig = pr["context_id"]; rep = orig + "-REPLAYED"
    pa = copy.deepcopy(pr); pa["context_id"] = rep
    check("a no-recompute -> record_hash denies", not verify_record_hash(pa))
    pb = copy.deepcopy(pr); pb["context_id"] = rep
    fields = {k: v for k, v in pb.items() if k != "record_hash"}
    pb["record_hash"] = hashlib.sha256(canonical_json(fields).encode()).hexdigest()
    check("b recompute -> record_hash valid (design boundary)", verify_record_hash(pb))
    v = check_context_replay(
        AuthContext("rf", orig, "witness-3", "rf-auth", "prod"),
        AuthContext("rf", rep, "witness-3", "rf-auth", "prod"))
    check("b ARK-457 denies replay", v.decision == "DENY")


def main():
    print("=" * 64)
    print("WITNESS-3 mock test suite (simulator + in-memory, zero QPU)")
    print("=" * 64)
    test_lp_and_canonical()
    cbs, r = test_chsh_violation()
    test_no_violation_fixture()
    pr, nist, astro, cal = test_proofrecord_and_verify(cbs, r)
    test_tamper(pr, cbs, cal, nist, astro)
    test_replay(pr)
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
