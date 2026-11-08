"""CLI tests that need no display."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from envy_crypto import cli


class CLITest(unittest.TestCase):
    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            cli.main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("envy-crypto", out.getvalue())

    def test_run_operation_on_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.txt"; src.write_bytes(b"Hello")
            dst = Path(tmp) / "out.txt"
            code, out, _ = self.invoke("run", "--op", "base64-encode", src, dst)
            self.assertEqual(code, 0)
            self.assertEqual(dst.read_bytes(), b"SGVsbG8=")

    def test_analyze_prints_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "c.txt"; src.write_bytes(b"Uryyb")
            code, out, _ = self.invoke("analyze", src)
            self.assertEqual(code, 0)
            report = json.loads(out)
            self.assertEqual(report["bytes"], 5)
            self.assertIn("rot_candidates", report)

    def test_bad_operation_input_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "x.txt"; src.write_bytes(b"not hex zz")
            dst = Path(tmp) / "y.bin"
            code, _, err = self.invoke("run", "--op", "hex-decode", src, dst)
            self.assertEqual(code, 2)
            self.assertIn("not valid", err.lower())

    def test_unknown_command(self):
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args(["enigma"])

    def test_recipe_trace_prints_each_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.txt"; src.write_bytes(b"Hello")
            rec = Path(tmp) / "r.json"
            rec.write_text(json.dumps({"schema": 1,
                                       "steps": [{"op": "rot", "shift": 13}, {"op": "base64-encode"}]}))
            dst = Path(tmp) / "out.txt"
            code, out, _ = self.invoke("recipe", "--recipe", rec, src, dst, "--trace")
            self.assertEqual(code, 0)
            self.assertIn("1. rot shift=13", out)
            self.assertIn("2. base64-encode", out)
            self.assertIn("sha256", out)
            self.assertEqual(dst.read_bytes(), b"VXJ5eWI=")       # rot13 "Hello"->"Uryyb"->base64

    def test_recipe_without_trace_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.txt"; src.write_bytes(b"Hello")
            rec = Path(tmp) / "r.json"
            rec.write_text(json.dumps({"schema": 1, "steps": [{"op": "base64-encode"}]}))
            dst = Path(tmp) / "out.txt"
            code, out, _ = self.invoke("recipe", "--recipe", rec, src, dst)
            self.assertEqual(code, 0)
            self.assertNotIn("sha256", out)


if __name__ == "__main__":
    unittest.main()
