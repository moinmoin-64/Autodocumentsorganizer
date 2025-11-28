#!/usr/bin/env python3
"""Script to find and fix unmatched docstrings in database.py"""

with open('app/database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_docstring = False
doc_start_line = None

for i, line in enumerate(lines, 1):
    if '"""' in line:
        if in_docstring:
            print(f"Closing docstring at line {i} (opened at {doc_start_line})")
            in_docstring = False
            doc_start_line = None
        else:
            print(f"Opening docstring at line {i}")
            in_docstring = True
            doc_start_line = i

if in_docstring:
    print(f"\n❌ PROBLEM: Unclosed docstring starting at line {doc_start_line}!")
    print(f"Line content: {lines[doc_start_line-1].strip()}")
else:
    print("\n✅ All docstrings properly closed")
