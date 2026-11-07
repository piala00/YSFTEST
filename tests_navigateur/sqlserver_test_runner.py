"""SQL Server CI runner: per-test timing and periodic stack diagnostics.

The duration log is flushed immediately so a global timeout still leaves the
name and elapsed time of the last unfinished test in GitHub Actions logs.
"""
import hashlib
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


def partition_suite():
    """Partition stable par test, sans omettre les tests imbriqués Django."""
    shard = int(os.environ.get("SQL_TEST_SHARD", "0"))
    count = int(os.environ.get("SQL_TEST_SHARDS", "1"))
    if count < 1 or not 0 <= shard < count:
        raise ValueError("SQL_TEST_SHARD/SQL_TEST_SHARDS invalides")
    if count == 1:
        return
    from django.test.runner import DiscoverRunner
    original_build = DiscoverRunner.build_suite

    def build_partition(self, *args, **kwargs):
        suite = original_build(self, *args, **kwargs)
        def walk(node):
            for child in node:
                if isinstance(child, unittest.TestSuite):
                    yield from walk(child)
                else:
                    yield child
        selected = [test for test in walk(suite)
                    if int.from_bytes(hashlib.sha256(test.id().encode()).digest()[:8], "big") % count == shard]
        print(f"[SQL-SHARD] {shard + 1}/{count}: {len(selected)} tests", flush=True)
        return unittest.TestSuite(selected)
    DiscoverRunner.build_suite = build_partition


def main():
    repository_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository_root))
    os.chdir(repository_root)
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    instrument_tests()
    partition_suite()
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
