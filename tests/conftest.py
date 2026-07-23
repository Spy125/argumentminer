"""Make the package importable during tests.

argumentminer is run with `python -m` rather than installed, so the repository
root must be on sys.path for `import argumentminer` to resolve when pytest is
invoked from anywhere.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
