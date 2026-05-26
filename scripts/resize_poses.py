#!/usr/bin/env python3
"""Resize all agent pose PNGs to 160x160 (2x for 80px CSS render).

Usage:
  python3 scripts/resize_poses.py              # process all agents
  python3 scripts/resize_poses.py dog-of-bitcoin  # one agent only

Reads from frontend/public/assets/agents/<name>/actions/
Overwrites in place. Skips files already at target size.
"""

import sys
from pathlib import Path
from PIL import Image

TARGET = 160  # 2x retina for 80px CSS
ASSETS = Path(__file__).resolve().parent.parent / "frontend" / "public" / "assets" / "agents"


def resize_dir(agent_dir: Path):
    actions = agent_dir / "actions"
    if not actions.is_dir():
        return
    for p in sorted(actions.glob("*.png")):
        img = Image.open(p)
        w, h = img.size
        if w == TARGET and h == TARGET:
            print(f"  skip (already {TARGET}x{TARGET}) {p.name}")
            continue
        img = img.resize((TARGET, TARGET), Image.LANCZOS)
        img.save(p, optimize=True)
        print(f"  {w}x{h} -> {TARGET}x{TARGET}  {p.name}")


def main():
    agents = sys.argv[1:] if len(sys.argv) > 1 else None
    dirs = []
    if agents:
        for name in agents:
            d = ASSETS / name
            if d.is_dir():
                dirs.append(d)
            else:
                print(f"not found: {d}")
    else:
        dirs = sorted(d for d in ASSETS.iterdir() if d.is_dir())

    for d in dirs:
        print(f"\n{d.name}/")
        resize_dir(d)

    print("\ndone.")


if __name__ == "__main__":
    main()
