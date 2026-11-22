"""Marriage-migration decomposition for the three Table A8 age thresholds.

Average women's and men's original and restricted model rates before scaling
the pooled observed rate, using the same calculation as Table A7.
"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd

def load_a7_helper():
    source = Path(__file__).with_name("table_a7_migration.py")
    spec = spec_from_file_location("table_a7_migration", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Table A7 helper from {source}.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for threshold in (16, 18, 20):
        parser.add_argument(f"--dir{threshold}", required=True)
        parser.add_argument(
            f"--observed{threshold}", type=float, nargs=2, required=True,
            metavar=("NON_MUSLIM", "MUSLIM"),
            help=f"Pooled observed percentages for age threshold {threshold}.",
        )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    for threshold in (16, 18, 20):
        if any(not 0 <= rate <= 100 for rate in getattr(args, f"observed{threshold}")):
            parser.error("Observed migration percentages must be between 0 and 100.")

    helper = load_a7_helper()
    figure4 = helper.load_figure4()
    rates = pd.concat(
        [
            helper.decompose_pooled(
                figure4,
                getattr(args, f"dir{threshold}"),
                f"t{threshold}",
                dict(zip(("Non-Muslim", "Muslim"), getattr(args, f"observed{threshold}"))),
            )
            for threshold in (16, 18, 20)
        ],
        ignore_index=True,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    rates.to_csv(args.output, index=False)
    print(rates.to_string(index=False))


if __name__ == "__main__":
    main()
