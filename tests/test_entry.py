"""Tests for the news-image-20261126 entry.

Run: python3 -m pytest tests/ -q   (or: python3 tests/test_entry.py)
Checks the gate rules from RULES.txt: PNG, <=1 MiB, <=1024x1024,
deterministic double run of main.ts, README badges, LICENSE SPDX.
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(33)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", head[16:24])
    return w, h


class EntryTests(unittest.TestCase):
    def test_entry_png_exists_and_valid(self):
        p = os.path.join(REPO, "entry.png")
        self.assertTrue(os.path.exists(p), "entry.png missing")
        self.assertLessEqual(os.path.getsize(p), 1048576, "entry.png over 1 MiB")
        w, h = png_size(p)
        self.assertLessEqual(w, 1024)
        self.assertLessEqual(h, 1024)
        self.assertGreater(w, 500)
        self.assertGreater(h, 500)

    def test_main_ts_copies_entry(self):
        src = open(os.path.join(REPO, "main.ts")).read()
        self.assertIn("entry.png", src)
        self.assertIn("MAKEFUN_OUTPUT_DIR", src)

    def test_main_ts_two_runs_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for i in range(2):
                outdir = os.path.join(d, f"out{i}")
                os.makedirs(outdir)
                env = dict(os.environ, MAKEFUN_OUTPUT_DIR=outdir)
                r = subprocess.run(
                    ["node", "main.ts"], cwd=REPO, env=env,
                    capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                with open(os.path.join(outdir, "entry.png"), "rb") as fh:
                    data = fh.read()
                outs.append(data)
            self.assertEqual(outs[0], outs[1], "two runs differ")
            with open(os.path.join(REPO, "entry.png"), "rb") as fh:
                repo_bytes = fh.read()
            self.assertEqual(outs[0], repo_bytes, "output differs from repo entry.png")
            h = hashlib.sha256(outs[0]).hexdigest()
            print(f"entry.png sha256={h} bytes={len(outs[0])}")

    def test_readme_has_three_badges(self):
        readme = open(os.path.join(REPO, "README.md")).read()
        self.assertIn("https://make.fun/badge/news-image-20261126.svg", readme)
        self.assertIn(
            "https://make.fun/badge/news-image-20261126/lively-panda-61/news-image-20261126/rank.svg",
            readme,
        )
        self.assertIn(
            "https://make.fun/badge/news-image-20261126/lively-panda-61/news-image-20261126/reward.svg",
            readme,
        )
        self.assertNotIn("{owner}", readme)
        self.assertNotIn("{repo}", readme)
        self.assertIn("26 November 2026", readme)

    def test_license_spdx_first_line(self):
        lic = open(os.path.join(REPO, "LICENSE")).read()
        self.assertTrue(
            lic.splitlines()[0].strip() == "SPDX-License-Identifier: MIT",
            "LICENSE first line must be the SPDX identifier",
        )
        self.assertIn("MIT License", lic)

    def test_no_secrets_in_repo(self):
        bad = ["af_", "api_key", "API_KEY", "BEGIN PRIVATE KEY", "keypair"]
        for root, dirs, files in os.walk(REPO):
            dirs[:] = [d for d in dirs if d != ".git"]
            for fn in files:
                if fn == "test_entry.py":
                    continue
                p = os.path.join(root, fn)
                if fn.endswith(".png"):
                    continue
                txt = open(p, errors="ignore").read()
                for token in bad:
                    self.assertNotIn(token, txt, f"{token} found in {p}")

    def test_render_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for i in range(2):
                out = os.path.join(d, f"r{i}.png")
                r = subprocess.run(
                    [sys.executable, "tools/render.py", "--out", out],
                    cwd=REPO, capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                with open(out, "rb") as fh:
                    outs.append(fh.read())
            self.assertEqual(outs[0], outs[1], "render not deterministic")


if __name__ == "__main__":
    unittest.main(verbosity=2)
