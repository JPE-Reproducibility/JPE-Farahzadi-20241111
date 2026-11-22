"""Produce Table A5 using observed and simulated matching moments.

Run Table A5 observed.do first, using the same sample as the model files.
"""

import argparse
from pathlib import Path
import warnings

import numpy as np
import numpy.matlib
import pandas as pd


ETHNICITIES = ["White British", "Other White", "Indian", "Pakistani/Bangladeshi", "Other"]
ROWS = (
    [("Inter-education", label) for label in ("Low-educated", "High-educated")]
    + [("Inter-ethnic", label) for label in ETHNICITIES]
    + [("Inter-religious", "All")]
    + [("Marriage Migration", label) for label in ETHNICITIES[1:]]
    + [("Single", "All")]
)


def IPFP(phi, nx, ny, ncat_x, ncat_y, tol, maxiter, dxy, dyx):
    ephi2 = np.exp(phi / 2)
    bigc = np.sqrt(1 / (ncat_x + ncat_y + 2 * np.sum(ephi2)))
    txi = np.repeat(np.asmatrix("1"), ncat_x, axis=0) * bigc
    tyi = np.repeat(np.asmatrix("1"), ncat_x, axis=0) * bigc
    err_diff = bigc
    tol_diff = tol * bigc
    niter = 0

    while (err_diff > tol_diff) & (niter < maxiter):
        Sx = np.sum(np.multiply(ephi2, np.transpose(tyi)) + np.multiply(ephi2, dxy), axis=1)
        tx = (np.sqrt(np.multiply(Sx, Sx) + 4 * np.transpose(nx)) - Sx) / 2
        Sy = np.transpose(np.sum(np.multiply(ephi2, tx) + np.multiply(ephi2, dyx), axis=0))
        ty = (np.sqrt(np.multiply(Sy, Sy) + 4 * np.transpose(ny)) - Sy) / 2
        err_diff = np.max(np.abs(tx - txi)) + np.max(np.abs(ty - tyi))
        txi = tx
        tyi = ty
        niter = niter + 1

    if err_diff > tol_diff:
        raise RuntimeError(f"IPFP did not converge in {maxiter} iterations.")
    mux0 = np.multiply(txi, txi)
    mu0y = np.multiply(tyi, tyi)
    muxy = np.multiply(ephi2, np.multiply(
        np.matlib.repmat(txi, 1, ncat_y),
        np.matlib.repmat(np.transpose(tyi), ncat_x, 1),
    ))
    with np.errstate(divide="ignore", invalid="ignore"):
        lxy = np.divide(np.multiply(muxy, dxy), np.transpose(tyi))
        lyx = np.divide(np.multiply(muxy, dyx), txi)
    return muxy, mux0, mu0y, lxy, lyx


def simulated_moments(model_dir):
    age = np.array([1, 2, 3])[np.newaxis]
    ethnicity = np.array([0, 1, 2, 3, 4])[np.newaxis]
    religion = np.array([0, 1])[np.newaxis]
    education = np.array([0, 1])[np.newaxis]
    c1 = np.repeat(age, ethnicity.shape[1] * education.shape[1] * religion.shape[1], axis=1)
    c2 = np.matlib.repmat(np.repeat(ethnicity, education.shape[1] * religion.shape[1]), 1, age.shape[1])
    c3 = np.matlib.repmat(np.repeat(religion, education.shape[1]), 1, age.shape[1] * ethnicity.shape[1])
    c4 = np.matlib.repmat(education, 1, age.shape[1] * ethnicity.shape[1] * religion.shape[1])
    ncat_x = c1.shape[1]
    ncat_y = c1.shape[1]

    xx1 = np.transpose(np.repeat(c1, ncat_y, 1))
    xx2 = np.transpose(np.repeat(c2, ncat_y, 1))
    xx3 = np.transpose(np.repeat(c3, ncat_y, 1))
    xx4 = np.transpose(np.repeat(c4, ncat_y, 1))
    yy1 = np.matlib.repmat(np.transpose(c1), ncat_x, 1)
    yy2 = np.matlib.repmat(np.transpose(c2), ncat_x, 1)
    yy3 = np.matlib.repmat(np.transpose(c3), ncat_x, 1)
    yy4 = np.matlib.repmat(np.transpose(c4), ncat_x, 1)
    group_x = xx1 * 1000 + xx2 * 100 + xx3 * 10 + xx4
    group_y = yy1 * 1000 + yy2 * 100 + yy3 * 10 + yy4
    group = c1 * 1000 + c2 * 100 + c3 * 10 + c4

    dis = pd.read_stata(model_dir / "dist.dta")
    if "group" in dis.columns and not np.array_equal(dis["group"].to_numpy(), group.ravel()):
        raise ValueError("dist.dta groups must be in the original age/ethnicity/religion/education order.")
    if len(dis) != ncat_x:
        raise ValueError("dist.dta must contain the 60 original model groups.")
    nx = np.array(dis.nx)[np.newaxis]
    ny = np.array(dis.ny)[np.newaxis]
    if not np.isfinite(nx).all() or not np.isfinite(ny).all() or (nx < 0).any() or (ny < 0).any():
        raise ValueError("dist.dta contains missing, non-finite or negative population counts.")

    def read_matrix(filename, column):
        frame = pd.read_stata(model_dir / filename).sort_values(by=["groupx", "groupy"])
        matrix = pd.pivot(frame[["groupx", "groupy", column]], columns="groupy", values=column, index="groupx")
        if not np.array_equal(matrix.index.to_numpy(), group.ravel()) or not np.array_equal(matrix.columns.to_numpy(), group.ravel()):
            raise ValueError(f"{filename} does not contain the 60 original model groups.")
        values = matrix.to_numpy()
        if not np.isfinite(values).all() or (column != "phi" and (values < 0).any()):
            raise ValueError(f"{filename} contains invalid {column} values.")
        return values

    phi = read_matrix("phi.dta", "phi")
    dxy = read_matrix("d.dta", "D_women")
    dyx = read_matrix("d.dta", "D_men")
    muxy, mux0, mu0y, lxy, lyx = IPFP(phi, nx, ny, ncat_x, ncat_y, 1e-9, 1000, dxy, dyx)
    if not all(np.isfinite(value).all() for value in (muxy, mux0, mu0y, lxy, lyx)):
        raise ValueError("The original IPFP produced non-finite matching masses; check for zero-population groups.")

    df = pd.DataFrame(
        np.concatenate((group_x, group_y, xx1, xx2, xx3, xx4, yy1, yy2, yy3, yy4), axis=1),
        columns=["groupx", "groupy", "ax", "ex", "rx", "sx", "ay", "ey", "ry", "sy"],
    ).sort_values(by=["groupx", "groupy"])
    df["muxy"] = muxy.reshape(ncat_x * ncat_y, 1)
    df["lxy"] = lxy.reshape(ncat_x * ncat_y, 1)
    df["lyx"] = lyx.reshape(ncat_x * ncat_y, 1)
    for mass in ("muxy", "lxy", "lyx"):
        for suffix, x, y in (("intereth", "ex", "ey"), ("interrel", "rx", "ry"), ("interedu", "sx", "sy")):
            df[f"{mass}_{suffix}"] = df[mass]
            df.loc[df[x] == df[y], f"{mass}_{suffix}"] = 0

    df_m = pd.DataFrame(
        np.concatenate((np.transpose(group), np.transpose(c1), np.transpose(c2),
                        np.transpose(c3), np.transpose(c4), mux0, mu0y), axis=1),
        columns=["group", "a", "e", "r", "s", "mux0", "mu0y"],
    ).set_index("group")
    df_m["mx"] = df.groupby("groupx")["muxy"].sum()
    df_m["my"] = df.groupby("groupy")["muxy"].sum()
    df_m["lx"] = df.groupby("groupx")["lxy"].sum()
    df_m["ly"] = df.groupby("groupy")["lyx"].sum()
    df_m["nx"] = np.transpose(nx)
    df_m["ny"] = np.transpose(ny)

    inter_edu0 = (
        (df.groupby(["rx", "sx"])["muxy_interedu"].sum() + df.groupby(["rx", "sx"])["lxy_interedu"].sum())
        / (df.groupby(["rx", "sx"])["muxy"].sum() + df.groupby(["rx", "sx"])["lxy"].sum())
        + (df.groupby(["ry", "sy"])["muxy_interedu"].sum() + df.groupby(["ry", "sy"])["lyx_interedu"].sum())
        / (df.groupby(["ry", "sy"])["muxy"].sum() + df.groupby(["ry", "sy"])["lyx"].sum())
    ) / 2
    inter_eth0 = (
        (df.groupby(["rx", "ex"])["muxy_intereth"].sum() + df.groupby(["rx", "ex"])["lxy_intereth"].sum())
        / (df.groupby(["rx", "ex"])["muxy"].sum() + df.groupby(["rx", "ex"])["lxy"].sum())
        + (df.groupby(["ry", "ey"])["muxy_intereth"].sum() + df.groupby(["ry", "ey"])["lyx_intereth"].sum())
        / (df.groupby(["ry", "ey"])["muxy"].sum() + df.groupby(["ry", "ey"])["lyx"].sum())
    ) / 2
    inter_rel0 = (
        (df.groupby("rx")["muxy_interrel"].sum() + df.groupby("rx")["lxy_interrel"].sum())
        / (df.groupby("rx")["muxy"].sum() + df.groupby("rx")["lxy"].sum())
        + (df.groupby("ry")["muxy_interrel"].sum() + df.groupby("ry")["lyx_interrel"].sum())
        / (df.groupby("ry")["muxy"].sum() + df.groupby("ry")["lyx"].sum())
    ) / 2
    marriage_migration0 = (
        df_m.groupby(["r", "e"])["lx"].sum()
        / (df_m.groupby(["r", "e"])["mx"].sum() + df_m.groupby(["r", "e"])["lx"].sum())
        + df_m.groupby(["r", "e"])["ly"].sum()
        / (df_m.groupby(["r", "e"])["my"].sum() + df_m.groupby(["r", "e"])["ly"].sum())
    ) / 2
    single0 = (
        df_m.groupby("r")["mux0"].sum() / df_m.groupby("r")["nx"].sum()
        + df_m.groupby("r")["mu0y"].sum() / df_m.groupby("r")["ny"].sum()
    ) / 2

    moments = {}
    for r in (0, 1):
        for s, label in enumerate(("Low-educated", "High-educated")):
            moments["Inter-education", label, r] = inter_edu0.get((r, s), np.nan)
        for e, label in enumerate(ETHNICITIES):
            moments["Inter-ethnic", label, r] = inter_eth0.get((r, e), np.nan)
            if e:
                moments["Marriage Migration", label, r] = marriage_migration0.get((r, e), np.nan)
        moments["Inter-religious", "All", r] = inter_rel0.get(r, np.nan)
        moments["Single", "All", r] = single0.get(r, np.nan)
    return moments


def observed_moments(directory):
    sources = (
        ("observed_inter_edu.dta", "Inter-education", "education_a5", ["Low-educated", "High-educated"], "inter_edu"),
        ("observed_inter_ethnic.dta", "Inter-ethnic", "ethnic_group", ETHNICITIES, "inter_ethnic"),
        ("observed_inter_relig.dta", "Inter-religious", None, ["All"], "inter_relig"),
        ("observed_migration.dta", "Marriage Migration", "ethnic_group", ETHNICITIES, "sadult_immig"),
        ("observed_single.dta", "Single", None, ["All"], "single"),
    )
    moments = {}
    for filename, measure, category, labels, value in sources:
        frame = pd.read_stata(directory / filename, convert_categoricals=False)
        keys = ["muslim"] + ([category] if category else [])
        if frame.duplicated(keys).any():
            raise ValueError(f"{filename} contains duplicate group combinations.")
        for _, row in frame.iterrows():
            religion = row["muslim"]
            if religion not in (0, 1):
                raise ValueError(f"{filename} contains an invalid religion group.")
            index = row[category] if category else 0
            if pd.isna(index) or index != int(index) or not 0 <= index < len(labels):
                raise ValueError(f"{filename} contains an invalid category.")
            v = row[value]
            if not pd.isna(v) and (not np.isfinite(v) or not 0 <= v <= 1):
                raise ValueError(f"{filename} contains an invalid {value} value.")
            moments[measure, labels[int(index)], int(religion)] = v
    return moments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", "--input-dir", dest="model_dir", type=Path, required=True, help="Directory containing dist.dta, phi.dta and d.dta.")
    parser.add_argument("--observed-dir", type=Path, required=True, help="Directory of Stata files from Table A5 observed.do.")
    parser.add_argument("--output", type=Path, required=True, help="Table A5 output CSV.")
    args = parser.parse_args()
    simulated = simulated_moments(args.model_dir)
    observed = observed_moments(args.observed_dir)
    rows = []
    for measure, group in ROWS:
        row = {"measure": measure, "group": group}
        for source, moments in (("observed", observed), ("simulated", simulated)):
            for religion, label in ((0, "non_muslim"), (1, "muslim")):
                value = moments.get((measure, group, religion), np.nan)
                if pd.isna(value):
                    warnings.warn(f"Undefined {source} outcome: {measure}, {group}, {label}")
                row[f"{source}_{label}_percent"] = value * 100
        rows.append(row)
    if not args.output.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {args.output.parent}")
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Table A5 saved to {args.output}")


if __name__ == "__main__":
    main()
