"""Issue-driven chess. Visitors play white by opening an issue titled 'chess: move e2e4';
Stockfish answers as black. Usage: python scripts/chess_game.py [--init]
Env: ISSUE_TITLE, ISSUE_USER, GITHUB_REPOSITORY, RESULT_FILE"""
import os, re, sys, json, random, time, pathlib, urllib.parse
import chess, chess.engine
from theme import *

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "chess" / "state.json"
SVGF = ROOT / "assets" / "chess.svg"
README = ROOT / "README.md"
REPO = os.environ.get("GITHUB_REPOSITORY", "darshitsorathiya/darshitsorathiya")
ENGINES = ["/usr/games/stockfish", "stockfish"]

SPR = {"P": ["........", "...##...", "..####..", "...##...", "..####..", "...##...", "..####..", ".######."],
       "R": ["##.##.##", "########", ".######.", "..####..", "..####..", "..####..", ".######.", "########"],
       "N": ["..##....", ".####...", "######..", "#.####..", "..####..", "..#####.", ".######.", "########"],
       "B": ["...##...", "..####..", ".##.###.", "..####..", "...##...", "..####..", "...##...", ".######."],
       "Q": ["#..##..#", "#.####.#", "########", ".######.", "..####..", "..####..", ".######.", "########"],
       "K": ["...##...", ".######.", "...##...", "..####..", ".######.", "..####..", ".######.", "########"]}

def fresh(games): return {"fen": chess.STARTING_FEN, "moves": [], "last": None, "last_player": None, "result": None, "games": games + 1}
def load(): return json.loads(STATE.read_text()) if STATE.exists() else fresh(0)
def save(s): STATE.parent.mkdir(exist_ok=True); STATE.write_text(json.dumps(s, indent=1))

def engine_reply(board):
    for path in ENGINES:
        try:
            with chess.engine.SimpleEngine.popen_uci(path) as eng:
                try: eng.configure({"Skill Level": 6})
                except Exception: pass
                return eng.play(board, chess.engine.Limit(time=0.3)).move
        except Exception: continue
    return random.choice(list(board.legal_moves))      # fallback if Stockfish is missing

def outcome_text(board):
    o = board.outcome(claim_draw=True)
    if o is None: return None
    who = "White (visitors) wins" if o.winner is True else "Black (Stockfish) wins" if o.winner is False else "Draw"
    return f"{who} — {o.termination.name.lower().replace('_', ' ')}"

def handle(state, title, user):
    t = (title or "").strip()
    if re.fullmatch(r"chess:\s*new", t, re.I):
        if not state["result"]: return state, "A game is still in progress — finish it first."
        return fresh(state["games"]), "New game started. You play white!"
    m = re.fullmatch(r"chess:\s*move\s+([a-h][1-8][a-h][1-8][qrbn]?)", t, re.I)
    if not m: return state, "Couldn't read that. Use a title like `chess: move e2e4`."
    if state["result"]: return state, f"The game is over ({state['result']}). Open `chess: new` to start another."
    board = chess.Board(state["fen"]); mv = chess.Move.from_uci(m.group(1).lower())
    if mv not in board.legal_moves: return state, f"`{mv.uci()}` isn't a legal move right now. Pick one from the README list."
    san = board.san(mv); board.push(mv); state["moves"].append(san); state["last"] = mv.uci(); state["last_player"] = user
    reply = f"You played **{san}**."
    if not board.is_game_over(claim_draw=True):
        em = engine_reply(board); esan = board.san(em); board.push(em); state["moves"].append(esan); state["last"] = em.uci()
        reply += f" Stockfish replied **{esan}**."
    state["fen"] = board.fen(); state["result"] = outcome_text(board)
    if state["result"]: reply += f" Game over: {state['result']}."
    return state, reply

def render(state):
    board = chess.Board(state["fen"]); ox, oy, sq = 20, 60, 50
    last = chess.Move.from_uci(state["last"]) if state["last"] else None
    hi = {last.from_square, last.to_square} if last else set()
    ch = R(0, 0, 800, 520, BG) + heading(20, 38, "CHESS", 800) + R(ox - 6, oy - 6, sq * 8 + 12, sq * 8 + 12, CARD, 6, f'stroke="{BORDER}"')
    for s in chess.SQUARES:
        f, r = chess.square_file(s), 7 - chess.square_rank(s); light = (r + f) % 2 == 0
        ch += R(ox + f * sq, oy + r * sq, sq, sq, ("#8a8a2a" if light else "#5e5e1c") if s in hi else ("#2f6b4a" if light else "#14291f"))
        if f == 0: ch += T(ox + 3, oy + r * sq + 12, str(r and 8 - r or 8), 10, DIM)
        if r == 7: ch += T(ox + f * sq + sq - 10, oy + r * sq + sq - 4, "abcdefgh"[f], 10, DIM)
        pc = board.piece_at(s)
        if pc:
            col = "#f6ead3" if pc.color else "#e5731a"; spr = SPR[pc.symbol().upper()]
            sx, sy = ox + f * sq + 9, oy + r * sq + 9
            for j, row in enumerate(spr):
                for i, c in enumerate(row):
                    if c == "#": ch += R(sx + i * 4 - 1, sy + j * 4 - 1, 6, 6, "#0b0f0c")
            for j, row in enumerate(spr):
                for i, c in enumerate(row):
                    if c == "#": ch += R(sx + i * 4, sy + j * 4, 4, 4, col)
    px0 = 450; ch += R(px0, 60, 330, 400, CARD, 10, f'stroke="{BORDER}"') + T(px0 + 20, 95, "$ chess --vs stockfish", 14, GREEN, "bold")
    mv = state["moves"]; rows = [(i // 2 + 1, mv[i], mv[i + 1] if i + 1 < len(mv) else "") for i in range(0, len(mv), 2)][-7:]
    for k, (n, w, b) in enumerate(rows): ch += T(px0 + 20, 130 + k * 24, esc(f"{n:>2}. {w:<8}{b}"), 15, WHITE)
    if not mv: ch += T(px0 + 20, 130, "no moves yet — you're white", 13, DIM)
    status = state["result"] or ("white to move" + (" — CHECK!" if board.is_check() else ""))
    ch += T(px0 + 20, 335, esc("status: " + short(status, 30)), 13, DIM if not state["result"] else GREEN)
    ch += T(px0 + 20, 357, esc("last  : " + (f'{state["last"]}' + (f' by @{state["last_player"]}' if state["last_player"] else "") if state["last"] else "-")[:30]), 13, DIM)
    ch += T(px0 + 20, 379, f'game  : #{state["games"]}', 13, DIM)
    ch += R(px0 + 20, 400, 14, 14, "#f6ead3") + T(px0 + 42, 412, "white — visitors", 13, WHITE)
    ch += R(px0 + 20, 424, 14, 14, "#e5731a") + T(px0 + 42, 436, "black — stockfish", 13, WHITE)
    return svg(800, 480, ch)

def short(s, n): return s if len(s) <= n else s[:n - 1] + "…"

def issue_link(title):
    return (f"https://github.com/{REPO}/issues/new?title={urllib.parse.quote(title)}"
            f"&body={urllib.parse.quote(chr(39).join(['Just press ', 'Submit new issue', '. Do not change the title.']))}")

V = int(time.time())
UI = ROOT / "assets" / "ui"; MV = ROOT / "assets" / "moves"
COL = {"move": "#3fb950", "capture": "#e5731a", "check": "#f85149", "castle": "#a371f7", "promote": "#ffd54a"}
PIECE_NAMES = {1: "PAWNS", 2: "KNIGHTS", 3: "BISHOPS", 4: "ROOKS", 5: "QUEEN", 6: "KING"}
SYM = {1: "P", 2: "N", 3: "B", 4: "R", 5: "Q", 6: "K"}

def sprite(x, y, sym, col, px=3):
    spr = SPR[sym]; o = ""
    for j, row in enumerate(spr):
        for i, c in enumerate(row):
            if c == "#": o += R(x + i * px - 1, y + j * px - 1, px + 2, px + 2, "#0b0f0c")
    for j, row in enumerate(spr):
        for i, c in enumerate(row):
            if c == "#": o += R(x + i * px, y + j * px, px, px, col)
    return o

def classify(board, m):
    kind, tag = "move", ""
    if board.is_castling(m): kind, tag = "castle", ("O-O" if chess.square_file(m.to_square) == 6 else "O-O-O")
    elif m.promotion: kind, tag = "promote", "=" + chess.piece_symbol(m.promotion).upper()
    elif board.is_capture(m): kind, tag = "capture", "x"
    if board.gives_check(m): kind, tag = "check", tag + "+"
    return kind, tag

def button_svg(board, m):
    kind, tag = classify(board, m); col = COL[kind]; sym = board.piece_at(m.from_square).symbol().upper()
    fr, to = chess.square_name(m.from_square), chess.square_name(m.to_square)
    b = R(1, 1, 148, 38, CARD, 6, f'stroke="{col}" stroke-width="2"') + R(4, 4, 4, 32, col) + sprite(16, 8, sym, "#f6ead3")
    b += T(48, 26, f'<tspan fill="{DIM}">{fr}</tspan> <tspan fill="{col}">→</tspan> <tspan fill="{WHITE}" font-weight="bold">{to}</tspan>', 14)
    b += T(144, 25, esc(tag), 11, col, "bold", 'text-anchor="end"')
    return svg(150, 40, b)

def group_svg(pt):
    n = PIECE_NAMES[pt]
    return svg(180, 30, sprite(4, 3, SYM[pt], "#f6ead3") + T(36, 21, n, 13, GREEN, "bold", 'letter-spacing="3"') +
               f'<line x1="{36 + len(n) * 11 + 10}" y1="16" x2="176" y2="16" stroke="#2a3a2f" stroke-dasharray="3 4"/>')

def cursor(x, y): return f'<rect x="{x}" y="{y}" width="9" height="14" fill="{GREEN}"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></rect>'

def header_svg(state):
    over = bool(state["result"]); h = 130 if over else 150
    s = R(0, 0, 800, h, CARD, 12, f'stroke="{BORDER}"')
    if over:
        s += T(24, 42, "&gt; GAME OVER", 22, "#e5731a", "bold", 'letter-spacing="3"') + T(24, 76, esc(state["result"]), 16, WHITE, "bold")
        s += T(24, 108, "$ ./play --new", 13, GREEN) + cursor(24 + 15 * 7.9 + 8, 96)
    else:
        n = len(state["moves"]) // 2 + 1
        s += T(24, 40, "&gt; YOUR MOVE, CHALLENGER", 20, GREEN, "bold", 'letter-spacing="3"')
        s += T(24, 72, "$ ./play --side white --vs stockfish", 13, DIM) + T(24, 94, f"move #{n} · cream army = you · orange army = stockfish", 13, WHITE)
        s += T(24, 124, "&gt; pick a move below", 13, GREEN) + cursor(24 + 22 * 7.9 + 8, 112)
        for i, (k, nm) in enumerate([("move", "move"), ("capture", "capture"), ("check", "check"), ("castle", "castle"), ("promote", "promote")]):
            s += R(600, 52 + i * 18, 10, 10, COL[k]) + T(618, 62 + i * 18, nm, 12, DIM)
    return svg(800, h, s)

def newgame_svg():
    return svg(220, 40, R(1, 1, 218, 38, CARD, 6, 'stroke="#e5731a" stroke-width="2"') + '<polygon points="16,10 16,30 34,20" fill="#e5731a"/>' + T(46, 26, "START NEW GAME", 14, WHITE, "bold"))

def build_ui(state):
    UI.mkdir(parents=True, exist_ok=True); MV.mkdir(parents=True, exist_ok=True)
    for f in MV.glob("*.svg"): f.unlink()
    (UI / "header.svg").write_text(header_svg(state), encoding="utf-8"); (UI / "new-game.svg").write_text(newgame_svg(), encoding="utf-8")
    for pt in PIECE_NAMES: (UI / f"group-{pt}.svg").write_text(group_svg(pt), encoding="utf-8")
    if not state["result"]:
        board = chess.Board(state["fen"])
        for m in board.legal_moves: (MV / f"{m.uci()}.svg").write_text(button_svg(board, m), encoding="utf-8")

def img(src, alt, w): return f'<img src="{src}?v={V}" alt="{alt}" width="{w}"/>'

def readme_block(state):
    board = chess.Board(state["fen"]); out = [img("assets/ui/header.svg", "chess status", 800)]
    if state["result"]:
        out.append(f'<a href="{issue_link("chess: new")}">{img("assets/ui/new-game.svg", "start new game", 220)}</a>')
    else:
        groups = {}
        for m in board.legal_moves: groups.setdefault(board.piece_at(m.from_square).piece_type, []).append(m)
        for pt in sorted(groups):
            btns = [f'<a href="{issue_link("chess: move " + m.uci())}">{img("assets/moves/" + m.uci() + ".svg", m.uci(), 150)}</a>'
                    for m in sorted(groups[pt], key=lambda m: (m.from_square, m.to_square, m.promotion or 0))]
            out.append(img(f"assets/ui/group-{pt}.svg", PIECE_NAMES[pt], 180) + "<br>\n" + "\n".join(btns))
    if state["last"]:
        out.append(f'<sub>▸ last move <code>{state["last"]}</code>' + (f' by <b>@{esc(state["last_player"])}</b>' if state["last_player"] else "") + "</sub>")
    return '<div align="center">\n' + "\n<br>\n".join(out) + "\n</div>"

def update_readme(state):
    t = README.read_text(encoding="utf-8")
    t = re.sub(r"<!--CHESS_START-->.*?<!--CHESS_END-->", lambda _: f"<!--CHESS_START-->\n{readme_block(state)}\n<!--CHESS_END-->", t, flags=re.S)
    README.write_text(bust(t, ["chess"], int(time.time())), encoding="utf-8")

def main():
    state = load(); msg = "Board refreshed."
    if "--init" not in sys.argv: state, msg = handle(state, os.environ.get("ISSUE_TITLE", ""), os.environ.get("ISSUE_USER", "visitor"))
    save(state); build_ui(state); SVGF.parent.mkdir(exist_ok=True); SVGF.write_text(render(state), encoding="utf-8"); update_readme(state)
    pathlib.Path(os.environ.get("RESULT_FILE", "/tmp/chess_result.txt")).write_text(msg)
    print(msg)

if __name__ == "__main__": main()
