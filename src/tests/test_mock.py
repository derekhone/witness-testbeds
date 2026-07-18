"""
test_mock.py — Pre-lock mock tests for WITNESS-1 harness.

Runs WITHOUT IBM Quantum access. Uses a synthetic counts fixture.
All tests must pass before the MANIFEST lock is committed.

Run: python -m pytest src/tests/test_mock.py -v
  or: python src/tests/test_mock.py
"""

import json
import sys
import os
import tempfile
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nonce import canonical_json, sha256_hex, derive_nonce, raw_counts_hash, calibration_hash
from proofrecord import build_proofrecord, verify_proofrecord, save_proofrecord, load_proofrecord
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

MOCK_CALIBRATION = {
    "backend_name": "mock_backend",
    "num_qubits": 8,
    "basis_gates": ["cx", "h", "rz"],
    "snapshot_utc": "2026-07-18T00:00:00+00:00",
    "qubit_properties": {
        str(q): {"T1": 100.0 + q, "T2": 80.0 + q, "readout_error": 0.01 * q}
        for q in range(8)
    },
}

MOCK_CONTEXT_ID = "witness-1-primary"

# ── Test utilities ─────────────────────────────────────────────────────────────

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status} {name}" + (f"  → {detail}" if detail else "")
    print(msg)
    results.append((name, condition, msg))
    assert condition, f"FAILED: {name}  {detail}"


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_canonical_json_sorted():
    obj = {"z": 1, "a": 2, "m": 3}
    cj = canonical_json(obj).decode("utf-8")
    check("canonical_json: keys sorted", cj == '{"a":2,"m":3,"z":1}', cj)


def test_canonical_json_no_whitespace():
    obj = {"a": 1, "b": [1, 2]}
    cj = canonical_json(obj).decode("utf-8")
    check("canonical_json: no whitespace", " " not in cj, cj)


def test_canonical_json_utf8():
    obj = {"key": "café"}
    b = canonical_json(obj)
    check("canonical_json: UTF-8 bytes", isinstance(b, bytes), str(type(b)))


def test_canonical_json_rejects_non_dict():
    try:
        canonical_json([1, 2, 3])
        check("canonical_json: rejects list", False, "should have raised ValueError")
    except ValueError:
        check("canonical_json: rejects list", True)


def test_sha256_hex_length():
    h = sha256_hex(b"hello world")
    check("sha256_hex: 64 char hex", len(h) == 64, h)


def test_sha256_hex_known_value():
    # SHA-256 of empty bytes
    h = sha256_hex(b"")
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    check("sha256_hex: known empty-bytes value", h == expected, h)


def test_derive_nonce_deterministic():
    n1 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("derive_nonce: deterministic", n1 == n2, f"n1={n1[:16]} n2={n2[:16]}")


def test_derive_nonce_length():
    n = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("derive_nonce: 64 char hex", len(n) == 64, n)


def test_derive_nonce_changes_on_counts_change():
    counts_alt = {**MOCK_COUNTS, "00000000": 99}
    n1 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = derive_nonce(counts_alt, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("derive_nonce: different on counts change", n1 != n2)


def test_derive_nonce_changes_on_jobid_change():
    n1 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID + "_ALT", MOCK_CALIBRATION)
    check("derive_nonce: different on job_id change", n1 != n2)


def test_derive_nonce_changes_on_calibration_change():
    cal_alt = {**MOCK_CALIBRATION, "num_qubits": 16}
    n1 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    n2 = derive_nonce(MOCK_COUNTS, MOCK_JOB_ID, cal_alt)
    check("derive_nonce: different on calibration change", n1 != n2)


def test_build_proofrecord_schema():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    required = {"schema", "nonce", "job_id", "backend", "calibration_hash",
                "timestamp_utc", "raw_counts_hash", "context_id"}
    check("build_proofrecord: all required fields", required.issubset(record.keys()))
    check("build_proofrecord: nonce 64 chars", len(record["nonce"]) == 64)
    check("build_proofrecord: context_id set", record["context_id"] == MOCK_CONTEXT_ID)


def test_verify_proofrecord_pass():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    result = verify_proofrecord(record, MOCK_COUNTS, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("verify_proofrecord: honest → all_pass", result["all_pass"])


def test_verify_proofrecord_tamper_counts():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    tampered = {**MOCK_COUNTS, "00000000": 999}
    result = verify_proofrecord(record, tampered, MOCK_JOB_ID, MOCK_CALIBRATION)
    check("verify_proofrecord: tampered counts → fail", not result["all_pass"])
    check("verify_proofrecord: tampered counts → nonce_match False", not result["nonce_match"])


def test_verify_proofrecord_tamper_jobid():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    result = verify_proofrecord(record, MOCK_COUNTS, MOCK_JOB_ID + "_TAMPERED", MOCK_CALIBRATION)
    check("verify_proofrecord: tampered job_id → fail", not result["all_pass"])


def test_verify_proofrecord_tamper_calibration():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    cal_tampered = {**MOCK_CALIBRATION, "num_qubits": 128}
    result = verify_proofrecord(record, MOCK_COUNTS, MOCK_JOB_ID, cal_tampered)
    check("verify_proofrecord: tampered calibration → fail", not result["all_pass"])


def test_save_load_proofrecord():
    record = build_proofrecord(
        MOCK_COUNTS, MOCK_JOB_ID, "mock_backend", MOCK_CALIBRATION, MOCK_CONTEXT_ID
    )
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "proofrecord.json")
        save_proofrecord(record, path)
        loaded = load_proofrecord(path)
    check("save/load: nonce preserved", loaded["nonce"] == record["nonce"])
    check("save/load: job_id preserved", loaded["job_id"] == record["job_id"])


def test_ark457_original_context_allow():
    ctx = AuthContext("rf", "sess-1", "res-1", "aud-1", "exp")
    verdict = check_context_replay(ctx, ctx)
    check("ark457: original context → ALLOW", verdict.decision == "ALLOW")


def test_ark457_replay_deny_session():
    orig = AuthContext("rf", "sess-1", "res-1", "aud-1", "exp")
    replay = AuthContext("rf", "sess-REPLAY", "res-1", "aud-1", "exp")
    verdict = check_context_replay(orig, replay)
    check("ark457: replay different session → DENY", verdict.decision == "DENY")
    check("ark457: mismatch on session dim", "session" in verdict.mismatched_dims)


def test_ark457_replay_deny_tenant():
    orig = AuthContext("rf", "sess-1", "res-1", "aud-1", "exp")
    replay = AuthContext("other-tenant", "sess-1", "res-1", "aud-1", "exp")
    verdict = check_context_replay(orig, replay)
    check("ark457: replay different tenant → DENY", verdict.decision == "DENY")


def test_ark457_no_normalization():
    orig = AuthContext("rf", "Session-1", "res-1", "aud-1", "exp")
    # Case change — no normalization → DENY
    replay = AuthContext("rf", "session-1", "res-1", "aud-1", "exp")
    verdict = check_context_replay(orig, replay)
    check("ark457: case change → DENY (no normalization)", verdict.decision == "DENY")


def test_ark457_verify_no_replay_true():
    ctx = AuthContext("rf", "s", "r", "a", "e")
    check("verify_no_replay: same ctx → True", verify_no_replay(ctx, ctx))


def test_ark457_verify_no_replay_false():
    orig = AuthContext("rf", "s1", "r", "a", "e")
    replay = AuthContext("rf", "s2", "r", "a", "e")
    check("verify_no_replay: diff ctx → False", not verify_no_replay(orig, replay))


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        test_canonical_json_sorted,
        test_canonical_json_no_whitespace,
        test_canonical_json_utf8,
        test_canonical_json_rejects_non_dict,
        test_sha256_hex_length,
        test_sha256_hex_known_value,
        test_derive_nonce_deterministic,
        test_derive_nonce_length,
        test_derive_nonce_changes_on_counts_change,
        test_derive_nonce_changes_on_jobid_change,
        test_derive_nonce_changes_on_calibration_change,
        test_build_proofrecord_schema,
        test_verify_proofrecord_pass,
        test_verify_proofrecord_tamper_counts,
        test_verify_proofrecord_tamper_jobid,
        test_verify_proofrecord_tamper_calibration,
        test_save_load_proofrecord,
        test_ark457_original_context_allow,
        test_ark457_replay_deny_session,
        test_ark457_replay_deny_tenant,
        test_ark457_no_normalization,
        test_ark457_verify_no_replay_true,
        test_ark457_verify_no_replay_false,
    ]

    print("=" * 60)
    print("WITNESS-1 Mock Test Suite (pre-lock)")
    print("=" * 60)

    failures = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append(str(e))
        except Exception as e:
            failures.append(f"{t.__name__}: unexpected exception: {e}")

    print("=" * 60)
    passed = len(tests) - len(failures)
    print(f"Results: {passed}/{len(tests)} passed")
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
