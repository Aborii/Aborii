#!/usr/bin/env python3
"""
Script to update README.md with resume data from personal-resume repository.
"""

import re
import json
import sys
from urllib.request import urlopen

RESUME_URL = "https://raw.githubusercontent.com/Aborii/personal-resume/main/data/resumeData.json"
README_PATH = "README.md"

def fetch_resume_summary():
    """Fetch and extract summary from resume JSON."""
    try:
        with urlopen(RESUME_URL) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Try multiple common field names for summary
        for field in ['summary', 'description', 'about', 'bio', 'profile', 'introduction']:
            if field in data and data[field]:
                return data[field].strip()
        
        print("Warning: No summary field found in resume data", file=sys.stderr)
        return None
        
    except Exception as e:
        print(f"Error fetching resume data: {e}", file=sys.stderr)
        sys.exit(1)

def update_readme(new_summary):
    """Update README.md with new summary."""
    if not new_summary:
        print("No summary to update")
        return False
    
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match the summary section
        # Between the subtitle and the image link
        pattern = r'(## Software Enginner[^\n]*\n\n)(.*?)(\n\n<a href="https://www\.abdullah-almofleh\.com/")'
        
        # Check if pattern matches
        if not re.search(pattern, content, flags=re.DOTALL):
            print("Error: Could not find summary section in README", file=sys.stderr)
            return False
        
        # Replace the summary
        updated_content = re.sub(pattern, rf'\1{new_summary}\3', content, flags=re.DOTALL)
        
        # Check if anything changed
        if updated_content == content:
            print("No changes needed - summary is already up to date")
            return False
        
        # Write back
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✓ README updated successfully")
        return True
        
    except Exception as e:
        print(f"Error updating README: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function."""
    print("Fetching resume data...")
    summary = fetch_resume_summary()
    
    print("Updating README...")
    changed = update_readme(summary)
    
    # Exit with code 0 if changed, 1 if no changes (for workflow control)
    sys.exit(0 if changed else 1)

if __name__ == "__main__":
    main()
