"""
WITNESS-3 submission harness — Cosmic Beacon (CHSH Bell test + NIST + LIGO/GWOSC fusion).
Requires IBM Quantum credentials. NOT called in mock tests.

Preregistered execution:
  - 4 CHSH measurement circuits (Bell pair on 2 qubits, four preregistered setting pairs).
  - SHOTS_PER_SETTING shots each, one Batch job.
  - Backend: operational, non-simulator, >= 2 qubits, open-plan accessible; least pending.
  - QPU budget gate: usage_remaining_seconds >= MIN_QPU_S, else GATE-STOP.
  - Witnesses fetched at execution time: NIST beacon pulse + GWOSC GW150914 strain file.
  - Fused cosmic_nonce + ProofRecord built and saved to results/.

Any provider/network unavailability at submission = GATE-STOP (not FAIL).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce_v3 import (compute_cosmic_nonce, compute_raw_counts_hash,
                      compute_calibration_hash, compute_nist_hash, compute_astro_hash)
from proofrecord_v3 import build_proofrecord
from calibration import extract_calibration_snapshot
from chsh import build_chsh_circuits, compute_chsh, SETTINGS
from beacon_nist import fetch_nist_witness
from astro_gwosc import fetch_astro_witness

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"
CONTEXT_ID = "witness-3-cosmic-beacon"
SHOTS_PER_SETTING = 2000
MIN_QPU_S = 20
SIGMA_THRESHOLD = 5.0
TSIRELSON_TOLERANCE = 0.10


def load_token() -> str:
    with open(Path.home() / ".config" / "abacusai_auth_secrets.json") as f:
        d = json.load(f)
    for slot in ['ibm quantum', 'ibm_quantum', 'ibm', 'witness1_ibmq']:
        v = d.get(slot, {}).get('secrets', {}).get('api_token', {}).get('value', '')
        if v:
            return v
    raise RuntimeError("IBM Quantum API token not found in secrets manager")


def is_eligible(backend) -> bool:
    try:
        s = backend.status()
        c = backend.configuration()
        return (s.operational and not getattr(c, 'simulator', True)
                and getattr(c, 'n_qubits', 0) >= 2)
    except Exception:
        return False


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService, Batch, SamplerV2 as Sampler
    from qiskit import transpile

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=load_token())

    usage = service.usage()
    remaining = usage.get('usage_remaining_seconds', 0) if isinstance(usage, dict) else 0
    print(f"QPU budget remaining: {remaining}s")
    if remaining is not None and remaining < MIN_QPU_S:
        print(f"GATE-STOP: {remaining}s < {MIN_QPU_S}s minimum")
        sys.exit(2)

    try:
        provider_instance = service.instances()[0]['crn']
    except Exception:
        provider_instance = str(service.instances()[0]) if service.instances() else "open-instance"
    print(f"Provider instance: {provider_instance}")

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
        # fall back to any eligible backend the account can see
        for b in service.backends(operational=True, simulator=False):
            if is_eligible(b):
                eligible.append(b)
    if not eligible:
        print("GATE-STOP: no eligible backend found")
        sys.exit(2)

    backend = min(eligible, key=lambda b: b.status().pending_jobs)
    print(f"Selected: {backend.name} at {selection_time}")

    # Use physical qubits 0,1 (logical); transpile handles the mapping.
    labeled = build_chsh_circuits(alice_qubit=0, bob_qubit=1)
    labels = [lab for lab, _ in labeled]
    circuits = [qc for _, qc in labeled]
    isa_circuits = [transpile(qc, backend=backend, optimization_level=1) for qc in circuits]
    print(f"Transpiled {len(isa_circuits)} CHSH circuits; labels={labels}")

    cal_snapshot = extract_calibration_snapshot(backend, [0, 1])

    # Fetch the two classical witnesses at execution time.
    print("Fetching NIST beacon witness...")
    nist_witness = fetch_nist_witness()
    print(f"  NIST pulseIndex={nist_witness['pulseIndex']} ts={nist_witness['timeStamp']}")
    print("Fetching LIGO/GWOSC astro witness (GW150914 strain)...")
    astro_witness = fetch_astro_witness()
    print(f"  astro file_sha256={astro_witness['file_sha256'][:16]}... size={astro_witness['file_size_bytes']}B")

    submission_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with Batch(backend=backend) as batch:
        job = Sampler(mode=batch).run(isa_circuits, shots=SHOTS_PER_SETTING)
        job_id = job.job_id()
        print(f"Job submitted: {job_id} at {submission_time}")

    print("Waiting for results...")
    result = job.result()

    counts_by_setting = {}
    for i, label in enumerate(labels):
        data = result[i].data
        creg = getattr(data, 'c', None) or getattr(data, 'meas', None)
        counts_raw = creg.get_counts()
        counts = {k.replace(' ', ''): int(v) for k, v in counts_raw.items()}
        for k in counts:
            assert len(k) == 2, f"Unexpected bit-string {k!r} for setting {label}"
        counts_by_setting[label] = counts

    raw_counts = counts_by_setting  # nonce binds the full per-setting measurement data
    chsh_result = compute_chsh(counts_by_setting)
    abs_S = chsh_result["abs_S"]
    sigmas = chsh_result["sigmas_above_classical"]
    bell_certified = bool(abs_S > 2.0 and sigmas >= SIGMA_THRESHOLD
                          and abs_S <= (chsh_result["tsirelson_bound"] + TSIRELSON_TOLERANCE))
    print(f"CHSH S = {chsh_result['S']:.4f} +/- {chsh_result['sigma_S']:.4f} "
          f"({sigmas:.1f} sigma over classical) -> bell_certified={bell_certified}")

    cosmic_nonce = compute_cosmic_nonce(raw_counts, job_id, cal_snapshot,
                                        nist_witness, astro_witness)
    proofrecord = build_proofrecord(
        cosmic_nonce=cosmic_nonce, job_id=job_id, backend=backend.name,
        provider_instance=provider_instance,
        calibration_hash=compute_calibration_hash(cal_snapshot),
        raw_counts_hash=compute_raw_counts_hash(raw_counts),
        nist_hash=compute_nist_hash(nist_witness),
        astro_hash=compute_astro_hash(astro_witness),
        chsh_result=chsh_result, bell_certified=bell_certified,
        context_id=CONTEXT_ID, timestamp_utc=submission_time)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "raw_counts.json", 'w') as f:
        json.dump(raw_counts, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "calibration_snapshot.json", 'w') as f:
        json.dump(cal_snapshot, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "nist_witness.json", 'w') as f:
        json.dump(nist_witness, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "astro_witness.json", 'w') as f:
        json.dump(astro_witness, f, sort_keys=True, indent=2)
    with open(RAW_DIR / "job_meta.json", 'w') as f:
        json.dump({
            "job_id": job_id, "backend": backend.name,
            "provider_instance": provider_instance,
            "shots_per_setting": SHOTS_PER_SETTING, "n_settings": len(labels),
            "settings": [{"label": lab, "alice_angle": a, "bob_angle": b, "sign_in_S": s}
                         for (lab, a, b, s) in SETTINGS],
            "selection_time_utc": selection_time,
            "submission_time_utc": submission_time,
            "channel": "ibm_quantum_platform", "execution_mode": "Batch",
            "qiskit_version": "2.5.0", "qiskit_ibm_runtime_version": "0.48.0",
            "python_version": "3.11",
        }, f, indent=2)
    with open(RESULTS_DIR / "chsh_result.json", 'w') as f:
        json.dump(chsh_result, f, indent=2)
    with open(RESULTS_DIR / "proofrecord.json", 'w') as f:
        json.dump(proofrecord, f, indent=2)

    print("\n=== ProofRecord ===")
    print(json.dumps(proofrecord, indent=2))
    print("\nArtifacts saved to witness-3/results/")


if __name__ == "__main__":
    main()
