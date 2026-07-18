"""
test_mock.py — Pre-lock mock tests for WITNESS-2 harness.

Runs WITHOUT IBM Quantum access. Uses a synthetic counts fixture and a synthetic
calibration snapshot matching the WITNESS-2 10-field deterministic schema.

Run: python -m pytest witness-2/src/tests/test_mock.py -v
  or: python witness-2/src/tests/test_mock.py
"""

import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

# Add witness-2/src/ to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nonce import (
    canonical_json,
    lp,
    compute_quantum_nonce,
    compute_raw_counts_hash,
    compute_calibration_hash,
)
from proofrecord import build_proofrecord, verify_record_hash, verify_quantum_nonce
from ark457_replay import AuthContext, check_context_replay, verify_no_replay

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_COUNTS = {
    "00000000": 18,
    "00000001": 22,
    "11111111": 19,
    "10101010": 17,
    "01010101": 20,
    "11001100": 15,
    "00110011": 21,
    "10011001": 16,
}

MOCK_JOB_ID = "mock_job_abc123xyz"

# 10-field deterministic calibration snapshot (WITNESS-2 schema)
MOCK_CALIBRATION = {
    "backend_name": "mock_backend",
    "backend_version": "1.0.0",
    "last_update_utc": "2026-07-18T00:00:00Z",
    "basis_gates": ["cx", "h", "id", "rz", "sx", "x"],
    "selected_qubits": [0, 1, 2, 3, 4, 5, 6, 7],
    "readout_error_by_qubit": {str(q): round(0.005 + 0.001 * q, 6) for q in range(8)},
    "t1_by_qubit":            {str(q): round(100e-6 + 10e-6 * q, 9) for q in range(8)},
    "t2_by_qubit":            {str(q): round(80e-6 + 8e-6 * q,  9) for q in range(8)},
    "gate_error_for_used_gates": {
        **{f"h_q{q}":       round(0.0003 + 0.0001 * q, 7) for q in range(8)},
        **{f"measure_q{q}": round(0.005  + 0.001  * q, 6) for q in range(8)},
    },
    "gate_length_for_used_gates": {
        **{f"h_q{q}":       round(56e-9   + 4e-9   * q, 12) for q in range(8)},
        **{f"measure_q{q}": round(1280e-9 + 100e-9 * q, 12) for q in range(8)},
    },
}

MOCK_PROVIDER_INSTANCE = "crn:v1:bluemix:public:quantum-computing:mock-region::a/mock"
MOCK_CONTEXT_ID        = "witness-2-primary"

# ── Test utilities ─────────────────────────────────────────────────────────────

PASS_TAG = "[PASS]"
FAIL_TAG = "[FAIL]"
_results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    tag = PASS_TAG if condition else FAIL_TAG
    msg = f"{tag} {name}" + (f"  → {detail}" if detail else "")
    print(msg)
    _results.append((name, condition, msg))
    assert condition, f"FAILED: {name}  {detail}"


# ── 1. canonical_json ──────────────────────────────────────────────────────────

def test_canonical_json_returns_str():
    cj = canonical_json({"a": 1})
    check("canonical_json: returns str", isinstance(cj, str), type(cj).__name__)


def test_canonical_json_sorted_keys():
    cj = canonical_json({"z": 1, "a": 2, "m": 3})
    check("canonical_json: keys sorted", cj == '{"a":2,"m":3,"z":1}', cj)


def test_canonical_json_no_whitespace():
    cj = canonical_json({"a": 1, "b": [1, 2]})
    check("canonical_json: no whitespace", " " not in cj, cj)


def test_canonical_json_ensure_ascii():
    cj = canonical_json({"key": "café"})
    check("canonical_json: ensure_ascii", all(ord(c) < 128 for c in cj), cj[:30])


# ── 2. lp() length prefix ──────────────────────────────────────────────────────

def test_lp_structure():
    data = b"hello"
    prefixed = lp(data)
    length = struct.unpack('>I', prefixed[:4])[0]
    payload = prefixed[4:]
    check("lp: 4-byte prefix + data", len(prefixed) == 9, str(len(prefixed)))
    check("lp: prefix encodes length", length == 5, str(length))
    check("lp: payload matches data", payload == data)


def test_lp_empty():
    prefixed = lp(b"")
    check("lp: empty → 4-byte zero prefix", prefixed == b'\x00\x00\x00\x00')


def test_lp_anti_length_extension():
    """
    Key property: LP prevents two different component splits from hashing identically.
    Without LP: SHA-256("abc" + "de") == SHA-256("ab" + "cde") — same bytes, same hash.
    With LP:    LP("abc") + LP("de") != LP("ab") + LP("cde") — length tags differ.
    """
    a1, b1 = b"abc", b"de"
    a2, b2 = b"ab",  b"cde"
    # Without LP: byte streams are identical
    check("lp: without LP: same bytes",    a1 + b1 == a2 + b2)
    # With LP: byte streams differ
    check("lp: with LP: different bytes",  lp(a1) + lp(b1) != lp(a2) + lp(b2))


# ── 3. compute_quantum_nonce ───────────────────────────────────────────────────

def test_nonce_deterministic():
    n1 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("compute_quantum_nonce: deterministic", n1 == n2, f"{n1[:16]}…")


def test_nonce_64_chars():
    n = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("compute_quantum_nonce: 64-char hex", len(n) == 64, n)


def test_nonce_changes_on_counts():
    counts_alt = {**MOCK_COUNTS, "00000000": 9999}
    n1 = compute_quantum_nonce(MOCK_COUNTS,    MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = compute_quantum_nonce(counts_alt,     MOCK_JOB_ID, MOCK_CALIBRATION)
    check("compute_quantum_nonce: changes on counts change", n1 != n2)


def test_nonce_changes_on_jobid():
    n1 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID,          MOCK_CALIBRATION)
    n2 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID + "_ALT", MOCK_CALIBRATION)
    check("compute_quantum_nonce: changes on job_id change", n1 != n2)


def test_nonce_changes_on_calibration():
    cal_alt = copy.deepcopy(MOCK_CALIBRATION)
    cal_alt["backend_version"] = "9.9.9"
    n1 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, cal_alt)
    check("compute_quantum_nonce: changes on calibration change", n1 != n2)


def test_nonce_lp_prevents_split_ambiguity():
    """
    Verify that length-prefixed nonce is different from a naively concatenated nonce,
    confirming the LP upgrade over WITNESS-1.
    """
    counts_bytes = canonical_json(MOCK_COUNTS).encode('utf-8')
    jobid_bytes  = MOCK_JOB_ID.encode('utf-8')
    cal_bytes    = canonical_json(MOCK_CALIBRATION).encode('utf-8')

    lp_nonce  = hashlib.sha256(lp(counts_bytes) + lp(jobid_bytes) + lp(cal_bytes)).hexdigest()
    raw_nonce = hashlib.sha256(counts_bytes + jobid_bytes + cal_bytes).hexdigest()

    actual_nonce = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("compute_quantum_nonce: uses LP (not bare concat)", actual_nonce == lp_nonce)
    check("compute_quantum_nonce: LP differs from bare concat", lp_nonce != raw_nonce)


# ── 4. compute_raw_counts_hash / compute_calibration_hash ─────────────────────

def test_raw_counts_hash_deterministic():
    h1 = compute_raw_counts_hash(MOCK_COUNTS)
    h2 = compute_raw_counts_hash(MOCK_COUNTS)
    check("compute_raw_counts_hash: deterministic", h1 == h2, h1[:16])


def test_raw_counts_hash_64_chars():
    h = compute_raw_counts_hash(MOCK_COUNTS)
    check("compute_raw_counts_hash: 64-char hex", len(h) == 64)


def test_raw_counts_hash_changes_on_mutation():
    counts_alt = {**MOCK_COUNTS, "11111111": 1}
    h1 = compute_raw_counts_hash(MOCK_COUNTS)
    h2 = compute_raw_counts_hash(counts_alt)
    check("compute_raw_counts_hash: changes on mutation", h1 != h2)


def test_calibration_hash_deterministic():
    h1 = compute_calibration_hash(MOCK_CALIBRATION)
    h2 = compute_calibration_hash(MOCK_CALIBRATION)
    check("compute_calibration_hash: deterministic", h1 == h2, h1[:16])


def test_calibration_hash_changes_on_mutation():
    cal_alt = copy.deepcopy(MOCK_CALIBRATION)
    cal_alt["readout_error_by_qubit"]["0"] = 0.9999
    h1 = compute_calibration_hash(MOCK_CALIBRATION)
    h2 = compute_calibration_hash(cal_alt)
    check("compute_calibration_hash: changes on mutation", h1 != h2)


# ── 5. build_proofrecord ───────────────────────────────────────────────────────

def _make_mock_record():
    nonce    = compute_quantum_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    rch      = compute_raw_counts_hash(MOCK_COUNTS)
    calh     = compute_calibration_hash(MOCK_CALIBRATION)
    return build_proofrecord(
        quantum_nonce     = nonce,
        job_id            = MOCK_JOB_ID,
        backend           = "mock_backend",
        provider_instance = MOCK_PROVIDER_INSTANCE,
        calibration_hash  = calh,
        raw_counts_hash   = rch,
        context_id        = MOCK_CONTEXT_ID,
        timestamp_utc     = "2026-07-18T00:00:00Z",
    )


def test_build_proofrecord_required_fields():
    pr = _make_mock_record()
    required = {
        "schema_version", "quantum_nonce", "job_id", "backend",
        "provider_instance", "calibration_hash", "raw_counts_hash",
        "context_id", "timestamp_utc", "record_hash",
    }
    missing = required - set(pr.keys())
    check("build_proofrecord: all required fields present", not missing, str(missing))


def test_build_proofrecord_schema_version():
    pr = _make_mock_record()
    check("build_proofrecord: schema_version correct",
          pr["schema_version"] == "witness-proofrecord-1.0",
          pr.get("schema_version"))


def test_build_proofrecord_quantum_nonce_64():
    pr = _make_mock_record()
    check("build_proofrecord: quantum_nonce 64 chars", len(pr["quantum_nonce"]) == 64)


def test_build_proofrecord_record_hash_64():
    pr = _make_mock_record()
    check("build_proofrecord: record_hash 64 chars", len(pr["record_hash"]) == 64)


def test_build_proofrecord_context_id():
    pr = _make_mock_record()
    check("build_proofrecord: context_id set",
          pr["context_id"] == MOCK_CONTEXT_ID, pr.get("context_id"))


def test_build_proofrecord_provider_instance():
    pr = _make_mock_record()
    check("build_proofrecord: provider_instance set",
          bool(pr.get("provider_instance")), pr.get("provider_instance"))


# ── 6. verify_record_hash ──────────────────────────────────────────────────────

def test_verify_record_hash_honest():
    pr = _make_mock_record()
    check("verify_record_hash: honest → True", verify_record_hash(pr))


def test_verify_record_hash_tamper_nonce():
    pr = copy.deepcopy(_make_mock_record())
    pr["quantum_nonce"] = "a" * 64
    check("verify_record_hash: tampered quantum_nonce → False", not verify_record_hash(pr))


def test_verify_record_hash_tamper_job_id():
    pr = copy.deepcopy(_make_mock_record())
    pr["job_id"] = pr["job_id"] + "_TAMPERED"
    check("verify_record_hash: tampered job_id → False", not verify_record_hash(pr))


def test_verify_record_hash_tamper_context_id():
    pr = copy.deepcopy(_make_mock_record())
    pr["context_id"] = "witness-2-FORGED"
    check("verify_record_hash: tampered context_id (no recompute) → False",
          not verify_record_hash(pr))


def test_verify_record_hash_tamper_provider_instance():
    pr = copy.deepcopy(_make_mock_record())
    pr["provider_instance"] = "crn:FORGED"
    check("verify_record_hash: tampered provider_instance → False",
          not verify_record_hash(pr))


# ── 7. verify_quantum_nonce ───────────────────────────────────────────────────

def test_verify_quantum_nonce_honest():
    pr = _make_mock_record()
    check("verify_quantum_nonce: honest → True",
          verify_quantum_nonce(pr, MOCK_COUNTS, MOCK_CALIBRATION))


def test_verify_quantum_nonce_tamper_counts():
    pr  = _make_mock_record()
    fcs = {**MOCK_COUNTS, "00000000": 9999}
    check("verify_quantum_nonce: tampered counts → False",
          not verify_quantum_nonce(pr, fcs, MOCK_CALIBRATION))


def test_verify_quantum_nonce_tamper_calibration():
    pr      = _make_mock_record()
    cal_alt = copy.deepcopy(MOCK_CALIBRATION)
    cal_alt["backend_version"] = "FORGED"
    check("verify_quantum_nonce: tampered calibration → False",
          not verify_quantum_nonce(pr, MOCK_COUNTS, cal_alt))


# ── 8. W2-C2 sub-trial pattern: 4 sub-trials ──────────────────────────────────

def test_w2c2_a_counts_altered():
    pr = _make_mock_record()
    fcs = dict(MOCK_COUNTS)
    keys = list(fcs.keys())
    fcs[keys[0]], fcs[keys[1]] = fcs[keys[1]], fcs[keys[0]]
    detected = not verify_quantum_nonce(pr, fcs, MOCK_CALIBRATION)
    check("W2-C2(a): counts_altered → detected by quantum_nonce", detected)


def test_w2c2_b_job_id_altered():
    pr   = _make_mock_record()
    fp   = copy.deepcopy(pr)
    fp["job_id"] = pr["job_id"] + "_FORGED"
    nonce_ok = verify_quantum_nonce(fp, MOCK_COUNTS, MOCK_CALIBRATION)
    rh_ok    = verify_record_hash(fp)
    detected = not nonce_ok or not rh_ok
    check("W2-C2(b): job_id_altered → detected by nonce and/or record_hash", detected)


def test_w2c2_c_calibration_altered():
    pr      = _make_mock_record()
    cal_alt = copy.deepcopy(MOCK_CALIBRATION)
    k0      = sorted(cal_alt["readout_error_by_qubit"].keys())[0]
    v0      = cal_alt["readout_error_by_qubit"][k0]
    cal_alt["readout_error_by_qubit"][k0] = 0.9999 if v0 != 0.9999 else 0.0001
    detected = not verify_quantum_nonce(pr, MOCK_COUNTS, cal_alt)
    check("W2-C2(c): calibration_altered → detected by quantum_nonce", detected)


def test_w2c2_d_context_id_altered_no_recompute():
    pr   = _make_mock_record()
    fp   = copy.deepcopy(pr)
    fp["context_id"] = "witness-2-FORGED-context"
    detected = not verify_record_hash(fp)
    check("W2-C2(d): context_id_altered (no recompute) → detected by record_hash", detected)


# ── 9. W2-C3 sub-case pattern: design boundary ───────────────────────────────

def test_w2c3_a_context_id_altered_no_recompute():
    """Sub-case (a): record_hash NOT recomputed → caught at field-integrity layer."""
    pr   = _make_mock_record()
    fa   = copy.deepcopy(pr)
    fa["context_id"] = "witness-2-replay-context"
    rec_valid = verify_record_hash(fa)   # False: record_hash stale
    denied    = not rec_valid
    check("W2-C3(a): context_id changed, no recompute → DENY by record_hash", denied)


def test_w2c3_b_context_id_altered_with_recompute():
    """
    Sub-case (b): record_hash RECOMPUTED with new context_id.
    record_hash is valid (attacker succeeded — this is EXPECTED and is NOT a defect).
    DENY must come from ARK-457 context binding.
    """
    import hashlib as _hl
    pr     = _make_mock_record()
    orig_ctx_id   = pr["context_id"]
    replay_ctx_id = "witness-2-replay-context"

    # Attacker recomputes record_hash
    fb_fields = {k: v for k, v in pr.items() if k != "record_hash"}
    fb_fields["context_id"] = replay_ctx_id
    new_rh = _hl.sha256(canonical_json(fb_fields).encode('utf-8')).hexdigest()
    fb = {**fb_fields, "record_hash": new_rh}

    # record_hash is valid (expected — this is the design boundary)
    rec_valid = verify_record_hash(fb)
    check("W2-C3(b): record_hash valid after attacker recomputes (expected)", rec_valid)

    # ARK-457 context binding fires
    orig_ctx   = AuthContext("remnant-fieldworks", orig_ctx_id,   "witness-2-nonce", "verifier", "production")
    replay_ctx = AuthContext("remnant-fieldworks", replay_ctx_id, "witness-2-nonce", "verifier", "production")
    verdict    = check_context_replay(orig_ctx, replay_ctx)
    check("W2-C3(b): ARK-457 → DENY on replay context", verdict.decision == "DENY")
    check("W2-C3(b): mismatch on session dimension", "session" in verdict.mismatched_dims)
    check("W2-C3(b): design boundary confirmed: record_hash=field_integrity only, ARK-457=context_enforcement",
          rec_valid and verdict.decision == "DENY")


# ── 10. ARK-457 direct tests ──────────────────────────────────────────────────

def test_ark457_allow_identical():
    ctx = AuthContext("rf", "sess-1", "res-1", "aud-1", "prod")
    verdict = check_context_replay(ctx, ctx)
    check("ark457: identical context → ALLOW", verdict.decision == "ALLOW")
    check("ark457: no mismatched dims on ALLOW", verdict.mismatched_dims == [])


def test_ark457_deny_session():
    orig   = AuthContext("rf", "sess-1",      "res-1", "aud-1", "prod")
    replay = AuthContext("rf", "sess-REPLAY",  "res-1", "aud-1", "prod")
    verdict = check_context_replay(orig, replay)
    check("ark457: different session → DENY",  verdict.decision == "DENY")
    check("ark457: session in mismatched_dims", "session" in verdict.mismatched_dims)


def test_ark457_deny_tenant():
    orig   = AuthContext("rf",           "s", "r", "a", "e")
    replay = AuthContext("other-tenant", "s", "r", "a", "e")
    verdict = check_context_replay(orig, replay)
    check("ark457: different tenant → DENY",  verdict.decision == "DENY")
    check("ark457: tenant in mismatched_dims", "tenant" in verdict.mismatched_dims)


def test_ark457_deny_multi_dim():
    orig   = AuthContext("rf",    "s1", "r1", "a1", "prod")
    replay = AuthContext("other", "s2", "r1", "a1", "prod")
    verdict = check_context_replay(orig, replay)
    check("ark457: multi-dim mismatch → DENY", verdict.decision == "DENY")
    check("ark457: two dims mismatched", len(verdict.mismatched_dims) == 2,
          str(verdict.mismatched_dims))


def test_ark457_no_normalization():
    orig   = AuthContext("rf", "Session-1", "r", "a", "e")
    replay = AuthContext("rf", "session-1", "r", "a", "e")  # case change
    verdict = check_context_replay(orig, replay)
    check("ark457: case change → DENY (no normalization)", verdict.decision == "DENY")


def test_ark457_verify_no_replay_true():
    ctx = AuthContext("rf", "s", "r", "a", "e")
    check("verify_no_replay: same ctx → True", verify_no_replay(ctx, ctx))


def test_ark457_verify_no_replay_false():
    orig   = AuthContext("rf", "s1", "r", "a", "e")
    replay = AuthContext("rf", "s2", "r", "a", "e")
    check("verify_no_replay: diff ctx → False", not verify_no_replay(orig, replay))


# ── 11. Calibration schema field-count ────────────────────────────────────────

def test_calibration_schema_10_fields():
    expected_keys = {
        "backend_name", "backend_version", "last_update_utc",
        "basis_gates", "selected_qubits",
        "readout_error_by_qubit", "t1_by_qubit", "t2_by_qubit",
        "gate_error_for_used_gates", "gate_length_for_used_gates",
    }
    missing = expected_keys - set(MOCK_CALIBRATION.keys())
    extra   = set(MOCK_CALIBRATION.keys()) - expected_keys
    check("calibration schema: exactly 10 required fields present",
          not missing and not extra,
          f"missing={missing} extra={extra}")


def test_calibration_basis_gates_sorted():
    gates = MOCK_CALIBRATION["basis_gates"]
    check("calibration schema: basis_gates sorted", gates == sorted(gates), str(gates))


def test_calibration_selected_qubits_sorted():
    qs = MOCK_CALIBRATION["selected_qubits"]
    check("calibration schema: selected_qubits sorted ascending", qs == sorted(qs), str(qs))


# ── Runner ────────────────────────────────────────────────────────────────────

_ALL_TESTS = [
    test_canonical_json_returns_str,
    test_canonical_json_sorted_keys,
    test_canonical_json_no_whitespace,
    test_canonical_json_ensure_ascii,
    test_lp_structure,
    test_lp_empty,
    test_lp_anti_length_extension,
    test_nonce_deterministic,
    test_nonce_64_chars,
    test_nonce_changes_on_counts,
    test_nonce_changes_on_jobid,
    test_nonce_changes_on_calibration,
    test_nonce_lp_prevents_split_ambiguity,
    test_raw_counts_hash_deterministic,
    test_raw_counts_hash_64_chars,
    test_raw_counts_hash_changes_on_mutation,
    test_calibration_hash_deterministic,
    test_calibration_hash_changes_on_mutation,
    test_build_proofrecord_required_fields,
    test_build_proofrecord_schema_version,
    test_build_proofrecord_quantum_nonce_64,
    test_build_proofrecord_record_hash_64,
    test_build_proofrecord_context_id,
    test_build_proofrecord_provider_instance,
    test_verify_record_hash_honest,
    test_verify_record_hash_tamper_nonce,
    test_verify_record_hash_tamper_job_id,
    test_verify_record_hash_tamper_context_id,
    test_verify_record_hash_tamper_provider_instance,
    test_verify_quantum_nonce_honest,
    test_verify_quantum_nonce_tamper_counts,
    test_verify_quantum_nonce_tamper_calibration,
    test_w2c2_a_counts_altered,
    test_w2c2_b_job_id_altered,
    test_w2c2_c_calibration_altered,
    test_w2c2_d_context_id_altered_no_recompute,
    test_w2c3_a_context_id_altered_no_recompute,
    test_w2c3_b_context_id_altered_with_recompute,
    test_ark457_allow_identical,
    test_ark457_deny_session,
    test_ark457_deny_tenant,
    test_ark457_deny_multi_dim,
    test_ark457_no_normalization,
    test_ark457_verify_no_replay_true,
    test_ark457_verify_no_replay_false,
    test_calibration_schema_10_fields,
    test_calibration_basis_gates_sorted,
    test_calibration_selected_qubits_sorted,
]


def run_all():
    print("=" * 70)
    print("WITNESS-2 Mock Test Suite (pre-lock)")
    print("=" * 70)

    failures = []
    for t in _ALL_TESTS:
        try:
            t()
        except AssertionError as e:
            failures.append(str(e))
        except Exception as e:
            failures.append(f"{t.__name__}: unexpected exception: {type(e).__name__}: {e}")

    print("=" * 70)
    passed = len(_ALL_TESTS) - len(failures)
    print(f"Results: {passed}/{len(_ALL_TESTS)} passed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  {f}")
        print("STATUS: FAIL — do not lock until all tests pass.")
        return False
    else:
        print("STATUS: ALL PASS — safe to lock.")
        return True


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
