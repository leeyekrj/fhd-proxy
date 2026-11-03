#!/usr/bin/env python3
import os, subprocess, tempfile, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="proxy-installer-") as temporary:
    base=Path(temporary); tools=base/"tools";tools.mkdir()
    curl=tools/"curl";curl.write_text('#!/bin/bash\nset -eu\noutput=\'\'; url=\'\'\nwhile [ "$#" -gt 0 ]; do\n case "$1" in -o) output="$2"; shift 2;; --retry|--proto|--tlsv1.2) if [ "$1" = --tlsv1.2 ]; then shift; else shift 2; fi;; https://*) url="$1"; shift;; *) shift;; esac\ndone\ncp "$TEUM_TEST_ASSETS/${url##*/}" "$output"\n');curl.chmod(0o755)
    env=dict(os.environ,PATH=str(tools)+":"+os.environ["PATH"],TEUM_TEST_ASSETS=str(root/"dist"))
    target=base/"bin with spaces 'test'"; skills=base/"skills"
    command=["bash",str(root/"install.sh"),"--bin-dir",str(target)]
    def run(ok=True, extra=()):
        result=subprocess.run(command+list(extra),env=env,text=True,capture_output=True)
        assert (result.returncode==0)==ok,result.stdout+result.stderr
        return result
    run(extra=["--skill-dir",str(skills)])
    assert (skills/"fhd-proxy/SKILL.md").is_file()
    assert subprocess.check_output([str(target/"fhd-proxy"),"--version"],text=True).strip()=="1.0.0"
    run()
    run(False,["--skill-dir",str(skills)])
    (target/"fhd-proxy").write_text("unrelated user file")
    run(False)
    assert (target/"fhd-proxy").read_text()=="unrelated user file"
print("PASS: CLI install/update, quoted paths, skill install, existing skill/file preservation")
