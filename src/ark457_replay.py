"""
ark457_replay.py — Cross-context replay protection, derived from ARK-457 construction.

Source: ARK-457 (DOI 10.5281/zenodo.21421742), Remnant Fieldworks ExecutionProof series.
        Imported here as a library module; NOT a fork of executionproof-testbeds.

Construction: 5-dimensional context tuple (tenant, session, resource, audience, environment).
Authorization is ALLOW only on exact byte/code-point match across all 5 dimensions.
Any mismatch on any dimension → DENY.
No normalization is applied (case, whitespace, zero-width, homoglyphs all produce DENY).
"""

from typing import NamedTuple


class AuthContext(NamedTuple):
    """Five-dimensional authorization context tuple (ARK-457 construction)."""
    tenant: str
    session: str
    resource: str
    audience: str
    environment: str


class ReplayVerdict(NamedTuple):
    decision: str      # "ALLOW" or "DENY"
    reason: str
    mismatched_dims: list  # which dimensions differed (empty on ALLOW)


def check_context_replay(
    original_context: AuthContext,
    presented_context: AuthContext,
) -> ReplayVerdict:
    """
    Evaluate whether a presented context is a valid re-use or a cross-context replay.

    Per ARK-457 construction:
    - ALLOW iff ALL 5 dimensions match exactly (byte/code-point equality).
    - DENY iff ANY dimension mismatches.
    - No normalization.

    Args:
        original_context: the context under which the ProofRecord was issued
        presented_context: the context in which authorization is being requested

    Returns:
        ReplayVerdict with decision, reason, and list of mismatched dimensions
    """
    dims = ["tenant", "session", "resource", "audience", "environment"]
    mismatches = [
        dim for dim in dims
        if getattr(original_context, dim) != getattr(presented_context, dim)
    ]

    if not mismatches:
        return ReplayVerdict(
            decision="ALLOW",
            reason="All 5 context dimensions match exactly.",
            mismatched_dims=[],
        )
    else:
        mismatch_detail = "; ".join(
            f"{dim}: original={repr(getattr(original_context, dim))} "
            f"presented={repr(getattr(presented_context, dim))}"
            for dim in mismatches
        )
        return ReplayVerdict(
            decision="DENY",
            reason=f"Cross-context replay detected. Mismatched dimension(s): {mismatch_detail}",
            mismatched_dims=mismatches,
        )


def verify_no_replay(
    original_context: AuthContext,
    presented_context: AuthContext,
) -> bool:
    """
    Convenience wrapper: returns True iff the presented context is NOT a replay
    (i.e., decision == ALLOW). Returns False on any mismatch.
    """
    verdict = check_context_replay(original_context, presented_context)
    return verdict.decision == "ALLOW"
