#!/usr/bin/env python3"""
MoveGuide Validator
Checks all generated pages for quality issues.
Usage: python validate.py
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / "public"

MIN_FILE_SIZE = 8000  # bytes — a proper page should be at least 8kb
REQUIRED_SECTIONS = ["worth-it", "visa", "before", "arrival", "first-month", "money", "work", "life"]

passed = []
failed = []

html_files = list(PUBLIC_DIR.rglob("moving-from-*.html"))
print(f"\n🔍 Validating {len(html_files)} pages...\n")

for path in html_files:
    errors = []

    # Check file size
    size = path.stat().st_size
    if size < MIN_FILE_SIZE:
        errors.append(f"Too small ({size} bytes)")

    # Check required sections
    content = path.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        if f'id="{section}"' not in content:
            errors.append(f"Missing section: {section}")

    # Check has image
    if 'unsplash.com' not in content:
        errors.append("No Unsplash image")

    # Check has title
    if '<title>' not in content:
        errors.append("Missing title tag")

    name = path.name
    if errors:
        print(f"❌ {name}")
        for e in errors:
            print(f"   → {e}")
        failed.append(path)
    else:
        passed.append(path)

print(f"\n{'='*50}")
print(f"✅ Passed: {len(passed)}")
print(f"❌ Failed: {len(failed)}")

if failed:
    print(f"\nFailed pages:")
    for p in failed:
        print(f"  {p.relative_to(BASE_DIR)}")
