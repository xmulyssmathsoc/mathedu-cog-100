#!/usr/bin/env python3
"""Deterministically rebuild MathEdu-Cog 100 + 30 illustrative error cases."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
COMMANDS=[
 'build_db.py', 'math_checks.py','validate.py','make_browser.py',
 'build_error_cases.py','error_case_math_checks.py','validate_error_cases.py'
]
for filename in COMMANDS:
 print(f'===== {filename} =====',flush=True)
 subprocess.run([sys.executable,str(ROOT/'scripts'/filename)],cwd=ROOT,check=True)
print('MathEdu-Cog 100 v1.1 build and all validations completed.',flush=True)
