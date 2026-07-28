#!/usr/bin/env python3
"""Verify the toolchain versions required by the course spec.

Required (any ONE of each):
  C compiler : GCC 13.x / 15.x   OR   Clang 20.x / 21.x
  Python     : 3.12.x, 3.13.x, or 3.14.x
  Rust       : 1.91.x, 1.93.x, or 1.95.x (rustc/cargo)

Hard-fails (non-zero exit) with a specific, actionable message if nothing
matches. Writes the selected python/cc choice to .toolchain.env for the
Makefile to source into subsequent build steps.
"""
import re
import shutil
import subprocess
import sys

ALLOWED_PY = {(3, 12), (3, 13), (3, 14)}
ALLOWED_RUST = {(1, 91), (1, 93), (1, 95)}
ALLOWED_GCC = {13, 15}
ALLOWED_CLANG = {20, 21}

CC_CANDIDATES = ["gcc-15", "gcc-13", "clang-21", "clang-20", "gcc", "clang", "cc"]
PY_CANDIDATES = ["python3.14", "python3.13", "python3.12", "python3"]


def run_version(cmd):
    try:
        out = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or out.stderr.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def find_version_tuple(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def check_cc():
    for cand in CC_CANDIDATES:
        if not shutil.which(cand):
            continue
        banner = run_version(cand)
        ver = find_version_tuple(banner)
        if not ver:
            continue
        major, _ = ver
        is_clang = "clang" in (banner or "").lower()
        if is_clang and major in ALLOWED_CLANG:
            return cand, banner.splitlines()[0]
        if not is_clang and major in ALLOWED_GCC:
            return cand, banner.splitlines()[0]
    return None


def check_python():
    for cand in PY_CANDIDATES:
        if not shutil.which(cand):
            continue
        banner = run_version(cand)
        ver = find_version_tuple(banner)
        if ver and ver in ALLOWED_PY:
            return cand, banner.strip()
    return None


def check_rust():
    if not shutil.which("rustc"):
        return None
    banner = run_version("rustc")
    ver = find_version_tuple(banner)
    if ver and ver in ALLOWED_RUST:
        return "rustc", banner.strip()
    return None


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    cc = check_cc()
    if not cc:
        fail(
            "No compatible C compiler found. Need GCC 13.x/15.x or Clang 20.x/21.x.\n"
            "  Ubuntu/Mint: sudo apt install gcc-13   (or gcc-15 / clang-20 / clang-21)"
        )
    py = check_python()
    if not py:
        fail(
            "No compatible Python found. Need 3.12.x, 3.13.x, or 3.14.x.\n"
            "  Ubuntu/Mint: sudo add-apt-repository ppa:deadsnakes/ppa && "
            "sudo apt install python3.12"
        )
    rust = check_rust()
    if not rust:
        fail(
            "No compatible Rust found. Need rustc 1.91.x, 1.93.x, or 1.95.x.\n"
            "  rustup toolchain install 1.95.0 && rustup override set 1.95.0"
        )

    cc_bin, cc_ver = cc
    py_bin, py_ver = py
    _, rust_ver = rust

    print(f"C compiler : {cc_bin:10s} -> {cc_ver}")
    print(f"Python     : {py_bin:10s} -> {py_ver}")
    print(f"Rust       : rustc      -> {rust_ver}")

    with open(".toolchain.env", "w") as f:
        f.write(f"CC={cc_bin}\n")
        f.write(f"PYTHON={py_bin}\n")

    print("Toolchain OK.")


if __name__ == "__main__":
    main()
