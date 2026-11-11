#!/usr/bin/env python3
"""Calculate or verify file checksums."""

import argparse
import hashlib
import sys
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def available_algorithms():
    """Return supported hash algorithms, excluding insecure legacy hashes."""
    return sorted(
        name
        for name in hashlib.algorithms_available
        if name.lower() not in {"md5", "sha1", "shake_128", "shake_256"}
    )


def hash_file(path: Path, algorithm: str) -> str:
    """Return the hexadecimal checksum for a file."""
    digest = hashlib.new(algorithm)

    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> int:
    algorithms = available_algorithms()

    parser = argparse.ArgumentParser(
        description="Calculate or verify a file checksum."
    )
    parser.add_argument(
        "--algorithm",
        "-a",
        choices=algorithms,
        default="sha256",
        help="Hash algorithm (default: sha256).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_parser = subparsers.add_parser("hash", help="Calculate a file checksum.")
    hash_parser.add_argument("file", type=Path, help="File to hash.")

    verify_parser = subparsers.add_parser(
        "verify", help="Compare a file with an expected checksum."
    )
    verify_parser.add_argument("file", type=Path, help="File to verify.")
    verify_parser.add_argument(
        "expected",
        help="Expected hexadecimal checksum.",
    )

    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Error: not a regular file: {args.file}", file=sys.stderr)
        return 2

    try:
        actual = hash_file(args.file, args.algorithm)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if args.command == "hash":
        print(f"{actual}  {args.file}")
        return 0

    expected = args.expected.strip()

    # Require a well-formed hexadecimal checksum of the right length.
    try:
        bytes.fromhex(expected)
    except ValueError:
        print("Error: expected checksum must be hexadecimal.", file=sys.stderr)
        return 2

    if len(expected) != len(actual):
        print(
            f"Error: checksum length does not match {args.algorithm}.",
            file=sys.stderr,
        )
        return 2

    if actual.lower() == expected.lower():
        print(f"OK: {args.file}")
        return 0

    print(f"MISMATCH: {args.file}")
    print(f"  Expected: {expected.lower()}")
    print(f"  Actual:   {actual}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
