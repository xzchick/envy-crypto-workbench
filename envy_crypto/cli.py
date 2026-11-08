"""Command-line entry point. The workbench window is the default."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import CryptoError, OPERATIONS, run_recipe_file, transform_file


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="envy-crypto",
        description="Offline encoding, classical ciphers and text analysis. Run with no "
                    "arguments to open the workbench window. Not modern encryption.")
    root.add_argument("--version", action="version", version=f"envy-crypto {__version__}")
    commands = root.add_subparsers(dest="command")
    commands.add_parser("gui", help="open the workbench window (default)")

    run = commands.add_parser("run", help="apply one operation to a file")
    run.add_argument("--op", required=True, choices=OPERATIONS)
    run.add_argument("--shift", type=int, default=13, help="ROT shift, -25..25")
    run.add_argument("--key", default="", help="keyword for vigenere-encode/decode (ASCII letters)")
    run.add_argument("source")
    run.add_argument("destination", help="a new file; it is never overwritten")

    recipe = commands.add_parser("recipe", help="run a saved recipe over a file")
    recipe.add_argument("--recipe", required=True, help="a schema-1 recipe JSON file")
    recipe.add_argument("source")
    recipe.add_argument("destination")
    recipe.add_argument("--trace", action="store_true",
                        help="print each step's output size and SHA-256 as the recipe runs")

    analyze = commands.add_parser("analyze", help="print read-only frequency and entropy analysis")
    analyze.add_argument("source")
    analyze.add_argument("--full", action="store_true", help="include the full byte histogram")
    return root


def _run(args) -> int:
    from .core import read_regular, analyze as analyze_bytes
    if args.command == "run":
        result = transform_file(args.op, args.source, args.destination, args.shift, args.key)
        print(f"{args.op}: wrote {result['bytes']} bytes to {result['output']}")
    elif args.command == "recipe":
        result = run_recipe_file(args.source, args.recipe, args.destination)
        if args.trace:
            for i, step in enumerate(result["steps"], 1):
                extra = f" shift={step['shift']}" if "shift" in step else (
                    f" key={step['key']}" if "key" in step else "")
                print(f"  {i}. {step['op']}{extra} → {step['output_bytes']} bytes  "
                      f"sha256 {step['output_sha256'][:16]}…")
        print(f"recipe ({len(result['steps'])} steps): wrote {result['output']}")
    else:  # analyze
        report = analyze_bytes(read_regular(args.source))
        if not args.full:
            report.pop("byte_frequency", None)
            report["rot_candidates"] = report["rot_candidates"][:3]
        print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "gui"):
        from .gui import run_app
        return run_app()
    try:
        return _run(args)
    except CryptoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
