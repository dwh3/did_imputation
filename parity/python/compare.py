from pathlib import Path

import pandas as pd


def compare(
    stata_csv: str,
    py_csv: str,
    label: str,
    tol_est: float = 0.05,
    tol_se: float = 0.05,
) -> str:
    stata = pd.read_csv(stata_csv).rename(columns=str.lower)
    python = pd.read_csv(py_csv).rename(columns=str.lower)

    required = {"k", "estimate"}
    if not required.issubset(stata.columns) or not required.issubset(python.columns):
        return f"### {label}\n- Missing required columns in one of the outputs.\n"

    merged = pd.merge(python, stata, on="k", how="inner", suffixes=("_py", "_stata"))
    if merged.empty:
        return f"### {label}\n- No overlapping k values.\n"

    merged["diff_est"] = (merged["estimate_py"] - merged["estimate_stata"]).abs()
    lines = [
        f"### {label}",
        f"- Rows compared: {len(merged)}",
        f"- Share(|delta estimate| <= {tol_est}): "
        f"{float((merged['diff_est'] <= tol_est).mean()):.2f}",
        f"- Max |delta estimate|: {merged['diff_est'].max():.4f}",
    ]

    if {"se_py", "se_stata"}.issubset(merged.columns):
        merged["diff_se"] = (merged["se_py"] - merged["se_stata"]).abs()
        share_se = float((merged["diff_se"] <= tol_se).mean())
        lines.insert(3, f"- Share(|delta se| <= {tol_se}): {share_se:.2f}")

    return "\n".join(lines)


def main() -> None:
    out_dir = Path("parity/out")
    report = ["# Python vs Stata Parity Report", ""]
    cases = [
        ("dgpA_no_treat", -3, 5, "nobs"),
        ("dgpB_const_te", 0, 3, "nobs"),
        ("dgpB_const_te", 0, 3, "equal"),
        ("dgpB_const_te", 0, 3, "cohort_share"),
        ("dgpC_pretrend", -3, 0, "nobs"),
    ]

    for name, kmin, kmax, scheme in cases:
        stata_csv = out_dir / f"{name}_stata_{scheme}_{kmin}_{kmax}.csv"
        python_csv = out_dir / f"{name}_py_{scheme}_{kmin}_{kmax}.csv"
        report.append(
            compare(
                str(stata_csv),
                str(python_csv),
                f"{name} | scheme={scheme} | {kmin}:{kmax}",
            )
        )
        report.append("")

    (out_dir / "PARITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print("Wrote parity/out/PARITY_REPORT.md")


if __name__ == "__main__":
    main()
