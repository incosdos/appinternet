#!/usr/bin/env python3
"""Optimiza imágenes en public/ — redimensiona, comprime y elimina metadatos."""

import subprocess, shutil, sys
from pathlib import Path


PUBLIC = Path(__file__).parent / "public"
MAX_DIM = 1200
QUALITY = 82
EXT = (".jpg", ".jpeg", ".png", ".webp")


def fmt(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    return f"{b/1024:.1f}K" if b < 1024**2 else f"{b/1024**2:.1f}M"


def report(path: Path) -> str:
    try:
        out = subprocess.run(
            ["identify", "-format", "%wx%h %b", str(path)],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        out = "?"
    return out


def optimize(path: Path):
    before = path.stat().st_size
    dims = report(path)

    tmp = path.with_stem(path.stem + ".tmp")

    subprocess.run(
        ["convert", str(path),
         "-resize", f"{MAX_DIM}x{MAX_DIM}>",
         "-strip",
         "-quality", str(QUALITY),
         str(tmp)],
        capture_output=True, timeout=30,
    )

    if not tmp.exists():
        print(f"  ✗ {path.name} — error processing")
        return

    if tmp.stat().st_size >= before:
        tmp.unlink()
        print(f"  – {path.name} — already optimal ({dims}, {fmt(before)})")
        return

    shutil.move(str(tmp), str(path))
    after = path.stat().st_size
    saved = before - after
    pct = saved / before * 100
    print(f"  ✓ {path.name} — {dims}  {fmt(before)} → {fmt(after)}  (-{fmt(saved)}, {pct:.0f}%)")


def main():
    images = sorted(p for p in PUBLIC.iterdir() if p.suffix.lower() in EXT)
    if not images:
        print("No images found in public/")
        sys.exit(1)

    print(f"Optimizing {len(images)} images in public/ (max {MAX_DIM}px, quality {QUALITY})\n")

    total_before = sum(p.stat().st_size for p in images)
    for img in images:
        optimize(img)
    total_after = sum(p.stat().st_size for p in images)
    total_saved = total_before - total_after
    pct = total_saved / total_before * 100

    print(f"\nTotal: {fmt(total_before)} → {fmt(total_after)}  (-{fmt(total_saved)}, {pct:.0f}%)")


if __name__ == "__main__":
    main()
