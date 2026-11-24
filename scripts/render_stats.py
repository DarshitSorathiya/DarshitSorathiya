"""Fetch live GitHub data and regenerate banner/about/projects/activity SVGs.
Usage: python scripts/render_stats.py [--mock]"""
import os, sys, json, random, hashlib, pathlib, time, urllib.request
from theme import *

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LOGIN = os.environ.get("GITHUB_REPOSITORY_OWNER") or os.environ.get("PROFILE_LOGIN") or "darshitsorathiya"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

QUERY = """
query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(ownerAffiliations:OWNER, privacy:PUBLIC, first:100, orderBy:{field:PUSHED_AT,direction:DESC}){
    totalCount nodes{ name description stargazerCount isFork primaryLanguage{name color} } }
  pinnedItems(first:4,types:REPOSITORY){ nodes{ ... on Repository{
    name description stargazerCount primaryLanguage{name color} } } }
  contributionsCollection{ totalCommitContributions totalPullRequestContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } }
}}"""

def http(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-readme"})
    if data: req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)

def streaks(days):
    counts = [d["count"] for d in days]
    best = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0: i -= 1          # today may not have commits yet
    cur = 0
    while i >= 0 and counts[i] > 0: cur += 1; i -= 1
    return cur, best

def fetch():
    u = http("https://api.github.com/graphql",
             json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode())["data"]["user"]
    repos = u["repositories"]["nodes"]
    cc = u["contributionsCollection"]; cal = cc["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"]} for d in w["contributionDays"]] for w in cal["weeks"]]
    flat = [d for w in weeks for d in w]
    cur, best = streaks(flat)
    def proj(n): return {"name": n["name"], "desc": n["description"] or "A project in progress.",
                         "stars": n["stargazerCount"], "lang": (n["primaryLanguage"] or {}).get("name", ""),
                         "color": (n["primaryLanguage"] or {}).get("color") or "#8b949e"}
    projects = [proj(n) for n in u["pinnedItems"]["nodes"]]
    for n in repos:
        if len(projects) >= 4: break
        if not n["isFork"] and n["name"] not in [p["name"] for p in projects]: projects.append(proj(n))
    langs = []
    for n in repos:
        l = n["primaryLanguage"]
        if l and l["color"] and l["color"] not in langs: langs.append(l["color"])
    lines = []
    try:
        for e in http(f"https://api.github.com/users/{LOGIN}/events/public"):
            if e["type"] == "PushEvent":
                for c in reversed(e["payload"].get("commits", [])):
                    lines.append(f'{e["repo"]["name"].split("/")[-1]}: {c["message"].splitlines()[0]}')
            if len(lines) >= 6: break
    except Exception: pass
    return {"login": LOGIN, "followers": u["followers"]["totalCount"], "repos": u["repositories"]["totalCount"],
            "stars": sum(n["stargazerCount"] for n in repos), "commits": cc["totalCommitContributions"],
            "prs": cc["totalPullRequestContributions"], "projects": projects[:4], "weeks": weeks,
            "year": cal["totalContributions"], "current": cur, "best": best,
            "commit_lines": lines[:6], "lang_colors": langs[:5]}

def mock():
    random.seed(5)
    weeks = [[{"date": "", "count": 0 if random.random() < .85 else random.randint(1, 9)} for _ in range(7)] for _ in range(53)]
    return {"login": LOGIN, "followers": 5, "repos": 17, "stars": 4, "commits": 92, "prs": 22,
            "projects": [
                {"name": "SkillSwap", "desc": "A project in progress.", "stars": 1, "lang": "JavaScript", "color": "#f1e05a"},
                {"name": "DarshitSorathiya", "desc": "A project in progress.", "stars": 1, "lang": "", "color": "#8b949e"},
                {"name": "derma.ai", "desc": "A project in progress.", "stars": 1, "lang": "Jupyter Notebook", "color": "#DA5B0B"},
                {"name": "Bank-Management-System-Java", "desc": "A project in progress.", "stars": 1, "lang": "Java", "color": "#b07219"}],
            "weeks": weeks, "year": 124, "current": 1, "best": 2,
            "commit_lines": ["Trionic_Intern: Final changes", "Trionic_Intern: Running project", "Trionic_Intern: bug fixed",
                             "DocAssistant: DocAssistant ready", "L2: name change", "L2: Complete"],
            "lang_colors": ["#3572A5", "#f1e05a", "#b07219", "#DA5B0B"]}

def short(s, n): return s if len(s) <= n else s[:n - 1] + "…"

def pixel_sprite(x, y, seed, fg, cell=8, cols=5, rows=8):
    rnd = random.Random(hashlib.md5(seed.encode()).hexdigest()); out = ""
    for j in range(rows):
        for i in range(cols):
            if rnd.random() > .42:
                out += R(x + i * cell, y + j * cell, cell, cell, fg)
                out += R(x + (2 * cols - 1 - i) * cell, y + j * cell, cell, cell, fg)
    return out

def banner(d):
    name = d["login"].upper(); b = R(0, 0, 800, 360, "#1a1f2e", 12)
    for x in range(0, 800, 40): b += R(x, 0, 20, 300, "#1d2335")
    b += R(0, 300, 800, 60, "#4a2f22") + R(0, 296, 800, 6, "#6b4630")
    for x in range(0, 800, 100): b += R(x, 302, 3, 58, "#3a251a")
    b += R(60, 50, 170, 150, "#2a2f3d")
    for x, y in [(68, 58), (150, 58), (68, 130), (150, 130)]: b += R(x, y, 74, 64 if y == 130 else 66, "#74b9ff")
    b += R(160, 70, 36, 12, "#fff") + R(176, 62, 24, 12, "#fff") + R(196, 70, 18, 18, "#ffd54a") + R(52, 200, 186, 10, "#5a3d2b")
    size = min(28, int(310 / (len(name) * 0.62)))
    b += R(236, 40, 330, 50, "#2b2118") + R(240, 44, 322, 42, "#f6ead3")
    b += T(401, 74 + (28 - size) // 3, esc(name), size, "#2b2118", "bold", 'text-anchor="middle" letter-spacing="1"')
    b += '<circle cx="680" cy="75" r="26" fill="#f6ead3" stroke="#2b2118" stroke-width="3"/><path d="M680 75V58M680 75L692 82" stroke="#2b2118" stroke-width="3"/>'
    b += R(270, 160, 50, 22, "#ffd54a") + R(293, 182, 6, 110, "#555b6b")
    b += R(330, 125, 230, 150, "#3a4056") + R(338, 133, 214, 130, "#0e1a2e") + R(430, 275, 30, 12, "#2a2f3d")
    lines = ["$ git log --oneline"] + [short(l, 31) for l in (d["commit_lines"] or ["no recent public commits"])]
    for i, l in enumerate(lines[:7]): b += T(346, 153 + i * 17, esc(l), 11, "#7ee787" if i else WHITE)
    b += R(275, 290, 300, 10, "#6b4630") + R(285, 300, 8, 70, "#5a3d2b") + R(560, 300, 8, 70, "#5a3d2b")
    b += R(520, 262, 26, 24, "#e6e0d0") + R(546, 268, 8, 10, "#e6e0d0") + R(418, 300, 44, 6, "#2a2f3d") + R(436, 306, 8, 50, "#2a2f3d")
    b += R(95, 260, 10, 40, "#3fb950") + R(75, 255, 22, 8, "#3fb950") + R(105, 270, 26, 8, "#3fb950") + R(88, 285, 10, 8, "#3fb950")
    b += R(82, 305, 50, 50, "#a0583a") + R(78, 300, 58, 8, "#7a4028")
    b += R(610, 150, 160, 8, "#6b4630") + R(610, 230, 160, 8, "#6b4630")
    rnd = random.Random(1)
    for k, c in enumerate((d["lang_colors"] or ["#2f6fb5"])[:5]):          # one book per language
        h = rnd.choice([36, 40, 44]); b += R(616 + k * 24, 150 - h, 18, h, c)
    b += R(620, 330, 70, 16, "#e8a05a") + R(690, 322, 18, 18, "#e8a05a") + R(610, 334, 12, 6, "#c97d3a") + R(630, 336, 50, 3, "#c97d3a")
    return svg(800, 360, b)

def about(d):
    a = R(0, 0, 800, 330, BG) + R(0, 0, 800, 230, CARD, 12, f'stroke="{BORDER}"')
    a += T(30, 50, "&gt; ABOUT", 16, GREEN, "normal", 'letter-spacing="2"') + T(30, 100, esc(d["login"]), 28, WHITE, "bold")
    a += T(30, 135, "Python developer. Working on Trionic_Intern right now.", 15, DIM)
    a += T(30, 190, f'{d["followers"]} followers · {d["repos"]} repositories · ★ {d["stars"]} stars', 13, DIM)
    a += R(650, 40, 120, 120, "#000", 0, f'stroke="{WHITE}" stroke-width="3"')
    rnd = random.Random(hashlib.md5(d["login"].encode()).hexdigest())
    for i in range(12):
        for j in range(12):
            dist = ((i - 6) ** 2 + (j - 6) ** 2) ** .5
            if rnd.random() > dist / 8:
                a += R(656 + i * 9.8, 46 + j * 9.8, 9.8, 9.8, rnd.choice(["#ffd54a", "#ff7a3d", "#6c5ce7", "#74b9ff", "#fff"]) if dist < 3 else rnd.choice(["#2b3a8f", "#5a2a82", "#1a1f4a"]))
    a += R(0, 250, 800, 70, CARD, 8, f'stroke="{BORDER}"')
    for x, n, l in [(20, d["commits"], "COMMITS"), (200, d["prs"], "PULL REQS"), (380, d["stars"], "STARS"), (560, f'{d["best"]}D', "BEST STREAK")]:
        a += T(x + 10, 288, esc(n), 34, WHITE, "bold") + T(x + 10, 308, l, 13, DIM, "normal", 'letter-spacing="2"')
    return svg(800, 330, a)

def projects(d):
    p = R(0, 0, 800, 355, BG) + heading(20, 38, "PROJECTS", 800)
    for k, pr in enumerate(d["projects"][:4]):
        x = 20 + (k % 2) * 370; y = 65 + (k // 2) * 140
        p += R(x, y, 355, 125, CARD, 10, f'stroke="{BORDER}"') + R(x + 12, y + 22, 80, 80, mix(pr["color"], .45), 8)
        p += pixel_sprite(x + 20, y + 30, pr["name"], pr["color"], 8, 4)
        p += T(x + 110, y + 38, esc(short(pr["name"], 24)), 15, WHITE, "bold") + T(x + 110, y + 65, esc(short(pr["desc"], 30)), 12, DIM)
        p += T(x + 110, y + 108, f'✱ {pr["stars"]}', 15, GREEN)
        if pr["lang"]: p += R(x + 205, y + 98, 10, 10, pr["color"], 2) + T(x + 222, y + 108, esc(short(pr["lang"], 16)), 11, DIM)
    return svg(800, 355, p)

def activity(d):
    c = R(0, 0, 800, 240, CARD, 12, f'stroke="{BORDER}"') + T(30, 45, "&gt; ACTIVITY", 16, GREEN, "normal", 'letter-spacing="2"')
    weeks = d["weeks"][-26:]; mx = max([x["count"] for w in weeks for x in w] + [1])
    for ci, w in enumerate(weeks):
        for ri, day in enumerate(w):
            v = day["count"] / mx
            col = "#1c2330" if day["count"] == 0 else ("#0e4429" if v < .25 else "#006d32" if v < .5 else "#26a641" if v < .75 else "#39d353")
            c += R(30 + ci * 13, 70 + ri * 13, 11, 11, col, 2)
    for i, (l, n) in enumerate([("CURRENT STREAK", f'{d["current"]} day{"" if d["current"] == 1 else "s"}'),
                                ("BEST STREAK", f'{d["best"]} day{"" if d["best"] == 1 else "s"}'), ("THIS YEAR", d["year"])]):
        c += T(500, 75 + i * 48, l, 11, DIM, "normal", 'letter-spacing="2"') + T(500, 98 + i * 48, esc(n), 22, WHITE, "bold")
    return svg(800, 240, c)

def main():
    d = mock() if "--mock" in sys.argv else fetch()
    ASSETS.mkdir(exist_ok=True)
    for name, fn in [("banner", banner), ("about", about), ("projects", projects), ("activity", activity)]:
        (ASSETS / f"{name}.svg").write_text(fn(d), encoding="utf-8")
    rd = ROOT / "README.md"
    rd.write_text(bust(rd.read_text(encoding="utf-8"), ["banner", "about", "projects", "activity"], int(time.time())), encoding="utf-8")
    print("stats rendered for", d["login"])

if __name__ == "__main__": main()
