#!/usr/bin/env python3
"""Render the ALU directed-test VCD into an SVG waveform (no dependencies).

Usage: python3 scripts/vcd_to_svg.py alu_4bit.vcd docs/alu_waveform.svg
"""
import sys
from pathlib import Path

SIGNALS = [  # (hierarchical name, label, kind)
    ("alu_4bit_tb.opcode", "opcode[2:0]", "op"),
    ("alu_4bit_tb.A", "A[3:0]", "num"),
    ("alu_4bit_tb.B", "B[3:0]", "num"),
    ("alu_4bit_tb.result", "result[3:0]", "num"),
    ("alu_4bit_tb.carry", "carry", "bit"),
    ("alu_4bit_tb.zero", "zero", "bit"),
]
OPS = ["ADD", "SUB", "AND", "OR", "XOR", "NOT A", "INC A", "DEC A"]
SYM = {0: "+", 1: "−", 2: "&", 3: "|", 4: "^"}

BG, GRID, TEXT, MUTED = "#ffffff", "#e6e8eb", "#1f2328", "#656d76"
WAVE, BUS_FILL, OP_FILL, ACCENT = "#1a7f37", "#dafbe1", "#ddf4ff", "#0969da"


def parse_vcd(path, wanted):
    ids, scope, scale = {}, [], 1
    changes = {name: [] for name in wanted}
    t, end = 0, None
    with open(path) as f:
        it = iter(f)
        for line in it:
            tok = line.split()
            if not tok:
                continue
            if tok[0] == "$timescale":
                spec = tok[1] if len(tok) > 1 else next(it).strip()
                unit = {"s": 1e12, "ms": 1e9, "us": 1e6, "ns": 1e3, "ps": 1}
                num = "".join(c for c in spec if c.isdigit())
                scale = int(num) * unit[spec[len(num):]]
            elif tok[0] == "$scope":
                scope.append(tok[2])
            elif tok[0] == "$upscope":
                scope.pop()
            elif tok[0] == "$var":
                name = ".".join(scope + [tok[4]])
                if name in changes:
                    ids.setdefault(tok[3], []).append(name)
            elif tok[0] == "$enddefinitions":
                break
        for line in it:
            line = line.strip()
            if not line:
                continue
            if line.startswith("$dumpoff"):  # directed phase ends here
                end = t
                break
            if line[0] == "$":
                continue
            c = line[0]
            if c == "#":
                t = int(line[1:]) * scale
            elif c in "01xzXZ":
                for n in ids.get(line[1:], ()):
                    changes[n].append((t, line[0]))
            elif c in "bB":
                val, ident = line[1:].split()
                for n in ids.get(ident, ()):
                    changes[n].append((t, val))
    return changes, end if end is not None else t


def value_at(ch, t):
    v = None
    for ct, cv in ch:
        if ct > t:
            break
        v = cv
    return v


def segments(ch, t0, t1):
    out, cur, start = [], value_at(ch, t0), t0
    for ct, cv in ch:
        if ct <= t0:
            continue
        if ct >= t1:
            break
        if cv != cur:
            out.append((start, ct, cur))
            start, cur = ct, cv
    out.append((start, t1, cur))
    return out


def as_int(v):
    try:
        return int(v, 2)
    except (TypeError, ValueError):
        return None


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def describe(op, a, b, r, c):
    if op in SYM:
        txt = f"{a} {SYM[op]} {b} = {r}"
    elif op == 5:
        txt = f"~{a} = {r}"
    elif op == 6:
        txt = f"{a} + 1 = {r}"
    else:
        txt = f"{a} − 1 = {r}"
    return txt


def render(changes, t0, t1, width=1280):
    left, right, top = 150, 24, 128
    row_h, wave_h = 46, 26
    plot_w = width - left - right
    rows = len(SIGNALS)
    height = top + rows * row_h + 64
    X = lambda t: left + (t - t0) / (t1 - t0) * plot_w
    sans = "-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         f'<rect width="100%" height="100%" fill="{BG}"/>',
         f'<text x="24" y="34" font-size="20" font-weight="700" fill="{TEXT}" font-family="{sans}">'
         f'4-bit ALU: directed test waveform (8 operations + flag edge cases)</text>',
         f'<text x="24" y="58" font-size="13" fill="{MUTED}" font-family="{sans}">'
         f'Combinational design: outputs settle as soon as the inputs change. Every step below is checked '
         f'by the testbench, plus an exhaustive sweep of all 2048 input combinations.</text>']

    # one annotation cell per test step (boundaries = opcode/A/B changes)
    edges = sorted({t for n in ("alu_4bit_tb.opcode", "alu_4bit_tb.A", "alu_4bit_tb.B")
                    for t, _ in changes[n] if t0 <= t < t1} | {t0, t1})
    y0 = top - 48
    for i, (a_t, b_t) in enumerate(zip(edges, edges[1:])):
        mid = (a_t + b_t) / 2
        op = as_int(value_at(changes["alu_4bit_tb.opcode"], mid))
        a = as_int(value_at(changes["alu_4bit_tb.A"], mid))
        b = as_int(value_at(changes["alu_4bit_tb.B"], mid))
        r = as_int(value_at(changes["alu_4bit_tb.result"], mid))
        c = value_at(changes["alu_4bit_tb.carry"], mid)
        xa, xb = X(a_t), X(b_t)
        shade = "#ddf4ff" if i % 2 == 0 else "#f6f8fa"
        o.append(f'<rect x="{xa:.1f}" y="{y0}" width="{xb - xa:.1f}" height="36" fill="{shade}" stroke="{GRID}"/>')
        o.append(f'<text x="{(xa + xb) / 2:.1f}" y="{y0 + 15}" font-size="11" fill="{ACCENT}" '
                 f'text-anchor="middle" font-weight="700">{esc(OPS[op])}</text>')
        o.append(f'<text x="{(xa + xb) / 2:.1f}" y="{y0 + 30}" font-size="11" fill="{TEXT}" '
                 f'text-anchor="middle">{esc(describe(op, a, b, r, c))}</text>')
        o.append(f'<line x1="{xa:.1f}" y1="{y0 + 36}" x2="{xa:.1f}" y2="{top + rows * row_h}" '
                 f'stroke="{ACCENT}" stroke-opacity="0.25" stroke-dasharray="3 3"/>')

    # time axis
    axis_y = top + rows * row_h + 22
    step = 10_000  # 10 ns
    k = 0
    while t0 + k * step <= t1:
        x = X(t0 + k * step)
        o.append(f'<text x="{x:.1f}" y="{axis_y}" font-size="11" fill="{MUTED}" text-anchor="middle">{(t0 + k * step) // 1000} ns</text>')
        k += 1

    for r, (name, label, kind) in enumerate(SIGNALS):
        yc = top + r * row_h + row_h / 2
        hi, lo = yc - wave_h / 2, yc + wave_h / 2
        if r % 2:
            o.append(f'<rect x="0" y="{top + r * row_h}" width="{width}" height="{row_h}" fill="#f6f8fa" fill-opacity="0.6"/>')
        o.append(f'<text x="{left - 14}" y="{yc + 4}" font-size="13" fill="{TEXT}" text-anchor="end">{label}</text>')
        segs = segments(changes[name], t0, t1)
        if kind == "bit":
            pts = []
            for a_t, b_t, v in segs:
                y = hi if v == "1" else lo
                pts += [(X(a_t), y), (X(b_t), y)]
                if v == "1":
                    o.append(f'<rect x="{X(a_t):.1f}" y="{hi}" width="{X(b_t) - X(a_t):.1f}" '
                             f'height="{wave_h}" fill="{WAVE}" fill-opacity="0.10"/>')
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            o.append(f'<path d="{d}" fill="none" stroke="{WAVE}" stroke-width="2" stroke-linejoin="round"/>')
        else:
            for a_t, b_t, v in segs:
                xa, xb = X(a_t), X(b_t)
                n = as_int(v)
                if kind == "op":
                    txt, fill = f"{n:03b} {OPS[n].split()[0]}", OP_FILL
                else:
                    txt, fill = f"{n:04b} ({n})", BUS_FILL
                sl = 5
                d = (f"M{xa:.1f},{yc} L{xa + sl:.1f},{hi} L{xb - sl:.1f},{hi} L{xb:.1f},{yc} "
                     f"L{xb - sl:.1f},{lo} L{xa + sl:.1f},{lo} Z")
                o.append(f'<path d="{d}" fill="{fill}" stroke="{WAVE}" stroke-width="1.5"/>')
                o.append(f'<text x="{(xa + xb) / 2:.1f}" y="{yc + 4}" font-size="12" fill="{TEXT}" text-anchor="middle">{txt}</text>')
    o.append(f'<line x1="{left}" y1="{top - 12}" x2="{left}" y2="{top + rows * row_h}" stroke="{GRID}"/>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    vcd, out = sys.argv[1], Path(sys.argv[2])
    ch, end = parse_vcd(vcd, [s[0] for s in SIGNALS])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(ch, 0, end))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
