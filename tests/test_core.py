"""Core operation, analysis and recipe tests. Standard library only."""

from pathlib import Path
import tempfile
import unittest

from envy_crypto import core


class OperationTest(unittest.TestCase):
    def test_base64_round_trip(self):
        data = b"The quick brown fox \xff\x00"
        self.assertEqual(core.operation("base64-decode", core.operation("base64-encode", data)), data)

    def test_hex_round_trip(self):
        data = bytes(range(256))
        self.assertEqual(core.operation("hex-decode", core.operation("hex-encode", data)), data)

    def test_rot13_known_vector(self):
        self.assertEqual(core.operation("rot", b"Hello, World!", 13), b"Uryyb, Jbeyq!")
        self.assertEqual(core.operation("rot", b"Uryyb, Jbeyq!", 13), b"Hello, World!")

    def test_atbash_is_its_own_inverse(self):
        self.assertEqual(core.operation("atbash", b"Attack at dawn"), b"Zggzxp zg wzdm")
        self.assertEqual(core.operation("atbash", core.operation("atbash", b"Secrets")), b"Secrets")

    def test_base32_round_trip(self):
        data = b"ENVY cryptography workbench \x00\x01"
        self.assertEqual(core.operation("base32-decode", core.operation("base32-encode", data)), data)

    def test_url_encode_round_trip_and_vector(self):
        self.assertEqual(core.operation("url-encode", b"a b&c=/?"), b"a%20b%26c%3D%2F%3F")
        data = "key = café/2".encode("utf-8")
        self.assertEqual(core.operation("url-decode", core.operation("url-encode", data)), data)

    def test_rot47_is_its_own_inverse_and_vector(self):
        self.assertEqual(core.operation("rot47", b"Hello, World!"), b"w6==@[ (@C=5P")
        self.assertEqual(core.operation("rot47", core.operation("rot47", b"Secrets 123")), b"Secrets 123")

    def test_reverse_handles_unicode(self):
        self.assertEqual(core.operation("reverse", "café".encode()), "éfac".encode())

    def test_rot_shift_bounds(self):
        with self.assertRaises(core.CryptoError):
            core.operation("rot", b"x", 99)
        with self.assertRaises(core.CryptoError):
            core.operation("rot", b"x", True)

    def test_bad_base64_is_rejected(self):
        with self.assertRaises(core.CryptoError):
            core.operation("base64-decode", b"not valid base64 !!!")

    def test_unknown_operation(self):
        with self.assertRaises(core.CryptoError):
            core.operation("enigma", b"x")


class AnalyzeTest(unittest.TestCase):
    def test_reports_entropy_and_rot_candidates(self):
        report = core.analyze(b"Uryyb Jbeyq")  # ROT13 of "Hello World"
        self.assertEqual(report["bytes"], 11)
        self.assertEqual(len(report["rot_candidates"]), 26)
        self.assertEqual(report["rot_candidates"][13]["preview"], "Hello World")
        self.assertGreater(report["entropy_bits_per_byte"], 0)

    def test_empty_input(self):
        report = core.analyze(b"")
        self.assertEqual(report["bytes"], 0)
        self.assertEqual(report["entropy_bits_per_byte"], 0)


class RecipeTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="envy-crypto-"))
        self.addCleanup(__import__("shutil").rmtree, self.dir)

    def test_run_steps_chains_operations(self):
        steps = [{"op": "base64-encode"}, {"op": "rot", "shift": 5}]
        result, trace = core.run_steps(b"secret", steps)
        self.assertEqual(len(trace), 2)
        # Reverse the chain to recover the input.
        back = core.operation("base64-decode", core.operation("rot", result, -5))
        self.assertEqual(back, b"secret")

    def test_invalid_recipe_rejected(self):
        for bad in ({"schema": 2, "steps": []}, {"steps": [{"op": "rot"}]},
                    {"schema": 1, "steps": [{"op": "nope"}]},
                    {"schema": 1, "steps": [{"op": "rot", "shift": 99}]}):
            with self.assertRaises(core.CryptoError):
                core.validate_recipe(bad)

    def test_save_load_and_run_recipe_file(self):
        src = self.dir / "in.txt"; src.write_bytes(b"hello recipe")
        recipe = self.dir / "r.json"
        core.save_recipe(recipe, [{"op": "base64-encode"}])
        loaded = core.load_recipe(recipe)
        self.assertEqual(loaded["steps"], [{"op": "base64-encode"}])
        out = self.dir / "out.txt"
        core.run_recipe_file(src, recipe, out)
        self.assertEqual(core.operation("base64-decode", out.read_bytes()), b"hello recipe")

    def test_file_transform_never_overwrites(self):
        src = self.dir / "a.txt"; src.write_bytes(b"data")
        dest = self.dir / "exists"; dest.write_bytes(b"keep me")
        with self.assertRaises(core.CryptoError):
            core.transform_file("hex-encode", src, dest)
        self.assertEqual(dest.read_bytes(), b"keep me")


if __name__ == "__main__":
    unittest.main()
