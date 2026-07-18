"""
WITNESS-4 submission harness — Freshness Bracket (non-backdatable, chain-linked quantum
ProofRecord). Requires IBM Quantum credentials. NOT called in mock tests.

Preregistered execution ORDER (the order is load-bearing for the freshness claim):
  1. Build the PRE-COMMITMENT (circuit spec + intent + context + prev ledger link) and
     record precommit_time_utc + precommit_hash — BEFORE any random anchor is known.
  2. Submit the CHSH Bell-test job (4 settings, SHOTS_PER_SETTING each, one Batch job).
  3. AFTER results return, fetch the NIST beacon pulse (its value did not exist before its
     release timeStamp) and the fixed public LIGO/GWOSC GW150914 strain file.
  4. Fuse the 7-segment nonce (precommit ‖ prev_link ‖ counts ‖ job_id ‖ cal ‖ nist ‖ astro),
     evaluate the freshness bracket, build + save the ProofRecord.

  - prev_record_hash (genesis link) = WITNESS-3 published record_hash -> the WITNESS series
    becomes a single append-only, third-party-verifiable ledger.
  - QPU budget gate: usage_remaining_seconds >= MIN_QPU_S, else GATE-STOP.
  - Any provider/network unavailability = GATE-STOP (not FAIL).

Channel note: channel="ibm_cloud" from the outset (the correct open-plan channel; this was
discovered as FIX-W3-1 in WITNESS-3 and is inherited here, NOT a post-lock WITNESS-4 fix).
"""

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nonce_v4 import (compute_fused_nonce, compute_raw_counts_hash,
                      compute_calibration_hash, compute_nist_hash, compute_astro_hash)
from proofrecord_v4 import build_proofrecord
from precommit import build_precommit, compute_precommit_hash
from calibration import extract_calibration_snapshot
from chsh import build_chsh_circuits, compute_chsh, SETTINGS, ALICE_ANGLES, BOB_ANGLES
from beacon_nist import fetch_nist_witness
from astro_gwosc import fetch_astro_witness

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_DIR = RESULTS_DIR / "raw"
CONTEXT_ID = "witness-4-freshness-bracket"
SHOTS_PER_SETTING = 2000
MIN_QPU_S = 20
SIGMA_THRESHOLD = 5.0
TSIRELSON_TOLERANCE = 0.10

# Genesis ledger link: WITNESS-3 published record_hash (Zenodo DOI 10.5281/zenodo.21434832).
# WITNESS-4 chains to it, making WITNESS-1..4 one append-only verifiable ledger.
GENESIS_PREV_HASH = "858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf"
PREV_RECORD_TIMESTAMP_UTC = "2026-07-18T22:31:00Z"  # WITNESS-3 finalize time (advisory chain-monotonic check)


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


def build_precommit_doc(precommit_time_utc: str) -> dict:
    circuit_spec = {
        "bell_state": "phi_plus",
        "alice_qubit": 0,
        "bob_qubit": 1,
        "shots_per_setting": SHOTS_PER_SETTING,
        "n_settings": len(SETTINGS),
        "alice_angles": ALICE_ANGLES,
        "bob_angles": BOB_ANGLES,
        "sigma_threshold": SIGMA_THRESHOLD,
        "tsirelson_tolerance": TSIRELSON_TOLERANCE,
    }
    return build_precommit(
        circuit_spec=circuit_spec,
        intent="WITNESS-4 freshness-bracket: non-backdatable, chain-linked quantum authorization nonce",
        context_id=CONTEXT_ID,
        prev_record_hash=GENESIS_PREV_HASH,
        precommit_time_utc=precommit_time_utc,
    )


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService, Batch, SamplerV2 as Sampler
    from qiskit import transpile

    # === STEP 1: PRE-COMMITMENT (before any random anchor is known) ===
    precommit_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    precommit_doc = build_precommit_doc(precommit_time)
    precommit_hash = compute_precommit_hash(precommit_doc)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "precommit.json", 'w') as f:
        json.dump(precommit_doc, f, sort_keys=True, indent=2)
    print(f"PRE-COMMITMENT fixed at {precommit_time}")
    print(f"  precommit_hash = {precommit_hash}")
    print(f"  prev_record_hash (genesis=WITNESS-3) = {GENESIS_PREV_HASH}")

    service = QiskitRuntimeService(channel="ibm_cloud", token=load_token())

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
        for b in service.backends(operational=True, simulator=False):
            if is_eligible(b):
                eligible.append(b)
    if not eligible:
        print("GATE-STOP: no eligible backend found")
        sys.exit(2)

    backend = min(eligible, key=lambda b: b.status().pending_jobs)
    print(f"Selected: {backend.name} at {selection_time}")

    # === STEP 2: QPU job ===
    labeled = build_chsh_circuits(alice_qubit=0, bob_qubit=1)
    labels = [lab for lab, _ in labeled]
    circuits = [qc for _, qc in labeled]
    isa_circuits = [transpile(qc, backend=backend, optimization_level=1) for qc in circuits]
    print(f"Transpiled {len(isa_circuits)} CHSH circuits; labels={labels}")

    cal_snapshot = extract_calibration_snapshot(backend, [0, 1])

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
    raw_counts = counts_by_setting

    # === STEP 3: fetch the random/public anchors AFTER the QPU results exist ===
    # CRITICAL: fetch a NIST pulse whose timestamp is AFTER the precommit_time to ensure
    # design_before_anchor_ok = true. NIST publishes every 60s on the minute; wait until
    # we're past the next pulse boundary + margin, then fetch.
    print("Fetching NIST beacon witness (post-QPU; must be after precommit for freshness)...")
    # Parse precommit_time to determine the target pulse
    pc = datetime.fromisoformat(precommit_time.replace('Z', '+00:00'))
    target_pulse_time_str = (pc + timedelta(minutes=1)).replace(second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Poll with backoff until we get a pulse >= target (NIST /pulse/last has ~3min delay)
    nist_witness = None
    delays = [10, 15, 20, 30, 45, 60]  # cumulative ~180s = 3 minutes max
    for i, delay in enumerate(delays):
        candidate = fetch_nist_witness()
        if candidate["timeStamp"] > precommit_time:
            nist_witness = candidate
            break
        print(f"  pulse {candidate['pulseIndex']} at {candidate['timeStamp']} is before precommit; retry in {delay}s ({i+1}/{len(delays)})...")
        time.sleep(delay)
    
    if nist_witness is None:
        # Final attempt
        candidate = fetch_nist_witness()
        if candidate["timeStamp"] > precommit_time:
            nist_witness = candidate
        else:
            print(f"GATE-STOP: could not fetch a NIST pulse after precommit {precommit_time} within 180s")
            sys.exit(2)
    
    nist_pulse_time = nist_witness["timeStamp"]
    print(f"  NIST pulseIndex={nist_witness['pulseIndex']} ts={nist_pulse_time} (after precommit)")
    print("Fetching LIGO/GWOSC astro witness (GW150914 strain)...")
    astro_witness = fetch_astro_witness()
    print(f"  astro file_sha256={astro_witness['file_sha256'][:16]}... size={astro_witness['file_size_bytes']}B")

    chsh_result = compute_chsh(counts_by_setting)
    abs_S = chsh_result["abs_S"]
    sigmas = chsh_result["sigmas_above_classical"]
    bell_certified = bool(abs_S > 2.0 and sigmas >= SIGMA_THRESHOLD
                          and abs_S <= (chsh_result["tsirelson_bound"] + TSIRELSON_TOLERANCE))
    print(f"CHSH S = {chsh_result['S']:.4f} +/- {chsh_result['sigma_S']:.4f} "
          f"({sigmas:.1f} sigma over classical) -> bell_certified={bell_certified}")

    # === STEP 4: fuse nonce + freshness bracket + ProofRecord ===
    finalize_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    fused_nonce = compute_fused_nonce(precommit_hash, GENESIS_PREV_HASH, raw_counts,
                                      job_id, cal_snapshot, nist_witness, astro_witness)
    proofrecord = build_proofrecord(
        fused_nonce=fused_nonce, precommit_hash=precommit_hash,
        prev_record_hash=GENESIS_PREV_HASH, job_id=job_id, backend=backend.name,
        provider_instance=provider_instance,
        calibration_hash=compute_calibration_hash(cal_snapshot),
        raw_counts_hash=compute_raw_counts_hash(raw_counts),
        nist_hash=compute_nist_hash(nist_witness),
        astro_hash=compute_astro_hash(astro_witness),
        chsh_result=chsh_result, bell_certified=bell_certified, context_id=CONTEXT_ID,
        nist_pulse_time=nist_pulse_time, precommit_time_utc=precommit_time,
        timestamp_utc=finalize_time, prev_record_timestamp_utc=PREV_RECORD_TIMESTAMP_UTC)

    print(f"Freshness bracket: {json.dumps(proofrecord['freshness'])}")

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
            "precommit_time_utc": precommit_time,
            "selection_time_utc": selection_time,
            "submission_time_utc": submission_time,
            "nist_pulse_time_utc": nist_pulse_time,
            "finalize_time_utc": finalize_time,
            "channel": "ibm_cloud", "execution_mode": "Batch",
            "qiskit_version": "2.5.0", "qiskit_ibm_runtime_version": "0.48.0",
            "python_version": "3.11",
        }, f, indent=2)
    with open(RESULTS_DIR / "chsh_result.json", 'w') as f:
        json.dump(chsh_result, f, indent=2)
    with open(RESULTS_DIR / "proofrecord.json", 'w') as f:
        json.dump(proofrecord, f, indent=2)

    print("\n=== ProofRecord ===")
    print(json.dumps(proofrecord, indent=2))
    print("\nArtifacts saved to witness-4/results/")


if __name__ == "__main__":
    main()
