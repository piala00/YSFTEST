"""CI SQL Server: periodic Python stack dumps identify stalled test/DB calls."""
import faulthandler
import runpy
import sys


def main():
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path("manage.py", run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
