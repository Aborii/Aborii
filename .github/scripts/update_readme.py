#!/usr/bin/env python3
"""
Script to update README.md with resume data from personal-resume repository.

Exit codes:
    0 - README was updated
    1 - no change needed, the summary already matched
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

def fetch_resume_summary():
    """Fetch and extract summary from resume JSON."""
    try:
        with urlopen(RESUME_URL, timeout=FETCH_TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Try multiple common field names for summary
        for field in ['summary', 'description', 'about', 'bio', 'profile', 'introduction']:
            if field in data and data[field]:
                return data[field].strip()

        print("Error: No summary field found in resume data", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    except Exception as e:
        print(f"Error fetching resume data: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

def update_readme(new_summary):
    """Update README.md with new summary."""
    if not new_summary:
        print("Error: No summary to update", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match the summary section
        # Between the subtitle and the image link
        pattern = r'(## Software Enginner[^\n]*\n\n)(.*?)(\n\n<a href="https://www\.abdullah-almofleh\.com/")'

        # Check if pattern matches
        if not re.search(pattern, content, flags=re.DOTALL):
            print("Error: Could not find summary section in README", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        # Replace the summary. A function replacement is used rather than a
        # template string so backslashes in the resume text stay literal.
        updated_content = re.sub(
            pattern,
            lambda m: m.group(1) + new_summary + m.group(3),
            content,
            count=1,
            flags=re.DOTALL,
        )

        # Check if anything changed
        if updated_content == content:
            print("No changes needed - summary is already up to date")
            return False

        # Write back
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print("README updated successfully")
        return True

    except Exception as e:
        print(f"Error updating README: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

def main():
    """Main function."""
    print("Fetching resume data...")
    summary = fetch_resume_summary()

    print("Updating README...")
    changed = update_readme(summary)

    sys.exit(EXIT_UPDATED if changed else EXIT_NO_CHANGE)

if __name__ == "__main__":
    main()
