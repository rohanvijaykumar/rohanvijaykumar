"""Fill the "Recently shipped" list in README.md from my public repos' latest releases.

Runs weekly from .github/workflows/shipped.yml. Standard library only. Forks and the
profile repo are skipped, and only version tags count (v1.2.0, not internal build tags).
"""
import datetime, json, os, re, urllib.request

USER = os.environ.get("GH_USER", "rohanvijaykumar")
TOKEN = os.environ.get("GH_TOKEN")
LIMIT = 4
START, END = "<!-- SHIPPED:START -->", "<!-- SHIPPED:END -->"


def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def pretty(name):
    return name.replace("-", " ").title() if name.islower() else name


entries = []
for repo in api(f"users/{USER}/repos?per_page=100&type=owner&sort=pushed"):
    if repo["fork"] or repo["private"] or repo["name"].lower() == USER.lower():
        continue
    for rel in api(f"repos/{USER}/{repo['name']}/releases?per_page=10"):
        if rel["draft"] or rel["prerelease"] or not re.match(r"^v?\d+(\.\d+)*$", rel["tag_name"]):
            continue
        when = datetime.datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))
        entries.append((when, f"**[{pretty(repo['name'])} {rel['tag_name']}]({rel['html_url']})** · released {when:%b} {when.day}, {when.year}"))

entries.sort(reverse=True)
lines = [f"- {text}" for _, text in entries[:LIMIT]] or ["- New releases will show up here."]
block = f"{START}\n" + "\n".join(lines) + f"\n{END}"

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
updated = re.sub(re.escape(START) + r".*?" + re.escape(END), block, readme, flags=re.S)
if updated != readme:
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)
    print("README updated:\n" + "\n".join(lines))
else:
    print("No change.")
