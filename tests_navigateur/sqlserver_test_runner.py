"""SQL Server CI runner: per-test timing and periodic stack diagnostics.

The duration log is flushed immediately so a global timeout still leaves the
name and elapsed time of the last unfinished test in GitHub Actions logs.
"""
import faulthandler
import os
from pathlib import Path
import runpy
import sys
import time
import unittest


def instrument_tests():
    original_run = unittest.TestCase.run
    threshold = float(os.environ.get("SQL_TEST_SLOW_SECONDS", "15"))

    def timed_run(self, result=None):
        test_name = self.id()
        started = time.monotonic()
        print(f"[SQL-TEST-START] {test_name}", flush=True)
        try:
            return original_run(self, result)
        finally:
            elapsed = time.monotonic() - started
            marker = "SLOW" if elapsed >= threshold else "END"
            print(f"[SQL-TEST-{marker}] {elapsed:.3f}s {test_name}", flush=True)

    unittest.TestCase.run = timed_run


def main():
    repository_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository_root))
    os.chdir(repository_root)
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    instrument_tests()
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
