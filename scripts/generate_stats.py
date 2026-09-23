#!/usr/bin/env python3
"""Generate a dependency-free SVG summary from GitHub's public REST API."""

from __future__ import annotations

import argparse
import html
import json
import os
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen


API = "https://api.github.com"
COLORS = ["#7dd3fc", "#a78bfa", "#34d399", "#fbbf24", "#fb7185"]


def github_json(path: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-stats-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"{API}{path}", headers=headers), timeout=30) as response:
        return json.load(response)


def render(username: str) -> str:
    user = github_json(f"/users/{username}")
    repos = github_json(f"/users/{username}/repos?type=owner&sort=updated&per_page=100")
    if not isinstance(user, dict) or not isinstance(repos, list):
        raise RuntimeError("Unexpected GitHub API response")

    projects = [repo for repo in repos if repo.get("name") != username]
    languages = Counter(repo.get("language") for repo in projects if repo.get("language"))
    top_languages = languages.most_common(5)
    total_language_repos = max(sum(count for _, count in top_languages), 1)
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in projects)

    bars = []
    labels = []
    x = 665
    total_width = 455
    for index, (language, count) in enumerate(top_languages):
        width = round(total_width * count / total_language_repos, 1)
        bars.append(
            f'<rect x="{x:.1f}" y="103" width="{width:.1f}" height="13" '
            f'fill="{COLORS[index]}" rx="6"/>'
        )
        x += width
        label_x = 665 + (index % 3) * 160
        label_y = 151 + (index // 3) * 28
        labels.append(
            f'<circle cx="{label_x}" cy="{label_y - 4}" r="4" fill="{COLORS[index]}"/>'
            f'<text x="{label_x + 12}" y="{label_y}" class="small">'
            f'{html.escape(str(language))} · {count}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="230" viewBox="0 0 1200 230" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(username)} GitHub signal</title>
  <desc id="desc">Public project, follower, star, and language statistics generated from the GitHub API.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#111827"/>
    </linearGradient>
    <style>
      .label {{ fill:#64748b;font:600 11px 'Segoe UI',Arial,sans-serif;letter-spacing:1.5px }}
      .value {{ fill:#e2e8f0;font:700 32px 'Segoe UI',Arial,sans-serif }}
      .small {{ fill:#94a3b8;font:12px 'Segoe UI',Arial,sans-serif }}
    </style>
  </defs>
  <rect x="1" y="1" width="1198" height="228" rx="18" fill="url(#bg)" stroke="#263244"/>
  <text x="38" y="40" fill="#7dd3fc" font-family="Consolas,monospace" font-size="12" letter-spacing="2">GITHUB://PUBLIC-SIGNAL</text>
  <line x1="38" y1="58" x2="1162" y2="58" stroke="#263244"/>
  <g transform="translate(38 82)">
    <text class="label">PUBLIC PROJECTS</text><text y="45" class="value">{len(projects)}</text>
  </g>
  <g transform="translate(225 82)">
    <text class="label">FOLLOWERS</text><text y="45" class="value">{int(user.get('followers', 0))}</text>
  </g>
  <g transform="translate(385 82)">
    <text class="label">STARS EARNED</text><text y="45" class="value">{stars}</text>
  </g>
  <g transform="translate(535 82)">
    <text class="label">LANGUAGES</text><text y="45" class="value">{len(languages)}</text>
  </g>
  <text x="665" y="89" class="label">PUBLIC REPOSITORY LANGUAGE MIX</text>
  <rect x="665" y="103" width="455" height="13" fill="#1f2937" rx="6"/>
  {''.join(bars)}
  {''.join(labels)}
  <text x="38" y="199" fill="#475569" font-family="Consolas,monospace" font-size="11">generated from api.github.com · public repositories only</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.username), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
