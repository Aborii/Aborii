#!/usr/bin/env python3
"""
Update README.md from the resume data in the personal-resume repository.

Every section this script owns is delimited by a marker pair, so the README can
be restyled freely as long as the markers survive.

Exit codes:
    0 - README was updated
    1 - no change needed, every section already matched
    2 - error, the sync did not run to completion
"""

import re
import json
import sys
from urllib.request import urlopen

RESUME_URL = "https://raw.githubusercontent.com/Aborii/personal-resume/main/data/resumeData.json"
README_PATH = "README.md"
FETCH_TIMEOUT = 30

EXIT_UPDATED = 0
EXIT_NO_CHANGE = 1
EXIT_ERROR = 2

# Badge colour and simple-icons slug per skill. A slug of None renders a plain
# text badge: shields.io drops unknown slugs silently and would otherwise leave
# a blank gap where the icon should be. Every Amazon slug and "playwright" were
# checked against shields.io and none returns an icon.
BADGES = {
    "TypeScript": ("3178C6", "typescript", "white"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "PHP": ("777BB4", "php", "white"),
    "Next.js": ("000000", "nextdotjs", "white"),
    "React.js": ("20232A", "react", "61DAFB"),
    "Vue.js": ("4FC08D", "vuedotjs", "white"),
    "Tailwind CSS": ("06B6D4", "tailwindcss", "white"),
    "Node.js": ("339933", "nodedotjs", "white"),
    "NestJS": ("E0234E", "nestjs", "white"),
    "Express.js": ("000000", "express", "white"),
    "Laravel": ("FF2D20", "laravel", "white"),
    "TypeORM": ("FE0902", None, "white"),
    "PostgreSQL": ("4169E1", "postgresql", "white"),
    "TimescaleDB": ("FDB515", "timescale", "black"),
    "MongoDB": ("47A248", "mongodb", "white"),
    "MySQL": ("4479A1", "mysql", "white"),
    "Redis": ("FF4438", "redis", "white"),
    "MQTT": ("660066", "mqtt", "white"),
    "AWS IoT Core": ("232F3E", None, "white"),
    "WebSockets": ("010101", "socketdotio", "white"),
    "REST": ("02569B", "fastapi", "white"),
    "GraphQL": ("E10098", "graphql", "white"),
    "AWS": ("232F3E", None, "white"),
    "Docker": ("2496ED", "docker", "white"),
    "GitHub Actions": ("2088FF", "githubactions", "white"),
    "GitHub Actions CI/CD": ("2088FF", "githubactions", "white"),
    "Sentry": ("362D59", "sentry", "white"),
    "Jest": ("C21325", "jest", "white"),
    "Cypress": ("69D3A7", "cypress", "black"),
    "Playwright": ("2EAD33", None, "white"),
    "Git": ("F05032", "git", "white"),
    "Agile": ("5C6BC0", None, "white"),
    "Scrum": ("5C6BC0", None, "white"),
}

DEFAULT_BADGE = ("5C6BC0", None, "white")


def fetch_resume():
    """Fetch the resume JSON."""
    try:
        with urlopen(RESUME_URL, timeout=FETCH_TIMEOUT) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching resume data: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)


def shorten(skill):
    """Drop the parenthetical experience note: 'React.js (6+ years)' -> 'React.js'."""
    return re.sub(r'\s*\([^)]*\)\s*$', '', skill).strip()


def badge(label):
    """Build a shields.io badge for one skill."""
    colour, logo, logo_colour = BADGES.get(label, DEFAULT_BADGE)
    text = label.replace('-', '--').replace('_', '__').replace(' ', '%20')
    url = f"https://img.shields.io/badge/{text}-{colour}?style=flat-square"
    if logo:
        url += f"&logo={logo}&logoColor={logo_colour}"
    return f"![{label}]({url})"


def build_summary(data):
    for field in ['summary', 'description', 'about', 'bio', 'profile', 'introduction']:
        if data.get(field):
            return data[field].strip()
    print("Error: No summary field found in resume data", file=sys.stderr)
    sys.exit(EXIT_ERROR)


def build_stack(data):
    """A row per skill category, badges in the second column."""
    skills = data.get('skills') or {}
    if not skills:
        print("Error: No skills found in resume data", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    rows = ["| Area | Tools |", "| --- | --- |"]
    for area, items in skills.items():
        badges = " ".join(badge(shorten(s)) for s in items)
        rows.append(f"| **{area}** | {badges} |")
    return "\n".join(rows)


def build_projects(data):
    """A row per project, linked where the resume gives a URL."""
    projects = data.get('projects') or []
    if not projects:
        print("Error: No projects found in resume data", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    rows = ["| Project | What it is | Built with |", "| --- | --- | --- |"]
    for p in projects:
        name = p.get('name', '').strip()
        label = f"**[{name}]({p['url']})**" if p.get('url') else f"**{name}**"
        what = (p.get('description') or '').strip() or '—'
        details = p.get('details') or []
        # The first detail line is the stack; the rest is prose.
        stack = details[0].strip() if details else '—'
        stack = re.sub(r'\s*,\s*', ' · ', stack)
        rows.append(f"| {label} | {what} | {stack} |")
    return "\n".join(rows)


def build_experience(data):
    """The career table plus the education line beneath it."""
    experience = data.get('experience') or []
    if not experience:
        print("Error: No experience found in resume data", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    rows = ["| Period | Role | Company |", "| --- | --- | --- |"]
    for job in experience:
        period = (job.get('period') or '').replace(' to ', ' — ').strip()
        title = (job.get('title') or '').strip()
        company = (job.get('company') or '').strip()
        location = (job.get('location') or '').strip()
        where = f"{company} · {location}" if location else company
        rows.append(f"| {period} | {title} | {where} |")

    table = "\n".join(rows)

    edu = data.get('education') or {}
    if edu:
        bits = [b for b in [edu.get('degree'), edu.get('school'), edu.get('location')] if b]
        line = ", ".join(bits)
        if edu.get('period'):
            line += f". {edu['period']}"
        if edu.get('gpa'):
            line += f", GPA {edu['gpa']}"
        table += f"\n\n**Education** — {line}."

    return table


def build_languages(data):
    """The single table cell listing spoken languages."""
    langs = data.get('languages') or {}
    if not langs:
        return "—"
    return ", ".join(f"{name} ({level.lower()})" for name, level in langs.items())


# Marker name -> builder. Each block is replaced between its START/END pair.
SECTIONS = {
    "SUMMARY": build_summary,
    "STACK": build_stack,
    "PROJECTS": build_projects,
    "EXPERIENCE": build_experience,
    "LANGUAGES": build_languages,
}


def replace_block(content, name, body):
    """Swap the text between one marker pair. Returns the new content.

    The newlines are optional so a block sitting on its own lines and an inline
    pair inside a table cell are both handled.
    """
    pattern = r'(<!-- ' + name + r':START -->\n?)(.*?)(\n?<!-- ' + name + r':END -->)'
    if not re.search(pattern, content, flags=re.DOTALL):
        print(f"Error: Could not find {name} markers in README", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    # A function replacement keeps backslashes in the resume text literal.
    return re.sub(pattern,
                  lambda m: m.group(1) + body + m.group(3),
                  content, count=1, flags=re.DOTALL)


def main():
    print("Fetching resume data...")
    data = fetch_resume()

    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            original = f.read()
    except Exception as e:
        print(f"Error reading README: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    print("Rendering sections...")
    updated = original
    for name, build in SECTIONS.items():
        updated = replace_block(updated, name, build(data))

    if updated == original:
        print("No changes needed - README already matches the resume")
        sys.exit(EXIT_NO_CHANGE)

    try:
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated)
    except Exception as e:
        print(f"Error writing README: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    changed = [n for n in SECTIONS
               if replace_block(original, n, SECTIONS[n](data)) != original]
    print("README updated. Sections changed: " + ", ".join(changed))
    sys.exit(EXIT_UPDATED)


if __name__ == "__main__":
    main()
