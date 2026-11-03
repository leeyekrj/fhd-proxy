import argparse
import hashlib
import importlib.machinery
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "bin/fhd-proxy"
loader = importlib.machinery.SourceFileLoader("proxy", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
p = importlib.util.module_from_spec(spec)
loader.exec_module(p)


class ProxyTests(unittest.TestCase):
    def test_name_collisions_are_rejected_before_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.mov").touch(); (folder / "a.mp4").touch()
            with self.assertRaisesRegex(ValueError, "충돌"):
                p.jobs([tmp], None)

    def test_shape_and_no_upscale(self):
        self.assertEqual(p.dimensions(3840, 2160), (1920, 1080))
        self.assertEqual(p.dimensions(2160, 3840), (606, 1080))
        self.assertEqual(p.dimensions(640, 480), (640, 480))

    def test_no_guessed_color(self):
        self.assertEqual(p.color_options({}), [])
        self.assertNotIn("bt709", p.color_options({"color_range": "pc"}))

    def test_real_roundtrip_and_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); source = folder / "원본 test.mov"; dst = folder / "output" / "원본 test.mov"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=24", "-f", "lavfi", "-i", "sine=frequency=440", "-t", "1", "-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-x265-params", "pools=2:log-level=error", "-color_range", "pc", "-colorspace", "bt2020nc", "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-c:a", "aac", "-timecode", "01:00:00:00", str(source)], check=True)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            args = argparse.Namespace(encoder="hevc_videotoolbox", quality=75)
            p.convert(source, dst, args)
            self.assertTrue(dst.exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            proxy_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError, "덮어쓰지"):
                p.convert(source, dst, args)
            self.assertEqual(hashlib.sha256(dst.read_bytes()).hexdigest(), proxy_hash)
            self.assertFalse(list(dst.parent.glob(".fhd-proxy-*")))
            bad = folder / "broken.mov"; bad.write_bytes(b"broken")
            result = subprocess.run([str(CLI), str(bad)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse((folder / "Proxy/broken.mov").exists())


if __name__ == "__main__":
    unittest.main()
