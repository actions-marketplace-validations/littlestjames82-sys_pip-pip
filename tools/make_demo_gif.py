#!/usr/bin/env python3
"""Build the README demo GIF: a terminal session rendered from the tool's
REAL output (no hand-typed fake). Usage:

    python3 tools/make_demo_gif.py <repo-to-review> [out.gif]

Needs Pillow (pip install pillow) and a monospace font (DejaVu Sans Mono).
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SIZE = 15
LH = 23
PAD_X, PAD_Y = 22, 52
W = 980
BG = (13, 17, 23)
FG = (230, 237, 243)
DIM = (139, 148, 158)
ACCENT = (240, 180, 41)
GREEN = (63, 185, 80)


def capture_output(repo: str) -> list[str]:
    env = dict(os.environ, PYTHONPATH=ROOT)
    out = subprocess.run([sys.executable, "-m", "pip_pip", repo],
                         capture_output=True, text=True, env=env)
    lines = [ln.rstrip() for ln in out.stdout.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines[:21]


def frame(lines: list[tuple[str, tuple, bool]], height: int) -> Image.Image:
    img = Image.new("RGB", (W, height), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, height - 1], radius=10, outline=(48, 54, 61), width=2)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 22 + i * 22
        d.ellipse([cx, 16, cx + 12, 28], fill=color)
    d.text((W // 2 - 60, 14), "on-a-pip", font=ImageFont.truetype(FONT_PATH, 13), fill=DIM)
    y = PAD_Y
    for text, color, bold in lines:
        font = ImageFont.truetype(FONT_BOLD if bold else FONT_PATH, SIZE)
        d.text((PAD_X, y), text, font=font, fill=color)
        y += LH
    return img


def style(line: str) -> tuple[str, tuple, bool]:
    if "PERFORMANCE IMPROVEMENT PLAN" in line:
        return line, FG, True
    if line.strip().startswith(("OVERALL", "AWARDS")):
        return line, ACCENT, True
    if line.startswith("$"):
        return line, GREEN, False
    if line.startswith("Successfully"):
        return line, DIM, False
    return line, FG, False


def main() -> None:
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "examples", "demo.gif")
    output = capture_output(repo)
    total_lines = 4 + len(output)
    height = PAD_Y + total_lines * LH + 18

    frames: list[Image.Image] = []
    durations: list[int] = []
    shown: list[tuple[str, tuple, bool]] = []

    def push(dur: int = 80) -> None:
        frames.append(frame(shown, height))
        durations.append(dur)

    cmd1 = "$ pip install on-a-pip"
    for i in range(0, len(cmd1) + 1, 3):
        shown = [style(cmd1[:i] + "▌")]
        push(60)
    shown = [style(cmd1), style("Successfully installed on-a-pip-1.0.1")]
    push(500)
    cmd2 = "$ on-a-pip"
    for i in range(0, len(cmd2) + 1, 2):
        shown = [style(cmd1), style("Successfully installed on-a-pip-1.0.1"), style(cmd2[:i] + "▌")]
        push(60)
    shown = [style(cmd1), style("Successfully installed on-a-pip-1.0.1"), style(cmd2), ("", FG, False)]
    push(350)
    base = list(shown)
    for i in range(0, len(output), 2):
        shown = base + [style(ln) for ln in output[:i + 2]]
        push(110)
    push(2600)

    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    print(f"wrote {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
