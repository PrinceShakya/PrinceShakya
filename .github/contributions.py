"""Draw the last year's contributions as contributions.svg, in the header's colours.

Run by .github/workflows/contributions.yml. Without GITHUB_TOKEN it draws
made-up data so the design can be previewed locally.
"""
import datetime as dt
import json
import os
import random
import urllib.request

LOGIN = "PrinceShakya"
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""

BG, PANEL, RULE = "#0F2A33", "#0A1F26", "#1E3E48"
LEVELS = ["#163A44", "#1F5A4C", "#2A8166", "#3FB68B", "#8FD6B9"]
SANS = "-apple-system, 'Segoe UI', 'Helvetica Neue', Roboto, Arial, sans-serif"
CELL, GAP = 14, 4
STEP = CELL + GAP


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body,
                                 headers={"Authorization": f"bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def sample():
    rnd = random.Random(7)
    end = dt.date.today()
    days = [((end - dt.timedelta(days=i)).isoformat(), rnd.choice([0, 0, 1, 2, 3, 5, 8, 13]))
            for i in range(364, -1, -1)]
    return sum(c for _, c in days), days


def render(total, days):
    first = dt.date.fromisoformat(days[0][0])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday on or before first day
    top = max(c for _, c in days) or 1
    weeks = (dt.date.fromisoformat(days[-1][0]) - start).days // 7 + 1
    x0 = (1200 - weeks * STEP + GAP) // 2
    y0 = 108

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" '
           f'role="img" aria-label="{total:,} contributions in the last year">',
           f'<rect width="1200" height="300" fill="{BG}"/>',
           f'<rect x="{x0 - 64}" y="28" width="{weeks * STEP + 88}" height="244" rx="10" fill="{PANEL}" stroke="{RULE}"/>',
           f'<g font-family="{SANS}">',
           f'<text x="{x0}" y="66" font-size="20" font-weight="700" fill="#FFFFFF">{total:,} contributions in the last year</text>']

    last_month, last_label_week = None, -9
    for date, count in days:
        d = dt.date.fromisoformat(date)
        week, row = (d - start).days // 7, (d.weekday() + 1) % 7
        if row == 0 and d.month != last_month:  # label the first week that starts in a new month
            if week - last_label_week < 3:  # too close: the newer month wins
                out.pop(last_label_at)
            last_label_at = len(out)
            out.append(f'<text x="{x0 + week * STEP}" y="{y0 - 10}" font-size="12" fill="#6F8C94">{d:%b}</text>')
            last_label_week = week
            last_month = d.month
        level = 0 if count == 0 else min(4, -(-4 * count // top))
        out.append(f'<rect class="day" x="{x0 + week * STEP}" y="{y0 + row * STEP}" width="{CELL}" height="{CELL}" '
                   f'rx="3" fill="{LEVELS[level]}"/>')

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{x0 - 12}" y="{y0 + row * STEP + 11}" font-size="12" fill="#6F8C94" text-anchor="end">{name}</text>')

    lx = x0 + weeks * STEP - GAP - 5 * STEP - 36
    ly = y0 + 7 * STEP + 18
    out.append(f'<text x="{lx - 8}" y="{ly + 11}" font-size="12" fill="#6F8C94" text-anchor="end">Less</text>')
    out += [f'<rect x="{lx + i * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS)]
    out.append(f'<text x="{lx + 5 * STEP + 4}" y="{ly + 11}" font-size="12" fill="#6F8C94">More</text>')
    out += ["</g>", "</svg>"]
    return "\n".join(out)


if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    total, days = fetch(token) if token else sample()
    svg = render(total, days)
    assert svg.count('class="day"') == len(days), "every day must get exactly one cell"
    with open("contributions.svg", "w") as f:
        f.write(svg)
    print(f"contributions.svg: {total} contributions over {len(days)} days")
