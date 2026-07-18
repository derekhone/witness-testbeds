"""
WITNESS-4 freshness-bracket verification.

Given a finalized ProofRecord and its source witnesses, this module evaluates the
temporal bracket that makes the record non-backdatable:

    precommit_time_utc  <=  nist_pulse_time  <=  finalize_time (timestamp_utc)

Verifiable invariants (all timestamps are ISO-8601 UTC, parsed to aware datetimes):

  1. NOT-BEFORE bound:   timestamp_utc >= nist_pulse_time
       The record commits (inside its fused nonce) to a NIST beacon outputValue that was
       not published until nist_pulse_time. A record finalized/effective before that time
       is impossible -> a claimed earlier effective time is a backdating forgery.

  2. DESIGN-BEFORE-ANCHOR:  precommit_time_utc <= nist_pulse_time
       The pre-commitment (which fixes circuit + intent + context + prev link) was hashed
       before the beacon value was known. If the recorded precommit_time is AFTER the
       pulse, the "design fixed independently of the anchor" claim fails.

  3. CHAIN ORDER (advisory): if the previous ledger record's timestamp is supplied, the
       current record's timestamp must be >= it (append-only monotonic ledger).

Returns a dict of individual boolean checks plus an overall `fresh` flag. This module is
pure/offline; it makes no network calls. Honesty note: it establishes a *lower* time
bound only (no upper bound exists), and relies on NIST publishing the pulse — it is not a
notarization authority.
"""

from datetime import datetime, timezone


def parse_iso_utc(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp to an aware UTC datetime. Accepts trailing 'Z'."""
    if ts is None:
        raise ValueError("timestamp is None")
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def evaluate_freshness(
    record_timestamp_utc: str,
    nist_pulse_time: str,
    precommit_time_utc: str,
    prev_record_timestamp_utc: str | None = None,
) -> dict:
    """Evaluate the freshness bracket. All args are ISO-8601 UTC strings."""
    t_rec = parse_iso_utc(record_timestamp_utc)
    t_pulse = parse_iso_utc(nist_pulse_time)
    t_pre = parse_iso_utc(precommit_time_utc)

    checks = {
        "not_before_bound_ok": t_rec >= t_pulse,          # invariant 1
        "design_before_anchor_ok": t_pre <= t_pulse,      # invariant 2
    }
    if prev_record_timestamp_utc is not None:
        t_prev = parse_iso_utc(prev_record_timestamp_utc)
        checks["chain_monotonic_ok"] = t_rec >= t_prev    # invariant 3
    checks["fresh"] = all(v for v in checks.values())
    return checks


if __name__ == "__main__":
    import json
    ok = evaluate_freshness(
        record_timestamp_utc="2026-07-18T23:00:00Z",
        nist_pulse_time="2026-07-18T22:59:00Z",
        precommit_time_utc="2026-07-18T22:50:00Z",
    )
    print(json.dumps(ok, indent=2))
    bad = evaluate_freshness(  # backdated: record claims a time before the pulse
        record_timestamp_utc="2026-07-18T22:00:00Z",
        nist_pulse_time="2026-07-18T22:59:00Z",
        precommit_time_utc="2026-07-18T22:50:00Z",
    )
    print(json.dumps(bad, indent=2))
