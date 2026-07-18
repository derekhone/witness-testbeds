"""
WITNESS-3 NIST Randomness Beacon (v2) witness.

Fetches one pulse from the NIST Interoperable Randomness Beacon and reduces it to a
deterministic, canonical record. The NIST beacon publishes a fresh 512-bit random value
every 60 seconds, each pulse cryptographically signed by NIST and chained to the previous
pulse. Public reference: https://beacon.nist.gov/ and NIST IR 8213.

We record the fields needed to independently re-fetch and verify the exact pulse:
  uri, version, chainIndex, pulseIndex, timeStamp, outputValue,
  signatureValue (truncated marker + full-hash), certificateId, and the sha256 of the
  full raw pulse JSON as returned by NIST.

Provenance note (preregistered): recording the pulse proves the nonce is bound to a
NIST-published, publicly re-verifiable beacon value at a specific time. It does not
re-run NIST's signature verification chain in this harness; the signatureValue and
certificateId are recorded so any auditor can verify the signature against NIST's
published certificate.
"""

import hashlib
import json
import urllib.request

BEACON_LAST_URL = "https://beacon.nist.gov/beacon/2.0/pulse/last"
BEACON_INDEX_URL = "https://beacon.nist.gov/beacon/2.0/pulse/{index}"


def _http_get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "witness-3/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")), raw


def build_nist_witness_record(pulse_json: dict, raw_bytes: bytes) -> dict:
    """Reduce a raw NIST pulse JSON to the deterministic witness record."""
    p = pulse_json["pulse"]
    sig = p.get("signatureValue", "") or ""
    return {
        "source": "nist_randomness_beacon_v2",
        "uri": p.get("uri"),
        "version": p.get("version"),
        "chainIndex": p.get("chainIndex"),
        "pulseIndex": p.get("pulseIndex"),
        "timeStamp": p.get("timeStamp"),
        "outputValue": p.get("outputValue"),
        "certificateId": p.get("certificateId"),
        # Full signature is long; store its sha256 plus a short prefix marker so the
        # witness record stays compact but the signature is still committed-to.
        "signatureValue_sha256": hashlib.sha256(sig.encode("utf-8")).hexdigest(),
        "signatureValue_prefix": sig[:32],
        # Hash of the exact bytes NIST returned (whole pulse object) for byte-level audit.
        "raw_pulse_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }


def fetch_nist_witness(index: int | None = None, timeout: int = 30) -> dict:
    """
    Fetch a NIST beacon pulse (latest by default, or a specific pulseIndex) and return
    the deterministic witness record. Network errors propagate to the caller (harness
    treats provider/network unavailability as GATE-STOP, not FAIL).
    """
    url = BEACON_LAST_URL if index is None else BEACON_INDEX_URL.format(index=index)
    pulse_json, raw_bytes = _http_get_json(url, timeout=timeout)
    return build_nist_witness_record(pulse_json, raw_bytes)


if __name__ == "__main__":
    rec = fetch_nist_witness()
    print(json.dumps(rec, indent=2, sort_keys=True))
