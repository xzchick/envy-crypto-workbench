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

    def test_base85_round_trip(self):
        for payload in (b"", b"Hello", b"\x00\x01\x02\xff binary \x10", b"A" * 100):
            enc = core.operation("base85-encode", payload)
            self.assertEqual(core.operation("base85-decode", enc), payload)

    def test_base85_decode_tolerates_whitespace(self):
        enc = core.operation("base85-encode", b"spread across lines")
        spaced = b"  " + enc[:4] + b"\n" + enc[4:] + b"  "
        self.assertEqual(core.operation("base85-decode", spaced), b"spread across lines")

    def test_base85_in_recipe(self):
        out, _ = core.run_steps(b"payload", [{"op": "base85-encode"}, {"op": "base85-decode"}])
        self.assertEqual(out, b"payload")

    def test_url_encode_round_trip_and_vector(self):
        self.assertEqual(core.operation("url-encode", b"a b&c=/?"), b"a%20b%26c%3D%2F%3F")
        data = "key = café/2".encode("utf-8")
        self.assertEqual(core.operation("url-decode", core.operation("url-encode", data)), data)

    def test_rot47_is_its_own_inverse_and_vector(self):
        self.assertEqual(core.operation("rot47", b"Hello, World!"), b"w6==@[ (@C=5P")
        self.assertEqual(core.operation("rot47", core.operation("rot47", b"Secrets 123")), b"Secrets 123")

    def test_reverse_handles_unicode(self):
        self.assertEqual(core.operation("reverse", "café".encode()), "éfac".encode())

    def test_vigenere_known_vector(self):
        # The classic ATTACKATDAWN / LEMON -> LXFOPVEFRNHR vector.
        self.assertEqual(core.operation("vigenere-encode", b"ATTACKATDAWN", key="LEMON"), b"LXFOPVEFRNHR")
        self.assertEqual(core.operation("vigenere-decode", b"LXFOPVEFRNHR", key="LEMON"), b"ATTACKATDAWN")

    def test_vigenere_round_trip_preserves_case_and_punctuation(self):
        msg = "Meet me at Dawn, by the River!".encode()
        enc = core.operation("vigenere-encode", msg, key="Falcon")
        self.assertNotEqual(enc, msg)
        self.assertEqual(core.operation("vigenere-decode", enc, key="Falcon"), msg)
        # Non-letters are passed through, not shifted.
        self.assertIn(b",", enc); self.assertIn(b"!", enc)

    def test_vigenere_requires_letter_key(self):
        for bad in ("", "  ", "key1", "clé"):
            with self.assertRaises(core.CryptoError):
                core.operation("vigenere-encode", b"hello", key=bad)

    def test_recipe_carries_vigenere_key(self):
        steps = [{"op": "vigenere-encode", "key": "LEMON"}, {"op": "base64-encode"}]
        out, trace = core.run_steps(b"ATTACKATDAWN", steps)
        self.assertEqual(core.operation("base64-decode", out), b"LXFOPVEFRNHR")
        self.assertEqual(len(trace), 2)
        with self.assertRaises(core.CryptoError):
            core.run_steps(b"x", [{"op": "vigenere-encode"}])            # missing key
        with self.assertRaises(core.CryptoError):
            core.run_steps(b"x", [{"op": "vigenere-encode", "key": "LEMON", "shift": 1}])  # stray param

    def test_railfence_known_vector(self):
        # The classic WEAREDISCOVEREDFLEEATONCE / 3 rails example.
        self.assertEqual(core.operation("railfence-encode", b"WEAREDISCOVEREDFLEEATONCE", rails=3),
                         b"WECRLTEERDSOEEFEAOCAIVDEN")
        self.assertEqual(core.operation("railfence-decode", b"WECRLTEERDSOEEFEAOCAIVDEN", rails=3),
                         b"WEAREDISCOVEREDFLEEATONCE")

    def test_railfence_round_trip_various_rails(self):
        msg = "The quick brown fox, jumps! 123".encode()
        for rails in (2, 4, 7):
            enc = core.operation("railfence-encode", msg, rails=rails)
            self.assertEqual(core.operation("railfence-decode", enc, rails=rails), msg)

    def test_railfence_rails_bounds(self):
        for bad in (1, 0, 65, True):
            with self.assertRaises(core.CryptoError):
                core.operation("railfence-encode", b"abc", rails=bad)

    def test_recipe_carries_rails(self):
        steps = [{"op": "railfence-encode", "rails": 3}, {"op": "base64-encode"}]
        out, _ = core.run_steps(b"WEAREDISCOVEREDFLEEATONCE", steps)
        self.assertEqual(core.operation("base64-decode", out), b"WECRLTEERDSOEEFEAOCAIVDEN")
        with self.assertRaises(core.CryptoError):
            core.run_steps(b"x", [{"op": "railfence-encode", "rails": 1}])
        with self.assertRaises(core.CryptoError):
            core.run_steps(b"x", [{"op": "railfence-encode", "key": "x"}])   # stray param

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
