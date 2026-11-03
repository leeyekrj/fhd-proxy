#!/usr/bin/env python3
from pathlib import Path
import tarfile, hashlib
root = Path(__file__).resolve().parents[1]
dist = root / "dist"; dist.mkdir(exist_ok=True)
asset = dist / "fhd-proxy-1.0.0.tar.gz"
with tarfile.open(asset, "w:gz") as archive:
    for name in ["bin/fhd-proxy", "skills/fhd-proxy/SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md"]:
        archive.add(root / name, arcname=name)
(dist / "SHA256SUMS.txt").write_text(hashlib.sha256(asset.read_bytes()).hexdigest() + "  " + asset.name + "\n")
print(asset)
