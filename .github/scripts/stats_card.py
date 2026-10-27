#!/usr/bin/env python3
"""Generate profile/stats.svg from the PUBLIC GitHub API (no personal token needed).

Counts only public data: stars of owned non-fork repos, public repos, followers, public commits, pull requests and issues.
Env: GITHUB_REPOSITORY_OWNER (or GH_USER), optional GITHUB_TOKEN (only to raise the rate limit). Exits non-zero on API errors so the
workflow fails visibly instead of publishing an error image. Theme colours follow the 'radical' theme used by the other card.
"""
import json, os, sys, urllib.error, urllib.request
from xml.sax.saxutils import escape

user = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER")
out = sys.argv[1] if len(sys.argv) > 1 else "profile/stats.svg"
if not user:
    sys.exit("GITHUB_REPOSITORY_OWNER or GH_USER is required")
H = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-card", "X-GitHub-Api-Version": "2022-11-28"}
if os.environ.get("GITHUB_TOKEN"):
    H["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]


def get(path):
    try:
        with urllib.request.urlopen(urllib.request.Request("https://api.github.com" + path, headers=H), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API {e.code} on {path.split('?')[0]}")


u = get(f"/users/{user}")
stars, page = 0, 1
while True:
    repos = get(f"/users/{user}/repos?per_page=100&type=owner&page={page}")
    stars += sum(r["stargazers_count"] for r in repos if not r["fork"])
    if len(repos) < 100:
        break
    page += 1
commits = get(f"/search/commits?q=author:{user}&per_page=1")["total_count"]
prs = get(f"/search/issues?q=author:{user}+type:pr&per_page=1")["total_count"]
issues = get(f"/search/issues?q=author:{user}+type:issue&per_page=1")["total_count"]

rows = [("Estrellas / Stars", stars), ("Commits públicos / Public commits", commits), ("Pull requests", prs),
        ("Issues", issues), ("Repos públicos / Public repos", u["public_repos"]), ("Seguidores / Followers", u["followers"])]
h = 55 + 25 * len(rows)
y0 = 65
lines = "".join(
    f'<g transform="translate(25,{y0 + i * 25})"><text class="stat" y="12.5">{escape(k)}:</text>'
    f'<text class="stat bold" x="215" y="12.5">{v:,}</text></g>' for i, (k, v) in enumerate(rows))
svg = f'''<svg width="495" height="{h}" viewBox="0 0 495 {h}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t">
<title id="t">Estadísticas públicas de GitHub de {escape(user)}</title>
<style>
.header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #fe428e; }}
.stat {{ font: 600 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif; fill: #a9fef7; }}
.bold {{ font-weight: 700; }}
</style>
<rect x="0.5" y="0.5" rx="4.5" height="{h - 1}" width="494" fill="#141321" stroke="#e4e2e2" stroke-opacity="1"/>
<g transform="translate(25,35)"><text class="header">Estadísticas de GitHub de {escape(user)}</text></g>
{lines}
</svg>
'''
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w", encoding="utf-8", newline="\n").write(svg)
print(f"wrote {out}: stars={stars} commits={commits} prs={prs} issues={issues} repos={u['public_repos']} followers={u['followers']}")
