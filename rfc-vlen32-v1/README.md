# RFC VLEN=32 v1 reproduction

This reproduces the behavior discussed in `[PATCH RFC] tcg: Support maxsz=4 in
GVEC descriptors`, posted on November 18, 2026.

- [Patch and discussion on qemu-devel](https://lore.kernel.org/qemu-devel/20261118-bug-issue-rvv-vlen32-gvec-v1-1-c15cf05de6bc@gmail.com/T/)
- [Richard Henderson's review](https://lore.kernel.org/qemu-devel/1224bde0-91d8-4efe-8be4-bcd83afc450e@linaro.org/)
- [Background and translation paths](https://zhenbaii.github.io/%E8%99%9A%E6%8B%9F%E5%8C%96/2026/11/17/riscv-zve32x-gvec-en/)

`auto_stats.c` computes `sum(left) + 3 * min(right)` in ordinary C. For
`left = {1,2,3,4}` and `right = {10,20,30,40}`, the expected result is 40.
GCC vectorizes this computation using Zve32x. `start.S`, `main.c` and `link.ld`
provide the bare-metal startup, UART output and QEMU exit mechanism.

## Run with four prepared QEMU executables

The runner requires Python 3.8+ on Linux. Arrange your executables as follows,
or [download the four tested binaries](../qemu-binary-vlen32/README.md).

```text
qemu-binary-vlen32/
  debug-nopatch/qemu-system-riscv64
  debug-patch/qemu-system-riscv64
  release-nopatch/qemu-system-riscv64
  release-patch/qemu-system-riscv64
```

Build the guest with RISC-V bare-metal GCC and binutils. The reference compiler
is `riscv64-unknown-elf-gcc 14.2.0` with Zve32x support.

```bash
cd rfc-vlen32-v1
make
python3 run-matrix.py --binary-root ../qemu-binary-vlen32
```

Use `make CROSS_COMPILE=/path/to/riscv64-unknown-elf-` for a compiler installed
elsewhere. The Makefile enables `-fvect-cost-model=unlimited` for `auto_stats.c`
and checks that GCC emitted `vredsum.vs` and `vminu.vv`. The startup and reporting
code are compiled separately, with automatic vectorization disabled for the
reporting code. `build/repro.dis` and `build/repro.attributes` record the
instructions and ISA attributes.

You can also download the tested guest ELF to run without a cross compiler.
Run the following commands from the repository root.

```bash
mkdir -p rfc-vlen32-v1/build
curl -fL https://github.com/zhenbaii/qemu-smoke-test/releases/download/rfc-vlen32-v1/repro.elf \
  -o rfc-vlen32-v1/build/repro.elf
python3 rfc-vlen32-v1/run-matrix.py
```

The runner executes the same ELF in all 16 cases. Each case varies the QEMU
build, `VLEN=32/128`, and `rvv_ta_all_1s=false/true`. It fixes `ELEN=32`, disables
the full V extension and sets `rvv_ma_all_1s=false`. It uses `-bios none` and an
explicit UART, so the matrix needs no external firmware files.

## Reference results

```text
VLEN  build               tail=false  tail=true
32    debug-nopatch       ASSERT      ASSERT
32    debug-patch         PASS(40)    PASS(40)
32    release-nopatch     PASS(40)    WRONG(7)
32    release-patch       PASS(40)    PASS(40)
128   debug-nopatch       PASS(40)    PASS(40)
128   debug-patch         PASS(40)    PASS(40)
128   release-nopatch     PASS(40)    PASS(40)
128   release-patch       PASS(40)    PASS(40)
```

The runner saves commands, output, exit codes, executable hashes and version
strings under `build/results/matrix-*/`. Exit status 0 means all 16 outcomes
match this reference matrix. Exit status 1 means at least one differs, and
`results.json` identifies the cases. Exit status 2 indicates invalid inputs.

In the unpatched debug build, descriptor construction triggers the size
assertion during translation. In the tested unpatched release build, a
four-byte size becomes an encoded `MAXSZ` field of 255 and decodes as 2048
bytes. With all-ones tails enabled, the helper's tail writes corrupt a live
vector register and this computation returns 7.

These results describe the supplied binaries and the GCC 14.2-generated guest.
Release builds violate a `__builtin_unreachable()` assumption for this input,
so another compiler or build may produce a different failure. A different
guest compiler may also allocate vector registers differently. The downloaded
ELF preserves the tested guest instruction sequence.

`rvv_ta_all_1s` selects QEMU's implementation of tail-agnostic elements. The
runner changes that CPU option while keeping the guest ELF fixed.

## Prepare the four QEMU builds yourself

The reference baseline is the project commit
`4437f0c7ef333aa97ac5deb7b95aedf377a471a6`. The submitted v1 commit is
`894d37820622fa6927ef83bc64bced7be332164f`, whose parent is that baseline.
The included [v1.patch](v1.patch) contains the exact submitted code change.

The two debug executables use `--enable-debug-tcg`. The two release executables
use `--disable-debug-tcg`. Debug information (`-g`) is independent of that option.
All four should use the same host compiler and optimization settings.

Use Bash and a clean QEMU checkout. QEMU's official source is available from
[gitlab.com/qemu-project/qemu](https://gitlab.com/qemu-project/qemu).
The commands below fetch the historical project baseline into that checkout,
then build the two baseline executables followed by the two patched executables.
Run them from this smoke-test repository's root. Set `QEMU_SRC` to your QEMU
source directory.

```bash
SMOKE_REPO=$(pwd)
QEMU_SRC=/path/to/qemu
QEMU_BINARIES="$SMOKE_REPO/qemu-binary-vlen32"

git -C "$QEMU_SRC" fetch https://github.com/processmission/qemu.git \
  4437f0c7ef333aa97ac5deb7b95aedf377a471a6
git -C "$QEMU_SRC" checkout --detach 4437f0c7ef333aa97ac5deb7b95aedf377a471a6

build_qemu() {
    local variant=$1
    local debug_option=$2
    local build_dir="$SMOKE_REPO/rfc-vlen32-v1/build/qemu-$variant"
    mkdir -p "$build_dir" "$QEMU_BINARIES/$variant"
    (
        cd "$build_dir"
        "$QEMU_SRC/configure" --target-list=riscv64-softmmu \
          --disable-docs --disable-werror --disable-gtk --disable-sdl \
          --disable-vnc --disable-opengl --disable-tools --disable-guest-agent \
          "$debug_option"
        ninja qemu-system-riscv64
    )
    install -m 755 "$build_dir/qemu-system-riscv64" "$QEMU_BINARIES/$variant/"
}

build_qemu debug-nopatch --enable-debug-tcg
build_qemu release-nopatch --disable-debug-tcg
git -C "$QEMU_SRC" am "$SMOKE_REPO/rfc-vlen32-v1/v1.patch"
build_qemu debug-patch --enable-debug-tcg
build_qemu release-patch --disable-debug-tcg
```

QEMU's build prerequisites include a host C/C++ compiler, Python, Ninja,
pkg-config, GLib and pixman development packages. Configure reports additional
dependencies for the selected host and may download its pinned subprojects.
`git am` reproduces the patched source tree; the new commit ID depends on your
local committer identity and timestamp. The release includes a baseline source
archive and the patch for convenient source access.
