"""
WITNESS-3 CHSH Bell-test module.

Prepares the Bell state |Phi+> = (|00> + |11>)/sqrt(2) and measures the two qubits
in four setting pairs (a,b), (a,b'), (a',b), (a',b'). From the measured two-qubit
correlations E(alpha,beta) it computes the CHSH statistic

    S = E(a,b) - E(a,b') + E(a',b) + E(a',b')

Local hidden-variable (classical) theories obey |S| <= 2 (the CHSH inequality).
Quantum mechanics allows up to |S| = 2*sqrt(2) ~= 2.8284 (Tsirelson bound).

Preregistered optimal angles for |Phi+> (E(alpha,beta) = cos(alpha - beta)):
    Alice: a = 0,        a' = pi/2
    Bob:   b = pi/4,     b' = 3*pi/4
    -> ideal S = +2*sqrt(2).

Measurement realisation: to measure the observable cos(theta) Z + sin(theta) X on a
qubit, append RY(-theta) to that qubit and then measure in the computational (Z) basis.
Qiskit convention: ry(phi) applies exp(-i phi Y / 2); ry(-theta) followed by a Z-basis
measurement yields expectation <cos(theta) Z + sin(theta) X> on the pre-rotation state.
The sign is validated empirically by the simulator mock (must reproduce S ~ +2.83).

IMPORTANT SCIENTIFIC BOUNDARY (see prereg Non-Claims):
This is NOT a loophole-free Bell test. The two qubits are neighbouring transmons on one
chip (no space-like separation -> locality/communication loophole open), outcomes are
read out under a fair-sampling assumption (detection loophole open), and measurement
settings are fixed by the harness (freedom-of-choice loophole open). A violation here is
consistent with non-classical correlations on the tested device under the no-signalling
and fair-sampling assumptions; it is NOT a device-independent, loophole-free certification.
"""

import math
from typing import Dict, List, Tuple

# Preregistered measurement angles (radians)
ALICE_ANGLES = {"a": 0.0,            "a_prime": math.pi / 2.0}
BOB_ANGLES   = {"b": math.pi / 4.0,  "b_prime": 3.0 * math.pi / 4.0}

# The four preregistered setting pairs, in fixed order.
# Each tuple: (label, alice_angle, bob_angle, sign_in_S)
SETTINGS: List[Tuple[str, float, float, int]] = [
    ("ab",   ALICE_ANGLES["a"],       BOB_ANGLES["b"],       +1),  # +E(a,b)
    ("abp",  ALICE_ANGLES["a"],       BOB_ANGLES["b_prime"], -1),  # -E(a,b')
    ("apb",  ALICE_ANGLES["a_prime"], BOB_ANGLES["b"],       +1),  # +E(a',b)
    ("apbp", ALICE_ANGLES["a_prime"], BOB_ANGLES["b_prime"], +1),  # +E(a',b')
]

CLASSICAL_BOUND = 2.0
TSIRELSON_BOUND = 2.0 * math.sqrt(2.0)


def build_chsh_circuits(alice_qubit: int = 0, bob_qubit: int = 1):
    """
    Build the four CHSH measurement circuits on a 2-qubit register.
    Returns a list of (label, QuantumCircuit) in the fixed SETTINGS order.
    Requires qiskit (imported lazily so mock/analytic paths need no qiskit).
    """
    from qiskit import QuantumCircuit

    circuits = []
    for label, a_angle, b_angle, _sign in SETTINGS:
        qc = QuantumCircuit(2, 2)
        # Bell state |Phi+> on (alice_qubit, bob_qubit)
        qc.h(alice_qubit)
        qc.cx(alice_qubit, bob_qubit)
        # Measurement-basis rotations
        qc.ry(-a_angle, alice_qubit)
        qc.ry(-b_angle, bob_qubit)
        qc.measure(alice_qubit, 0)  # classical bit 0 = Alice
        qc.measure(bob_qubit, 1)    # classical bit 1 = Bob
        circuits.append((label, qc))
    return circuits


def correlator_from_counts(counts: Dict[str, int]) -> float:
    """
    E = [N(00) + N(11) - N(01) - N(10)] / N_total.
    Outcome bit 0 -> +1, bit 1 -> -1; correlation is the product of the two outcomes.
    Count keys are 2-character bit strings; the parity (XOR) of the two bits decides sign:
    even parity (00, 11) -> +1, odd parity (01, 10) -> -1.
    """
    total = sum(counts.values())
    if total == 0:
        raise ValueError("Empty counts: cannot compute correlator")
    agree = 0
    disagree = 0
    for bitstr, n in counts.items():
        b = bitstr.replace(" ", "")
        if len(b) != 2:
            raise ValueError(f"Expected 2-bit outcome, got {bitstr!r}")
        parity = (int(b[0]) ^ int(b[1]))
        if parity == 0:
            agree += n
        else:
            disagree += n
    return (agree - disagree) / total


def compute_chsh(counts_by_setting: Dict[str, Dict[str, int]]) -> dict:
    """
    Given a mapping {setting_label: counts_dict} for the four preregistered settings,
    compute the correlators, the CHSH S statistic, its standard error, and the
    violation significance in standard deviations above the classical bound of 2.

    Standard error model: each correlator E from N shots has Var(E) = (1 - E^2)/N
    (binomial on the +/-1 outcome). S is a fixed linear combination of four
    independent correlators, so Var(S) = sum Var(E_i) and sigma_S = sqrt(Var(S)).
    """
    correlators = {}
    var_S = 0.0
    S = 0.0
    per_setting = {}
    for label, _a, _b, sign in SETTINGS:
        if label not in counts_by_setting:
            raise KeyError(f"Missing counts for setting {label!r}")
        counts = counts_by_setting[label]
        N = sum(counts.values())
        E = correlator_from_counts(counts)
        correlators[label] = E
        S += sign * E
        var_E = (1.0 - E * E) / N if N > 0 else 0.0
        var_S += var_E  # sign^2 = 1
        per_setting[label] = {"E": E, "shots": N, "var_E": var_E, "sign_in_S": sign}

    sigma_S = math.sqrt(var_S) if var_S > 0 else 0.0
    violation = abs(S) - CLASSICAL_BOUND
    sigmas_above_classical = (violation / sigma_S) if sigma_S > 0 else float("inf")

    return {
        "S": S,
        "abs_S": abs(S),
        "sigma_S": sigma_S,
        "classical_bound": CLASSICAL_BOUND,
        "tsirelson_bound": TSIRELSON_BOUND,
        "violation_over_classical": violation,
        "sigmas_above_classical": sigmas_above_classical,
        "correlators": correlators,
        "per_setting": per_setting,
    }
