import os
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT_DIR = r"/Users/skyla/Downloads/midi"
SURPRISE_ROOT = os.path.join(ROOT_DIR, "_surprise")

PLOTS_ROOT = os.path.join(ROOT_DIR, "_plots")


def find_surprise_files():
    """
    Walk SURPRISE_ROOT and yield (style, full_path) for each *.surprise.txt file.
    'style' = top-level subfolder name (e.g. 'pop', 'classical', etc.).
    """
    for dirpath, _, filenames in os.walk(SURPRISE_ROOT):
        for fn in filenames:
            if fn.endswith(".surprise.txt"):
                full_path = os.path.join(dirpath, fn)
                # style is the first folder under _surprise
                rel = os.path.relpath(dirpath, SURPRISE_ROOT)
                style = rel.split(os.sep)[0] if rel != "." else "ROOT"
                yield style, full_path


def load_all_surprises():
    """
    Load all .surprise.txt files into a dict
    """
    style_to_dfs = defaultdict(list)

    for style, path in find_surprise_files():
        try:
            df = pd.read_csv(path, sep="\t")
        except Exception as e:
            print(f"[warn] Could not read {path}: {e}")
            continue

        if "surprise_bits" not in df.columns:
            print(f"[warn] File {path} missing 'surprise_bits' column, skipping.")
            continue

        df["file"] = os.path.basename(path)
        style_to_dfs[style].append(df)

    style_to_data = {}
    for style, dfs in style_to_dfs.items():
        if not dfs:
            continue
        style_to_data[style] = pd.concat(dfs, ignore_index=True)

    return style_to_data


def summarize_styles(style_to_data):
    """
    Print and return summary stats (mean, variance, count) for each style.
    """
    summary_rows = []

    print("\n=== Summary statistics by style ===")
    for style, df in style_to_data.items():
        mean_s = df["surprise_bits"].mean()
        var_s = df["surprise_bits"].var()
        n = len(df)

        summary_rows.append(
            {"style": style, "mean_surprise": mean_s, "variance": var_s, "n_notes": n}
        )

        print(
            f"- {style:15s} | "
            f"mean surprise = {mean_s:.3f} bits, "
            f"var = {var_s:.3f}, "
            f"n = {n}"
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(SURPRISE_ROOT, "style_surprise_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSaved summary CSV to: {summary_csv}")

    return summary_df


def plot_histograms(style_to_data, bins=50):
    """
    Plot a histogram of surprise_bits for each style and save as PNG.
    """
    os.makedirs(PLOTS_ROOT, exist_ok=True)

    print("\n=== Plotting histograms ===")
    for style, df in style_to_data.items():
        plt.figure()
        df["surprise_bits"].hist(bins=bins)
        plt.title(f"Surprise distribution ({style})")
        plt.xlabel("Surprise (bits)")
        plt.ylabel("Count")
        plt.tight_layout()

        out_path = os.path.join(PLOTS_ROOT, f"{style}_surprise_hist.png")
        plt.savefig(out_path)
        plt.close()
        print(f"- Saved histogram for style '{style}' -> {out_path}")


def pick_example_file(df):
    """
    Pick one 'representative' file from a style DataFrame.
    """
    counts = df.groupby("file")["surprise_bits"].count()
    # file with max count
    if len(counts) == 0:
        return None
    return counts.idxmax()


def plot_example_curve_per_style(style_to_data):
    """
    For each style, pick one file and plot surprise vs index.
    """
    os.makedirs(PLOTS_ROOT, exist_ok=True)

    print("\n=== Plotting example surprise curves (one file per style) ===")
    for style, df in style_to_data.items():
        file_name = pick_example_file(df)
        if file_name is None:
            print(f"- No data for style '{style}', skipping example curve.")
            continue

        sub = df[df["file"] == file_name].sort_values("index")

        plt.figure()
        plt.plot(sub["index"], sub["surprise_bits"])
        plt.title(f"Surprise vs. note index\nStyle: {style}, File: {file_name}")
        plt.xlabel("Note index")
        plt.ylabel("Surprise (bits)")
        plt.tight_layout()

        out_path = os.path.join(PLOTS_ROOT, f"{style}_{file_name}_curve.png")
        # sanitize filename a bit (remove spaces just in case)
        out_path = out_path.replace(" ", "_")
        plt.savefig(out_path)
        plt.close()
        print(f"- Saved curve for style '{style}' file '{file_name}' -> {out_path}")


def main():
    if not os.path.isdir(SURPRISE_ROOT):
        print(f"[error] SURPRISE_ROOT does not exist: {SURPRISE_ROOT}")
        return

    style_to_data = load_all_surprises()
    if not style_to_data:
        print("[error] No surprise data found.")
        return

    summarize_styles(style_to_data)
    plot_histograms(style_to_data, bins=50)
    plot_example_curve_per_style(style_to_data)

    print("\nDone. Check the _surprise and _plots folders for results.")


if __name__ == "__main__":
    main()
