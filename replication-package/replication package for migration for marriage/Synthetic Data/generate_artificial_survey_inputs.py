"""Generate artificial survey-shaped files for software checks, not research."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def save(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_stata(path, write_index=False, version=118)
    frame.to_csv(path.with_suffix(".csv"), index=False)
    print(f"Created artificial inputs: {path} and {path.with_suffix('.csv')}")


def main() -> None:
    rng = np.random.default_rng(20261119)
    n = 12000
    india = pd.DataFrame(
        {
            "hv005": rng.uniform(0.5, 1.5, n),
            "hv104": rng.integers(1, 3, n, dtype=np.int16),
            "hv105": rng.integers(18, 75, n, dtype=np.int16),
            "hv106": rng.integers(0, 4, n, dtype=np.int16),
            "sh54": rng.integers(1, 3, n, dtype=np.int16),
        }
    )
    india["hv104"] = india["sh54"]
    save(india, ROOT / "DHS India" / "IAPR42FL synthetic.dta")

    n = 20000
    ipums = pd.DataFrame(
        {
            "sample": rng.choice([586199801, 50200101], n).astype(np.int32),
            "sex": rng.integers(1, 3, n, dtype=np.int16),
            "age": rng.integers(23, 55, n, dtype=np.int16),
            "edattain": rng.integers(1, 5, n, dtype=np.int16),
            "perwt": rng.uniform(0.5, 1.5, n),
        }
    )
    save(ipums, ROOT / "IPUMS" / "ipumsi synthetic.dta")


if __name__ == "__main__":
    main()
