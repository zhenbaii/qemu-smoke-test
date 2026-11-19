# Prebuilt QEMU for RFC VLEN=32 v1

The [rfc-vlen32-v1 release](https://github.com/zhenbaii/qemu-smoke-test/releases/tag/rfc-vlen32-v1)
provides copies of the four tested executables from `~/qemu-binary-vlen32`.
Extract the binary archive into this repository's root to use the runner's
default paths.

```bash
curl -fLO https://github.com/zhenbaii/qemu-smoke-test/releases/download/rfc-vlen32-v1/qemu-binary-vlen32-linux-x86_64.tar.gz
curl -fLO https://github.com/zhenbaii/qemu-smoke-test/releases/download/rfc-vlen32-v1/SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS
tar -xzf qemu-binary-vlen32-linux-x86_64.tar.gz
sha256sum -c qemu-binary-vlen32/SHA256SUMS
```

The binaries were built on Ubuntu 25.04, x86-64, with host GCC 14.2.0. They
are dynamically linked and require compatible host libraries, including glibc
2.38 or newer. Run `ldd qemu-binary-vlen32/debug-nopatch/qemu-system-riscv64`
to check dependencies. [manifest.json](manifest.json) records the versions,
hashes, host details and required shared-library names.

| Directory | Source | TCG debug assertions |
| --- | --- | --- |
| `debug-nopatch` | baseline `4437f0c7ef` | enabled |
| `release-nopatch` | baseline `4437f0c7ef` | disabled |
| `debug-patch` | v1 `894d378206` | enabled |
| `release-patch` | v1 `894d378206` | disabled |

The release also provides the tested `repro.elf` and
`qemu-source-4437f0c7ef.tar.gz`. The source archive contains the baseline QEMU
source, the pinned SoftFloat, TestFloat and keycodemapdb sources, the v1 patch,
and the reproduction/build instructions. QEMU's COPYING and COPYING.LIB and
the dependency license notices are retained in the source archive. The binary
archive includes the QEMU license texts.

For a local build, follow [the QEMU preparation instructions](../rfc-vlen32-v1/README.md#prepare-the-four-qemu-builds-yourself).
