import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class PruebasCli(unittest.TestCase):
    def test_version(self):
        r = subprocess.run([sys.executable, "-m", "dockeeper", "--version"], cwd=RAIZ, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("dockeeper", r.stdout)


if __name__ == "__main__":
    unittest.main()
