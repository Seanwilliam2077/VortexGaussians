"""Use the registered serial T144 supervisor with the embedded-guard worker."""
import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    directory = parser.parse_args().out.resolve()
    source = next(HERE.parent.glob("t144-*/supervise.py"))
    spec = importlib.util.spec_from_file_location("paired_bonsai_supervisor", source)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.HERE = HERE
    directory.mkdir(parents=True, exist_ok=False)
    for number in (1, 2):
        if not runner.one(directory, number):
            raise SystemExit(1)
