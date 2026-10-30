"""Geometry pass over obfuscation-tax.pptx, standing in for a visual render.

Checks every shape against the canvas and the 0.5 inch margin, estimates the wrapped
height of each text box against the height it was given, and looks for text frames that
overlap. The footer band at y 6.98, which holds the source line and the slide number, is
the deck's own convention and is exempt from the bottom margin.

    uv run --with python-pptx python check_geometry.py obfuscation-tax.pptx
"""

import sys

from pptx import Presentation

EMU = 914400.0
CANVAS_W, CANVAS_H = 13.333, 7.5
MARGIN = 0.5
FOOTER_Y = 6.9
# Average glyph width as a fraction of the font size. Deliberately a little generous,
# so a box flagged here is worth looking at rather than certainly wrong.
CHAR_W = {"Cambria": 0.50, "Calibri": 0.47}
DEFAULT_FACE = "Calibri"
SLACK = 0.06


def paragraphs(tf):
    for p in tf.paragraphs:
        size, face, text = None, DEFAULT_FACE, ""
        for r in p.runs:
            text += r.text
            if r.font.size:
                size = r.font.size.pt
            if r.font.name:
                face = r.font.name
        if size is None:
            size = p.font.size.pt if p.font.size else 18.0
        yield text, size, face, p.line_spacing


def wrapped_height(tf, w):
    total = 0.0
    for text, size, face, spacing in paragraphs(tf):
        char_w = CHAR_W.get(face, CHAR_W[DEFAULT_FACE]) * size / 72.0
        per_line = max(1, int(w / char_w))
        lines = sum(max(1, -(-len(seg) // per_line)) for seg in (text.split("\n") or [""]))
        mult = spacing if isinstance(spacing, float) else 1.0
        total += lines * (size * 1.21 * mult) / 72.0
    return total


def in_footer(shape, y):
    return y >= FOOTER_Y and (shape.name == "source" or "Slide Number" in shape.name)


def main(path):
    prs = Presentation(path)
    issues = 0
    for n, slide in enumerate(prs.slides, 1):
        frames = []
        for sh in slide.shapes:
            if sh.left is None or sh.top is None:
                continue
            x, y = sh.left / EMU, sh.top / EMU
            w, h = (sh.width or 0) / EMU, (sh.height or 0) / EMU
            right, bottom = x + w, y + h
            if x < -0.001 or y < -0.001 or right > CANVAS_W + 0.001 or bottom > CANVAS_H + 0.001:
                print(f"slide {n}: {sh.name} is off the canvas, x={x:.2f} y={y:.2f} r={right:.2f} b={bottom:.2f}")
                issues += 1
            elif not in_footer(sh, y) and (
                x < MARGIN - 0.001
                or y < MARGIN - 0.001
                or right > CANVAS_W - MARGIN + 0.001
                or bottom > CANVAS_H - MARGIN + 0.001
            ):
                print(f"slide {n}: {sh.name} breaks the 0.5in margin, x={x:.2f} y={y:.2f} r={right:.2f} b={bottom:.2f}")
                issues += 1
            if sh.has_text_frame and sh.text_frame.text.strip():
                need = wrapped_height(sh.text_frame, w)
                if need > h + SLACK:
                    print(f"slide {n}: {sh.name} may wrap past its box, need {need:.2f} in {h:.2f}: {sh.text_frame.text[:44]!r}")
                    issues += 1
                frames.append((sh.name, x, y, w, h))
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                an, ax, ay, aw, ah = frames[i]
                bn, bx, by, bw, bh = frames[j]
                ox = min(ax + aw, bx + bw) - max(ax, bx)
                oy = min(ay + ah, by + bh) - max(ay, by)
                if ox > SLACK and oy > SLACK:
                    print(f"slide {n}: {an} and {bn} overlap by {ox:.2f} x {oy:.2f} in")
                    issues += 1
    print(f"{issues} issue(s) over {n} slides")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "obfuscation-tax.pptx"))
