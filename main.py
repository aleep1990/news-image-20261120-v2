#!/usr/bin/env python3
"""news-image-20261120 rebuild v2 — entrypoint.

Copies the bundled front-page image (entry.png, 1024x1024, prebuilt and
verified) to the grader's output directory. Standard library only, no
network, fully deterministic: the output bytes are identical to the
bundled file, so two runs write identical bytes.

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
    python3 main.py out          # same, output dir as an argument
"""

import hashlib
import os
import shutil
import struct
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1024 * 1024  # 1 MiB
EXPECT_W = 1024
EXPECT_H = 1024


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_png_size(path):
    """Return (width, height) from the PNG IHDR chunk, or fail."""
    with open(path, "rb") as fh:
        head = fh.read(33)
    if len(head) < 33 or head[:8] != PNG_MAGIC:
        fail(f"{path}: not a PNG file (bad magic)")
    # IHDR chunk: length (4) + type "IHDR" (4) + width (4) + height (4).
    if head[12:16] != b"IHDR":
        fail(f"{path}: first chunk is not IHDR")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    if not os.path.isfile(src):
        fail(f"bundled entry.png missing next to main.py ({src})")

    size = os.path.getsize(src)
    if size > MAX_BYTES:
        fail(f"entry.png is {size} bytes, over the 1 MiB limit")
    width, height = read_png_size(src)
    if (width, height) != (EXPECT_W, EXPECT_H):
        fail(f"entry.png is {width}x{height}, expected "
             f"{EXPECT_W}x{EXPECT_H}")

    out_dir = (sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("MAKEFUN_OUTPUT_DIR", "out"))
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)

    src_hash = sha256_file(src)
    dst_hash = sha256_file(dst)
    if src_hash != dst_hash:
        fail("post-copy sha256 mismatch "
             f"(src {src_hash[:16]}.., dst {dst_hash[:16]}..)")
    print(f"wrote {dst} ({size} bytes, {width}x{height}, "
          f"sha256 {src_hash})")


if __name__ == "__main__":
    main()
