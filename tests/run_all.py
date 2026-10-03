from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
