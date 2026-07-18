#!/usr/bin/env python3
"""Publish WITNESS-3 (Cosmic Beacon) to Zenodo."""
import requests
import json
import os
from pathlib import Path

# Load Zenodo token from secrets
secrets_path = Path.home() / ".config" / "abacusai_auth_secrets.json"
with open(secrets_path) as f:
    secrets = json.load(f)
ZENODO_TOKEN = secrets["zenodo"]["secrets"]["api_token"]["value"]

ZENODO_API = "https://zenodo.org/api/deposit/depositions"
WITNESS_CONCEPT_DOI = "10.5281/zenodo.21424323"  # WITNESS series concept DOI

# Experiment metadata
title = "WITNESS-3 — Cosmic Beacon: CHSH Bell + NIST + LIGO/GWOSC Fused Authorization Nonce"
description = f"""<p><strong>WITNESS-3 "Cosmic Beacon"</strong> — Remnant Fieldworks Inc. ExecutionProof research program.</p>

<p>Fuses <strong>three independent, publicly re-verifiable physical witnesses</strong> into a single ExecutionProof authorization nonce:</p>
<ol>
<li><strong>CHSH Bell-inequality violation</strong> measured on a real IBM QPU (certifies quantum non-classicality AND seeds the nonce)</li>
<li><strong>NIST public Randomness Beacon</strong> pulse (timestamped, signed random value)</li>
<li><strong>LIGO/GWOSC gravitational-wave data</strong> (GW150914, byte-exact open astrophysical data)</li>
</ol>

<p><strong>Execution:</strong> Job <code>d9dvul2neu4c739nrdl0</code>, backend <code>ibm_fez</code>, 8000 shots (4 CHSH settings × 2000)</p>

<p><strong>CHSH Bell Test:</strong> S = 2.545 ± 0.0345 → <strong>15.8 σ above classical bound</strong> → <strong>Bell-certified = TRUE</strong></p>

<p><strong>External Witnesses:</strong></p>
<ul>
<li>NIST Beacon pulse #1865471 (2026-07-18T22:31:00Z)</li>
<li>LIGO/GWOSC GW150914 H1 strain, 4096 samples @ offset 65536, file SHA-256 <code>66c4b196...</code></li>
</ul>

<p><strong>Cosmic Nonce:</strong> <code>6876050a7f8ebadf79b1bd702346ae42563019725c03d29bd8d26dadc8c7f686</code><br>
<strong>Record Hash:</strong> <code>858ffd49fd7517fd58ef242226bd7c680bb5db5850a34256fedffd76df0f1caf</code></p>

<p><strong>Verdicts (all PASS):</strong></p>
<table>
<tr><th>Case</th><th>Description</th><th>Verdict</th></tr>
<tr><td>W3-C4</td><td>CHSH Bell certification</td><td>✅ PASS (S=2.545, 15.8σ, bell_certified=true)</td></tr>
<tr><td>W3-C2</td><td>Tamper detection (6 sub-trials)</td><td>✅ PASS (all forgeries detected)</td></tr>
<tr><td>W3-C3</td><td>Replay prevention (2 sub-cases)</td><td>✅ PASS (both denied)</td></tr>
<tr><td>W3-C1</td><td>Honest verify (13 checks)</td><td>✅ PASS (provider job found, counts match)</td></tr>
</table>

<p><strong>Honesty Bounds:</strong> NOT loophole-free (neighboring transmons, no spacelike separation). NOT device-independent (fair-sampling, no-signalling assumed). Astro witness is provenance only (NOT a detection claim). Findings bound to tested backend/qubits/calibration/shots.</p>

<p><strong>Harness Fix (post-lock, disclosed):</strong> FIX-W3-1 (<code>submit_job.py</code> line 63): <code>channel="ibm_quantum_platform"</code> → <code>"ibm_cloud"</code> to match working IBM endpoint for open-instance.</p>

<p><em>Covenant: outcomes preserved as measured; claims bounded to the tested conditions. Research experiment demonstrating verifiable-provenance quantum-sourced nonces — NOT legal, patent, security, or production certification. Soli Deo Gloria.</em></p>
"""

creators = [
    {"name": "Hone, Derek Adam", "affiliation": "Remnant Fieldworks Inc."}
]

# GitHub repo reference
related_identifiers = [
    {"identifier": WITNESS_CONCEPT_DOI, "relation": "isPartOf", "scheme": "doi"},  # Part of WITNESS concept
    {"identifier": "https://github.com/derekhone/witness-testbeds", "relation": "isSupplementTo", "scheme": "url"},
]

keywords = [
    "ExecutionProof",
    "quantum-sourced nonce",
    "CHSH Bell inequality",
    "NIST randomness beacon",
    "LIGO gravitational wave",
    "verifiable provenance",
    "authorization boundary",
    "Remnant Fieldworks"
]

print(f"{'='*70}\nPublishing WITNESS-3 to Zenodo\n{'='*70}")

# Step 1: Create new deposition
params = {"access_token": ZENODO_TOKEN}
headers = {"Content-Type": "application/json"}

r = requests.post(ZENODO_API, json={}, params=params, headers=headers)
if r.status_code != 201:
    print(f"❌ FAIL create deposition: {r.status_code}")
    print(r.text[:500])
    exit(1)

dep = r.json()
dep_id = dep["id"]
bucket_url = dep["links"]["bucket"]
print(f"✅ Created deposition {dep_id}")

# Step 2: Upload tarball
tarball_path = "witness-3.tar.gz"
tarball_name = "witness-3.tar.gz"

with open(tarball_path, "rb") as f:
    r = requests.put(f"{bucket_url}/{tarball_name}", data=f, params=params)
if r.status_code != 200 and r.status_code != 201:
    print(f"❌ FAIL upload tarball: {r.status_code}")
    print(r.text[:500])
    exit(1)

print(f"✅ Uploaded {tarball_name} ({os.path.getsize(tarball_path)} bytes)")

# Step 3: Set metadata
metadata = {
    "metadata": {
        "title": title,
        "upload_type": "dataset",
        "description": description,
        "creators": creators,
        "keywords": keywords,
        "related_identifiers": related_identifiers,
        "access_right": "open",
        "license": "cc-by-4.0"
    }
}

r = requests.put(f"{ZENODO_API}/{dep_id}", json=metadata, params=params, headers=headers)
if r.status_code != 200:
    print(f"❌ FAIL set metadata: {r.status_code}")
    print(r.text[:500])
    exit(1)

print(f"✅ Metadata set")

# Step 4: Publish
r = requests.post(f"{ZENODO_API}/{dep_id}/actions/publish", params=params)
if r.status_code != 202:
    print(f"❌ FAIL publish: {r.status_code}")
    print(r.text[:500])
    exit(1)

final = r.json()
doi = final.get("doi", "")
doi_url = final.get("doi_url", "")
record_url = final["links"]["record_html"]

print(f"\n{'='*70}")
print(f"✅ PUBLISHED")
print(f"{'='*70}")
print(f"DOI: {doi}")
print(f"DOI URL: {doi_url}")
print(f"Record URL: {record_url}")
print(f"{'='*70}\n")

# Write result to JSON
result = {
    "witness-3": {
        "deposition_id": dep_id,
        "doi": doi,
        "doi_url": doi_url,
        "record_url": record_url,
        "status": "published"
    }
}

with open("zenodo_witness3_result.json", "w") as f:
    json.dump(result, f, indent=2)

print("✅ Result saved to zenodo_witness3_result.json")
