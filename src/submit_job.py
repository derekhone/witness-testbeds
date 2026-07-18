"""
submit_job.py — Build 8-qubit H-measure circuit, submit to IBM Quantum,
save job_id, raw counts, backend calibration snapshot to results/raw/.

Execution-phase script. Run ONLY after the MANIFEST lock is committed and
the PR is merged by Derek. Requires IBM_QUANTUM_TOKEN in environment.

Usage:
    IBM_QUANTUM_TOKEN=<token> python src/submit_job.py

Outputs (written to results/raw/):
    job_meta.json      — job_id, backend, timestamp_utc, shots
    raw_counts.json    — canonical raw counts dict (bitstring -> int)
    calibration.json   — backend calibration snapshot (subset of properties)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


RESULTS_RAW = Path(__file__).parent.parent / "results" / "raw"
SHOTS = 4000
N_QUBITS = 8


def build_circuit():
    """Build 8-qubit Hadamard + measure-all circuit using Qiskit."""
    try:
        from qiskit import QuantumCircuit
    except ImportError:
        print("ERROR: qiskit not installed. Run: pip install qiskit qiskit-ibm-runtime")
        sys.exit(1)

    qc = QuantumCircuit(N_QUBITS, N_QUBITS)
    for i in range(N_QUBITS):
        qc.h(i)
    qc.measure_all()
    return qc


def get_calibration_snapshot(backend) -> dict:
    """
    Extract a minimal calibration snapshot from the backend properties.
    Stores: backend_name, num_qubits, basis_gates, coupling_map (first 16 pairs),
    and per-qubit T1/T2/readout_error for qubits 0-7.
    """
    try:
        props = backend.properties()
        snap = {
            "backend_name": backend.name,
            "num_qubits": backend.num_qubits,
            "basis_gates": sorted(backend.basis_gates),
            "coupling_map": [list(pair) for pair in list(backend.coupling_map)[:16]],
            "snapshot_utc": datetime.now(timezone.utc).isoformat(),
            "qubit_properties": {},
        }
        for q in range(min(N_QUBITS, backend.num_qubits)):
            try:
                qubit_props = props.qubit_property(q)
                snap["qubit_properties"][str(q)] = {
                    "T1": float(qubit_props.get("T1", (None, None))[0] or 0),
                    "T2": float(qubit_props.get("T2", (None, None))[0] or 0),
                    "readout_error": float(
                        props.readout_error(q) if props else 0
                    ),
                }
            except Exception:
                snap["qubit_properties"][str(q)] = {"T1": None, "T2": None, "readout_error": None}
        return snap
    except Exception as exc:
        # If properties unavailable, store a minimal snapshot with backend name only
        print(f"WARNING: Could not fetch full calibration properties: {exc}")
        return {
            "backend_name": backend.name,
            "num_qubits": getattr(backend, "num_qubits", None),
            "basis_gates": sorted(getattr(backend, "basis_gates", [])),
            "snapshot_utc": datetime.now(timezone.utc).isoformat(),
            "calibration_fetch_error": str(exc),
        }


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"  Saved: {path}")


def main():
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print("ERROR: IBM_QUANTUM_TOKEN environment variable not set.")
        sys.exit(1)

    print("=== WITNESS-1 submit_job.py ===")
    print(f"Qubits: {N_QUBITS}  Shots: {SHOTS}")

    # --- Connect to IBM Quantum ---
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
        from qiskit_ibm_runtime import Batch
    except ImportError:
        print("ERROR: qiskit-ibm-runtime not installed. Run: pip install qiskit-ibm-runtime")
        sys.exit(1)

    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)

    # Select least-busy backend with >= N_QUBITS qubits
    print("Selecting least-busy backend...")
    backend = service.least_busy(
        operational=True,
        simulator=False,
        min_num_qubits=N_QUBITS,
    )
    backend_name = backend.name
    print(f"Selected backend: {backend_name}  (num_qubits={backend.num_qubits})")

    # --- Calibration snapshot (before job submission) ---
    print("Capturing calibration snapshot...")
    calibration = get_calibration_snapshot(backend)

    # --- Build and transpile circuit ---
    print("Building circuit...")
    qc = build_circuit()

    try:
        from qiskit.compiler import transpile
        qc_t = transpile(qc, backend=backend)
    except Exception as exc:
        print(f"WARNING: Transpilation error: {exc}. Submitting untranspiled.")
        qc_t = qc

    # --- Submit job ---
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    print(f"Submitting job at {timestamp_utc}...")

    # Note: Session is not available on the open plan; Batch is used instead.
    # Harness fix (pre-execution, disclosed): channel and execution mode corrected.
    with Batch(backend=backend) as batch:
        sampler = Sampler(mode=batch)
        job = sampler.run([qc_t], shots=SHOTS)
        job_id = job.job_id()
        print(f"Job submitted. job_id = {job_id}")
        print("Waiting for results (this may take 10–120 seconds)...")
        result = job.result()

    # --- Extract raw counts ---
    print("Extracting raw counts...")
    try:
        pub_result = result[0]
        # Qiskit SamplerV2 returns BitArray; convert to counts dict
        bit_array = pub_result.data.meas
        counts_raw = bit_array.get_counts()
        # Normalise keys: ensure all bitstrings are N_QUBITS wide
        raw_counts = {
            k.replace(" ", "").zfill(N_QUBITS): v
            for k, v in counts_raw.items()
        }
    except Exception as exc:
        print(f"ERROR extracting counts: {exc}")
        sys.exit(1)

    total_shots = sum(raw_counts.values())
    unique_outcomes = len(raw_counts)
    print(f"Counts extracted: {total_shots} total shots, {unique_outcomes} unique outcomes")

    # --- Save artifacts ---
    print("Saving artifacts to results/raw/ ...")
    meta = {
        "job_id": job_id,
        "backend": backend_name,
        "timestamp_utc": timestamp_utc,
        "shots": SHOTS,
        "n_qubits": N_QUBITS,
        "total_shots_received": total_shots,
        "unique_outcomes": unique_outcomes,
        "circuit_description": f"{N_QUBITS}-qubit Hadamard on all qubits, measure all",
    }
    save_json(meta, RESULTS_RAW / "job_meta.json")
    save_json(raw_counts, RESULTS_RAW / "raw_counts.json")
    save_json(calibration, RESULTS_RAW / "calibration.json")

    print("\n=== submit_job.py COMPLETE ===")
    print(f"  job_id:   {job_id}")
    print(f"  backend:  {backend_name}")
    print(f"  shots:    {total_shots}")
    print(f"  outcomes: {unique_outcomes}")
    print("Artifacts saved. Proceed to run case scripts.")


if __name__ == "__main__":
    main()
