"""Shared SVG helpers + palette for the pixel/terminal theme."""
import html, re
F = "font-family=\"'Courier New',Consolas,monospace\""
BG = "#0d1117"; CARD = "#151b23"; BORDER = "#242c38"
GREEN = "#3fb950"; DIM = "#8b949e"; WHITE = "#e6edf3"

def esc(s): return html.escape(str(s), quote=True)
def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
def R(x, y, w, h, c, rx=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" rx="{rx}" {extra}/>'
def T(x, y, s, size=14, c=WHITE, w="normal", extra=""):
    return f'<text x="{x}" y="{y}" {F} font-size="{size}" fill="{c}" font-weight="{w}" {extra}>{s}</text>'
def heading(x, y, s, w):
    return (T(x, y, "&gt; " + s, 22, GREEN, "bold", 'letter-spacing="3"') +
            f'<line x1="{x + len(s) * 16 + 60}" y1="{y - 6}" x2="{w - 20}" y2="{y - 6}" stroke="#2a3a2f" stroke-dasharray="3 4"/>')

def mix(hex_c, k):
    """Darken a #rrggbb colour toward black by factor k (0..1 keeps k of it)."""
    h = hex_c.lstrip("#")
    if len(h) != 6: h = "8b949e"
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))

def bust(text, names, v):
    """Add ?v=<n> to image URLs so GitHub's image proxy refetches them."""
    pat = r"(assets/(?:%s)\.svg)(\?v=\d+)?" % "|".join(names)
    return re.sub(pat, rf"\1?v={v}", text)
