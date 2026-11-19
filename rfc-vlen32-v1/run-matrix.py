#!/usr/bin/env python3
"""Run one bare-metal ELF with four supplied QEMU builds."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shlex
import signal
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
VARIANTS = ("debug-nopatch", "debug-patch", "release-nopatch", "release-patch")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary-root", type=Path,
                        default=HERE.parent / "qemu-binary-vlen32")
    parser.add_argument("--elf", type=Path, default=HERE / "build/repro.elf")
    args = parser.parse_args()
    elf = args.elf.resolve()
    if not elf.is_file():
        parser.error(f"Missing ELF: {elf}. Build it with make or download the release ELF.")
    binaries = {name: args.binary_root.resolve() / name / "qemu-system-riscv64"
                for name in VARIANTS}
    for binary in binaries.values():
        if not binary.is_file() or not os.access(binary, os.X_OK):
            parser.error(f"Missing or non-executable QEMU: {binary}")

    environment = dict(os.environ)
    environment.pop("LD_PRELOAD", None)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    metadata = {"elf_sha256": sha256(elf), "elf": str(elf), "binaries": []}
    for name, binary in binaries.items():
        try:
            version = subprocess.check_output(
                [str(binary), "--version"], env=environment, text=True,
                stderr=subprocess.STDOUT, timeout=10)
        except (OSError, subprocess.SubprocessError) as error:
            parser.error(f"Cannot execute {binary}: {error}")
        metadata["binaries"].append({"variant": name, "path": str(binary),
                                     "sha256": sha256(binary), "version": version})

    results_root = HERE / "build/results"
    results_root.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="matrix-", dir=results_root))
    # The virt board, explicit UART and -bios none need no external firmware.
    firmware = output / "empty-firmware"
    firmware.mkdir()
    rows = []
    for vlen in (32, 128):
        for variant in VARIANTS:
            for tail in (False, True):
                command = [str(binaries[variant]), "-M", "virt", "-accel", "tcg",
                           "-cpu", f"rv64,v=false,zve32x=true,vlen={vlen},elen=32,"
                           f"rvv_ta_all_1s={str(tail).lower()},rvv_ma_all_1s=false",
                           "-smp", "1", "-m", "128M", "-bios", "none",
                           "-L", str(firmware), "-nodefaults", "-nographic",
                           "-monitor", "none", "-serial", "stdio", "-kernel", str(elf)]
                try:
                    result = subprocess.run(command, env=environment,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            timeout=30)
                    code, text = result.returncode, result.stdout.decode(errors="replace")
                except subprocess.TimeoutExpired as error:
                    code, text = "timeout", (error.stdout or b"").decode(errors="replace")
                except OSError as error:
                    code, text = "exec-error", str(error)

                values = re.search(r"actual=0x([0-9a-f]+) expected=0x([0-9a-f]+)", text)
                if code == -signal.SIGABRT and "check_size_align" in text and "Assertion" in text:
                    status = "ASSERT"
                elif values:
                    actual, expected = (int(value, 16) for value in values.groups())
                    status = f"WRONG({actual})"
                    if actual == expected == 40 and code == 0:
                        status = "PASS(40)"
                else:
                    status = f"EXIT({code})"

                reference = "PASS(40)"
                if vlen == 32 and variant == "debug-nopatch":
                    reference = "ASSERT"
                if vlen == 32 and variant == "release-nopatch" and tail:
                    reference = "WRONG(7)"
                row = {"variant": variant, "vlen": vlen, "tail_all_ones": tail,
                       "command": command, "returncode": code, "output": text,
                       "status": status, "reference": reference,
                       "matches_reference": status == reference}
                rows.append(row)
                log = output / f"{variant}-vlen{vlen}-tail-{str(tail).lower()}.log"
                log.write_text(shlex.join(command) + "\n\n" + text +
                               f"\nreturncode={code}\nstatus={status}\n")

    metadata["results"] = rows
    (output / "results.json").write_text(json.dumps(metadata, indent=2) + "\n")
    lines = ["VLEN  build               tail=false  tail=true"]
    for vlen in (32, 128):
        for variant in VARIANTS:
            pair = [row["status"] for row in rows
                    if row["variant"] == variant and row["vlen"] == vlen]
            lines.append(f"{vlen:<5} {variant:<19} {pair[0]:<11} {pair[1]}")
    summary = "\n".join(lines) + "\n"
    (output / "summary.txt").write_text(summary)
    print(summary, end="")
    print("Commands, logs and binary hashes:", output)
    mismatches = sum(not row["matches_reference"] for row in rows)
    print(f"Reference matrix: {16 - mismatches}/16 matches")
    return int(bool(mismatches))


if __name__ == "__main__":
    raise SystemExit(main())
