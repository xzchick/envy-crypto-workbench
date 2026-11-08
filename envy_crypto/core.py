"""Offline encoding and classical-cipher operations for ENVY Cryptography Workbench.

These are reversible encodings and teaching ciphers (Base64, hex, ROT, Atbash,
reverse) and read-only analysis (byte/letter frequency, Shannon entropy, index
of coincidence, ROT brute force). None of this is modern encryption — secrets
belong in ENVY Vault. Ported from ENVY BLACK VEIL's Crypto Lab.
"""

from __future__ import annotations

import base64
import binascii
from collections import Counter
import hashlib
import json
import math
import os
import stat
import urllib.parse
from pathlib import Path

MAX_INPUT = 1024 * 1024
MAX_OUTPUT = 4 * 1024 * 1024
MAX_STEPS = 16
OPERATIONS = ("base64-encode", "base64-decode", "base32-encode", "base32-decode",
              "hex-encode", "hex-decode", "url-encode", "url-decode",
              "rot", "rot47", "atbash", "vigenere-encode", "vigenere-decode", "reverse")
CAPTIONS = {
    "base64-encode": "Encode as Base64", "base64-decode": "Decode Base64",
    "base32-encode": "Encode as Base32", "base32-decode": "Decode Base32",
    "hex-encode": "Encode as hex", "hex-decode": "Decode hex",
    "url-encode": "URL-encode (percent)", "url-decode": "URL-decode (percent)",
    "rot": "Shift letters (ROT)", "rot47": "Shift printable (ROT47)",
    "atbash": "Reverse alphabet (Atbash)",
    "vigenere-encode": "Vigenère encipher (keyword)", "vigenere-decode": "Vigenère decipher (keyword)",
    "reverse": "Reverse characters",
}


class CryptoError(Exception):
    """A user-facing error: bad input for an operation, a malformed recipe."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _vigenere(data: bytes, key: str, decode: bool = False) -> bytes:
    """Classic Vigenère over A–Z/a–z; case preserved, non-letters passed through
    without consuming the key. The key must be ASCII letters."""
    key = (key or "").strip()
    if not key or not key.isascii() or not key.isalpha():
        raise CryptoError("Vigenère needs a key of ASCII letters (A–Z)")
    shifts = [ord(k.lower()) - ord("a") for k in key]
    out, i = [], 0
    for char in data.decode("utf-8"):
        start = ord("A") if "A" <= char <= "Z" else ord("a") if "a" <= char <= "z" else None
        if start is None:
            out.append(char)
            continue
        s = shifts[i % len(shifts)]
        out.append(chr(start + (ord(char) - start + (-s if decode else s)) % 26))
        i += 1
    return "".join(out).encode("utf-8")


def operation(action: str, data: bytes, shift: int = 13, key: str = "") -> bytes:
    """Apply one reversible operation to bytes. Raises CryptoError on bad input."""
    if action not in OPERATIONS:
        raise CryptoError("Unknown operation")
    try:
        if action == "base64-encode":
            result = base64.b64encode(data)
        elif action == "base64-decode":
            result = base64.b64decode(b"".join(data.split()), validate=True)
        elif action == "base32-encode":
            result = base64.b32encode(data)
        elif action == "base32-decode":
            result = base64.b32decode(b"".join(data.split()), casefold=True)
        elif action == "hex-encode":
            result = data.hex().encode("ascii")
        elif action == "hex-decode":
            result = bytes.fromhex(data.decode("ascii"))
        elif action == "url-encode":
            result = urllib.parse.quote_from_bytes(data, safe="").encode("ascii")
        elif action == "url-decode":
            result = urllib.parse.unquote_to_bytes(data.decode("ascii"))
        elif action == "rot47":
            # ROT47 shifts printable ASCII (33–126) by 47; it is its own inverse.
            result = bytes(33 + (b - 33 + 47) % 94 if 33 <= b <= 126 else b for b in data)
        elif action == "vigenere-encode":
            result = _vigenere(data, key, decode=False)
        elif action == "vigenere-decode":
            result = _vigenere(data, key, decode=True)
        elif action == "reverse":
            result = data.decode("utf-8")[::-1].encode("utf-8")
        else:
            if isinstance(shift, bool) or not isinstance(shift, int) or not -25 <= shift <= 25:
                raise CryptoError("ROT shift must be an integer between -25 and 25")
            out = []
            for char in data.decode("utf-8"):
                start = ord("A") if "A" <= char <= "Z" else ord("a") if "a" <= char <= "z" else None
                if start is None:
                    out.append(char)
                elif action == "atbash":
                    out.append(chr(start + 25 - (ord(char) - start)))
                else:
                    out.append(chr(start + (ord(char) - start + shift) % 26))
            result = "".join(out).encode("utf-8")
    except (UnicodeError, ValueError, binascii.Error) as exc:
        raise CryptoError("Input is not valid for this operation: " + str(exc)) from None
    if len(result) > MAX_OUTPUT:
        raise CryptoError("Output exceeds the 4 MiB limit")
    return result


def analyze(data: bytes) -> dict:
    """Read-only frequency and entropy analysis, plus ROT brute-force previews."""
    count = Counter(data)
    entropy = -sum((n / len(data)) * math.log2(n / len(data)) for n in count.values()) if data else 0
    letters = Counter(chr(byte).upper() for byte in data if 65 <= byte <= 90 or 97 <= byte <= 122)
    total = sum(letters.values())
    coincidence = sum(n * (n - 1) for n in letters.values()) / (total * (total - 1)) if total > 1 else 0
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        text = None
    candidates = []
    if text is not None:
        preview = text[:512].encode("utf-8")
        candidates = [{"shift": s, "preview": operation("rot", preview, s).decode("utf-8")} for s in range(26)]
    return {
        "bytes": len(data), "sha256": _digest(data), "utf8": text is not None,
        "entropy_bits_per_byte": round(entropy, 6),
        "index_of_coincidence": round(coincidence, 6),
        "letters": {chr(i): letters[chr(i)] for i in range(65, 91)},
        "byte_frequency": {f"{byte:02x}": count[byte] for byte in sorted(count)},
        "rot_candidates": candidates,
        "interpretation": "Encoding and classical-cipher learning only. Entropy and frequency do "
                          "not prove encryption, randomness, identity, or wrongdoing.",
    }


def validate_recipe(recipe: dict) -> dict:
    if (not isinstance(recipe, dict) or set(recipe) != {"schema", "steps"}
            or type(recipe["schema"]) is not int or recipe["schema"] != 1):
        raise CryptoError("Expected a schema 1 recipe with only schema and steps")
    steps = recipe["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise CryptoError("A recipe needs between 1 and 16 steps")
    for step in steps:
        if not isinstance(step, dict) or step.get("op") not in OPERATIONS:
            raise CryptoError("Invalid recipe operation")
        if step["op"] == "rot":
            allowed = {"op", "shift"}
        elif step["op"].startswith("vigenere-"):
            allowed = {"op", "key"}
        else:
            allowed = {"op"}
        if not set(step) <= allowed:
            raise CryptoError("Unknown recipe step parameter")
        if step["op"] == "rot":
            shift = step.get("shift", 13)
            if isinstance(shift, bool) or not isinstance(shift, int) or not -25 <= shift <= 25:
                raise CryptoError("Recipe ROT shift must be between -25 and 25")
        if step["op"].startswith("vigenere-"):
            key = step.get("key", "")
            if not isinstance(key, str) or not key.strip() or not key.strip().isascii() or not key.strip().isalpha():
                raise CryptoError("Recipe Vigenère key must be ASCII letters")
    return recipe


def run_steps(data: bytes, steps: list) -> tuple[bytes, list]:
    """Apply a validated step list to bytes, returning the result and a trace."""
    validate_recipe({"schema": 1, "steps": steps})
    trace = []
    for step in steps:
        data = operation(step["op"], data, step.get("shift", 13), step.get("key", ""))
        trace.append(dict(step, output_bytes=len(data), output_sha256=_digest(data)))
    return data, trace


# ----- file and recipe helpers (cross-platform) ----------------------------

def read_regular(path: str | Path, limit: int = MAX_INPUT) -> bytes:
    path = Path(path).expanduser()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(str(path), flags)
    except FileNotFoundError:
        raise CryptoError(f"File not found: {path}") from None
    except OSError as exc:
        raise CryptoError(f"Cannot open {path}: {exc.strerror or exc}") from None
    with os.fdopen(descriptor, "rb") as stream:
        meta = os.fstat(stream.fileno())
        if not stat.S_ISREG(meta.st_mode):
            raise CryptoError("Expected a regular file.")
        if meta.st_size > limit:
            raise CryptoError(f"File is larger than the {limit // (1024 * 1024)} MiB limit.")
        return stream.read(limit + 1)[:limit + 1]


def write_new_file(path: str | Path, data: bytes) -> Path:
    path = Path(path).expanduser()
    try:
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    except FileExistsError:
        raise CryptoError(f"Output already exists; choose a new name: {path}") from None
    except OSError as exc:
        raise CryptoError(f"Cannot write {path}: {exc.strerror or exc}") from None
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def transform_file(action: str, source: str | Path, destination: str | Path, shift: int = 13, key: str = "") -> dict:
    data = read_regular(source)
    result = operation(action, data, shift, key)
    write_new_file(destination, result)
    return {"output": str(Path(destination).expanduser()), "operation": action,
            "bytes": len(result), "modern_encryption": False, "source_preserved": True}


def load_recipe(source: str | Path) -> dict:
    try:
        return validate_recipe(json.loads(read_regular(source, 16 * 1024)))
    except (json.JSONDecodeError, UnicodeError, RecursionError):
        raise CryptoError("Recipe must contain valid UTF-8 JSON") from None


def save_recipe(destination: str | Path, steps: list) -> dict:
    recipe = validate_recipe({"schema": 1, "steps": steps})
    write_new_file(destination, (json.dumps(recipe, indent=2) + "\n").encode("utf-8"))
    return {"output": str(Path(destination).expanduser()), "steps": len(steps)}


def run_recipe_file(source: str | Path, recipe: str | Path, destination: str | Path) -> dict:
    data = read_regular(source)
    result, trace = run_steps(data, load_recipe(recipe)["steps"])
    write_new_file(destination, result)
    return {"output": str(Path(destination).expanduser()), "steps": trace,
            "modern_encryption": False, "source_preserved": True}
