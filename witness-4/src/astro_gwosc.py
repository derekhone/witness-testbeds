"""
WITNESS-3 astrophysical witness — LIGO/GWOSC open science data.

Binds the nonce to a fixed, public gravitational-wave strain data file from the Gravitational
Wave Open Science Center (GWOSC, https://gwosc.org). Default: the 32-second, 4096 Hz H1
strain file around GW150914 — the first direct detection of gravitational waves
(Abbott et al., PRL 116, 061102, 2016), the merger of two black holes ~1.3 billion light
years away.

The witness record commits to:
  - the exact public URL,
  - the SHA-256 of the exact file bytes (byte-level provenance anchor),
  - the file size,
  - GW event name, detector, GPS start, duration, sample rate,
  - a deterministic digest of a fixed window of strain samples (SHA-256 over the
    canonical repr of N samples starting at a fixed offset), so the record is bound to
    the actual physical strain time-series, not merely to file metadata.

SCIENTIFIC BOUNDARY (preregistered Non-Claim): the strain file is used purely as a
PUBLIC, RE-VERIFIABLE PROVENANCE WITNESS. WITNESS-3 does NOT detect gravitational waves,
does NOT re-derive the astrophysical parameters, and makes NO cosmological claim. It binds
the nonce to real, published detector data that anyone can re-download and hash.
"""

import hashlib
import json
import urllib.request

# GW150914 — first detection. 32 s, 4096 Hz, H1 detector (GWOSC event-hosted file).
DEFAULT_ASTRO = {
    "event": "GW150914",
    "detector": "H1",
    "gps_start": 1126259446,
    "duration_s": 32,
    "sample_rate_hz": 4096,
    "reference": "Abbott et al., PRL 116, 061102 (2016)",
    "url": "https://gwosc.org/s/events/GW150914/H-H1_LOSC_4_V1-1126259446-32.hdf5",
}

# Deterministic strain-sample window (fixed so the digest is reproducible).
SAMPLE_OFFSET = 65536      # start index into the strain array
SAMPLE_COUNT = 4096        # number of samples (1 second at 4096 Hz)
SAMPLE_QUANTIZE = 1e-24    # quantisation step so float repr is byte-stable across platforms


def _http_get_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "witness-3/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _strain_sample_digest(file_bytes: bytes) -> dict:
    """
    Read the strain dataset from the HDF5 bytes and compute a deterministic digest over a
    fixed window of samples. Returns the digest plus provenance of the window.
    Requires h5py; if unavailable, returns a digest over the raw file bytes window instead
    (still deterministic and re-verifiable), flagged by 'method'.
    """
    try:
        import io
        import h5py
        import numpy as np
        with h5py.File(io.BytesIO(file_bytes), "r") as f:
            strain = f["strain"]["Strain"][:]
        window = strain[SAMPLE_OFFSET:SAMPLE_OFFSET + SAMPLE_COUNT]
        # Quantise to integers for byte-stable canonicalisation, then hash.
        quant = [int(round(float(x) / SAMPLE_QUANTIZE)) for x in window]
        digest = hashlib.sha256(
            json.dumps(quant, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {
            "method": "hdf5_strain_window",
            "sample_offset": SAMPLE_OFFSET,
            "sample_count": len(quant),
            "quantize_step": SAMPLE_QUANTIZE,
            "n_total_samples": int(len(strain)),
            "strain_window_sha256": digest,
        }
    except Exception as e:
        # Fallback: deterministic window over the raw file bytes.
        window = file_bytes[SAMPLE_OFFSET:SAMPLE_OFFSET + SAMPLE_COUNT]
        return {
            "method": "raw_byte_window_fallback",
            "fallback_reason": str(e),
            "byte_offset": SAMPLE_OFFSET,
            "byte_count": len(window),
            "strain_window_sha256": hashlib.sha256(window).hexdigest(),
        }


def build_astro_witness_record(meta: dict, file_bytes: bytes) -> dict:
    """Reduce a downloaded strain file + metadata to the deterministic witness record."""
    rec = {
        "source": "ligo_gwosc_open_data",
        "event": meta["event"],
        "detector": meta["detector"],
        "gps_start": meta["gps_start"],
        "duration_s": meta["duration_s"],
        "sample_rate_hz": meta["sample_rate_hz"],
        "reference": meta["reference"],
        "url": meta["url"],
        "file_size_bytes": len(file_bytes),
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
    }
    rec["strain_sample"] = _strain_sample_digest(file_bytes)
    return rec


def fetch_astro_witness(meta: dict | None = None, timeout: int = 120) -> dict:
    """
    Download the public GWOSC strain file and return the deterministic witness record.
    Network errors propagate (harness treats provider/network unavailability as GATE-STOP).
    """
    meta = meta or DEFAULT_ASTRO
    file_bytes = _http_get_bytes(meta["url"], timeout=timeout)
    return build_astro_witness_record(meta, file_bytes)


if __name__ == "__main__":
    rec = fetch_astro_witness()
    print(json.dumps(rec, indent=2, sort_keys=True))
