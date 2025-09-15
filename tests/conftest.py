import sys
from pathlib import Path


# Ensure project root is on sys.path so `import src...` works in tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_str = str(PROJECT_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


