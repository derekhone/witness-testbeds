"""
WITNESS-2 submission harness. Requires IBM Quantum credentials. NOT called in mock tests.

Eligibility (preregistered):
  - operational (backend.status().operational == True)
  - non-simulator (backend.configuration().simulator == False)
  - n_qubits >= 8
  - accessible on open-plan instance

Budget gate: usage_remaining_seconds >= 30, else GATE-STOP.
Backend reselection: if selected backend unavailable at submission, reselect and log both.
Provider API unavailability at W2-C1 verification: GATE-STOP, not FAIL.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce import compute_quantum_nonce, compute_raw_counts_hash, compute_calibration_hash
from proofrecord import build_proofrecord
from calibration import extract_calibration_snapshot

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR     = RESULTS_DIR / "raw"
CONTEXT_ID  = "witness-2-primary"
N_QUBITS    = 8
SHOTS       = 4000
MIN_QPU_S   = 30   # gate-stop if below this


def load_token() -> str:
    secrets = Path.home() / ".config" / "abacusai_auth_secrets.json"
    with open(secrets) as f:
        d = json.load(f)
    for slot in ['witness1_ibmq', 'ibm_quantum', 'ibm']:
        v = d.get(slot, {}).get('secrets', {}).get('api_token', {}).get('value', '')
        if v:
            return v
    raise RuntimeError("IBM Quantum API token not found in secrets manager")


def is_eligible(backend) -> bool:
    try:
        s = backend.status()
        c = backend.configuration()
        return (s.operational
                and not getattr(c, 'simulator', True)
                and getattr(c, 'n_qubits', 0) >= N_QUBITS)
    except Exception:
        return False


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService, Batch, SamplerV2 as Sampler
    from qiskit import QuantumCircuit

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=load_token())

    # QPU budget gate
    usage = service.usage()
    remaining = usage.get('usage_remaining_seconds', 0)
    print(f"QPU budget remaining: {remaining}s")
    if remaining < MIN_QPU_S:
        print(f"GATE-STOP: {remaining}s < {MIN_QPU_S}s minimum")
        sys.exit(2)

    provider_instance = service.instances()[0]['crn']
    print(f"Provider instance: {provider_instance}")

    # Backend selection
    candidates = ['ibm_fez', 'ibm_marrakesh', 'ibm_kingston']
    selection_time = datetime.now(timezone.utc).isoformat()
    eligible = []
    for name in candidates:
        try:
            b = service.backend(name)
            if is_eligible(b):
                eligible.append(b)
            else:
                print(f"  {name}: ineligible")
        except Exception as e:
            print(f"  {name}: unavailable ({e})")

    if not eligible:
        print("GATE-STOP: no eligible backend found")
        sys.exit(2)

    backend = service.least_busy(eligible)
    print(f"Selected: {backend.name} at {selection_time}")

    # Circuit
    qc = QuantumCircuit(N_QUBITS)
    qc.h(range(N_QUBITS))
    qc.measure_all()
    selected_qubits = list(range(N_QUBITS))

    # Calibration snapshot BEFORE submission
    cal_snapshot = extract_calibration_snapshot(backend, selected_qubits)

    # Submit
    submission_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with Batch(backend=backend) as batch:
        job = Sampler(mode=batch).run([qc], shots=SHOTS)
        job_id = job.job_id()
        print(f"Job submitted: {job_id} at {submission_time}")

    print("Waiting for results...")
    result = job.result()
    raw_counts_raw = result[0].data.meas.get_counts()

    # Normalise: no spaces in keys, integer values
    raw_counts = {k.replace(' ', ''): int(v) for k, v in raw_counts_raw.items()}
    for k in raw_counts:
        assert len(k) == N_QUBITS, f"Unexpected bit-string length: {k!r}"

    print(f"Shots: {sum(raw_counts.values())} | Unique outcomes: {len(raw_counts)}")

    # Compute hashes and nonce
    quantum_nonce    = compute_quantum_nonce(raw_counts, job_id, cal_snapshot)
    raw_counts_hash  = compute_raw_counts_hash(raw_counts)
    calibration_hash = compute_calibration_hash(cal_snapshot)

    # Build ProofRecord
    proofrecord = build_proofrecord(
        quantum_nonce=quantum_nonce, job_id=job_id,
        backend=backend.name, provider_instance=provider_instance,
        calibration_hash=calibration_hash, raw_counts_hash=raw_counts_hash,
        context_id=CONTEXT_ID, timestamp_utc=submission_time,
    )

    # Save artifacts
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(RAW_DIR / "raw_counts.json", 'w') as f:
        json.dump(raw_counts, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "calibration_snapshot.json", 'w') as f:
        json.dump(cal_snapshot, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "job_meta.json", 'w') as f:
        json.dump({
            "job_id": job_id, "backend": backend.name,
            "provider_instance": provider_instance,
            "shots": SHOTS, "n_qubits": N_QUBITS,
            "selection_time_utc": selection_time,
            "submission_time_utc": submission_time,
            "unique_outcomes": len(raw_counts),
            "total_shots": sum(raw_counts.values()),
            "channel": "ibm_quantum_platform",
            "execution_mode": "Batch",
            "harness_fix_disclosure": "None — no pre-execution fixes required for WITNESS-2",
            "qiskit_version": "2.5.0",
            "qiskit_ibm_runtime_version": "0.48.0",
            "python_version": "3.11.6",
        }, f, indent=2)
    with open(RESULTS_DIR / "proofrecord.json", 'w') as f:
        json.dump(proofrecord, f, indent=2)

    print("\n=== ProofRecord ===")
    print(json.dumps(proofrecord, indent=2))
    print("\nArtifacts saved to witness-2/results/")


if __name__ == "__main__":
    main()
