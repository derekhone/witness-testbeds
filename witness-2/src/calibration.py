"""
WITNESS-2 deterministic calibration snapshot extractor.

All 10 schema fields always present. Missing values -> None (not omitted).
Non-finite floats (nan, inf, -inf) replaced with None.
Keys in dicts sorted lexicographically by canonical_json.

Schema:
  backend_name               : str
  backend_version            : str | None
  last_update_utc            : str (ISO 8601 second-precision UTC) | None
  basis_gates                : [str] sorted lexicographically
  selected_qubits            : [int] sorted ascending
  readout_error_by_qubit     : {"<qubit_idx>": float | None}
  t1_by_qubit                : {"<qubit_idx>": float | None}  (seconds)
  t2_by_qubit                : {"<qubit_idx>": float | None}  (seconds)
  gate_error_for_used_gates  : {"<gate>_q<idx>": float | None}
  gate_length_for_used_gates : {"<gate>_q<idx>": float | None} (seconds)
"""

import math

USED_GATES = ['h', 'measure']


def _clean(v):
    """Replace non-finite float with None; pass through everything else."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def extract_calibration_snapshot(backend, selected_qubits: list) -> dict:
    """
    Extract a deterministic calibration snapshot from a Qiskit backend object.
    selected_qubits: list of integer qubit indices used in the circuit (will be sorted).
    """
    props  = backend.properties()
    config = backend.configuration()
    selected_qubits = sorted(selected_qubits)

    # last_update_utc: second-precision ISO 8601 UTC
    last_update = None
    if hasattr(props, 'last_update_date') and props.last_update_date is not None:
        try:
            last_update = props.last_update_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            last_update = str(props.last_update_date)

    readout_error, t1, t2 = {}, {}, {}
    for q in selected_qubits:
        qstr = str(q)
        try:    readout_error[qstr] = _clean(props.readout_error(q))
        except Exception: readout_error[qstr] = None
        try:    t1[qstr] = _clean(props.t1(q))
        except Exception: t1[qstr] = None
        try:    t2[qstr] = _clean(props.t2(q))
        except Exception: t2[qstr] = None

    gate_error, gate_length = {}, {}
    for gate in USED_GATES:
        for q in selected_qubits:
            key = f"{gate}_q{q}"
            try:    gate_error[key] = _clean(props.gate_error(gate, q))
            except Exception: gate_error[key] = None
            try:    gate_length[key] = _clean(props.gate_length(gate, q))
            except Exception: gate_length[key] = None

    return {
        "backend_name":               backend.name,
        "backend_version":            getattr(config, 'backend_version', None),
        "last_update_utc":            last_update,
        "basis_gates":                sorted(config.basis_gates),
        "selected_qubits":            selected_qubits,
        "readout_error_by_qubit":     readout_error,
        "t1_by_qubit":                t1,
        "t2_by_qubit":                t2,
        "gate_error_for_used_gates":  gate_error,
        "gate_length_for_used_gates": gate_length,
    }
