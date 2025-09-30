import pandas as pd
import argparse
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Input CSV")
    parser.add_argument("-n", "--num_points", type=int, default=5, help="Number of last points to use")
    parser.add_argument("--gradient_out", required=True, help="File to write gradient")
    parser.add_argument("--r2_out", required=True, help="File to write R² value")
    args = parser.parse_args()

    # Read CSV
    df = pd.read_csv(args.input, sep=",")

    # Take last N points
    last_points = df.tail(args.num_points)

    # Extract time and p_out_dynamic
    t = last_points["time"].values
    y = last_points["p_out_dynamic"].values

    # Fit a straight line: y = m*x + c
    coeffs = np.polyfit(t, y, 1)
    gradient = coeffs[0]

    # Compute R²
    y_pred = np.polyval(coeffs, t)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    # Write outputs separately
    with open(args.gradient_out, "w") as f:
        f.write(str(gradient))

    with open(args.r2_out, "w") as f:
        f.write(str(r2))


if __name__ == "__main__":
    main()
