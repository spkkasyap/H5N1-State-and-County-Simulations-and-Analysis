import os
import re
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

SEED_STATE = "Texas"
SEED_DAY = 28

FILE_PATTERN = re.compile(
    r"sir_edgelist_.*_dairy_network_(\d+).*_state\.network\.csv$"
)

OUTPUT_DIR = "outputs/summaries/"


# ---------------------------------------------------------
# Process one dairy network
# ---------------------------------------------------------
def process_dairy_network(dairy_id, files_info):

    # group files by parameter folder
    folder_groups = {}
    for folder, file_path, alpha, beta, gamma in files_info:
        folder_groups.setdefault(folder, []).append(
            (file_path, alpha, beta, gamma)
        )

    rows = []

    # GLOBAL accumulators across ALL parameter folders
    G_intro_days = {}
    G_intro_counts = {}
    G_second_intro_cumu = {}
    G_final_cumu = {}
    G_export_days = {}
    G_export_counts = {}

    for folder, file_list in folder_groups.items():

        # folder-level accumulators (≈10 runs)
        S_intro_days = {}
        S_intro_counts = {}
        S_second_intro_cumu = {}
        S_final_cumu = {}
        S_export_days = {}
        S_export_counts = {}

        folder_alpha = file_list[0][1]
        folder_beta = file_list[0][2]
        folder_gamma = file_list[0][3]

        for file_path, alpha, beta, gamma in file_list:

            df = pd.read_csv(file_path)
            if not {"head", "tail", "day"}.issubset(df.columns):
                continue

            df = df.sort_values("day").reset_index(drop=True)

            # enforce Texas seed
            if SEED_STATE not in df["tail"].values:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {
                                "head": [SEED_STATE],
                                "tail": [SEED_STATE],
                                "day": [SEED_DAY],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            else:
                df.loc[df["tail"] == SEED_STATE, "day"] = SEED_DAY

            df = df.sort_values("day").reset_index(drop=True)

            # ---------------- IMPORTS ----------------
            for state, sub in df.groupby("tail"):
                sub = sub.sort_values("day").reset_index(drop=True)

                intro_events = sub[sub["head"] != state]
                intro_days = [SEED_DAY] if state == SEED_STATE else []
                intro_days.extend(intro_events["day"].tolist())
                intro_days = sorted(intro_days)

                for D in (S_intro_days, G_intro_days):
                    D.setdefault(state, []).append(intro_days)

                for D in (S_intro_counts, G_intro_counts):
                    D.setdefault(state, []).append(len(intro_days))

                cumu = 0
                cumu_before_second = 0
                cutoff = intro_days[1] if len(intro_days) >= 2 else None

                for _, r in sub.iterrows():
                    if r["head"] == state and r["tail"] == state:
                        if cutoff is not None and r["day"] < cutoff:
                            cumu_before_second += 1
                        cumu += 1

                if len(intro_days) >= 2:
                    for D in (S_second_intro_cumu, G_second_intro_cumu):
                        D.setdefault(state, []).append(cumu_before_second)

                for D in (S_final_cumu, G_final_cumu):
                    D.setdefault(state, []).append(cumu)

            # ---------------- EXPORTS ----------------
            for state, sub in df.groupby("head"):
                export_events = sub[sub["tail"] != state]
                export_days = sorted(export_events["day"].tolist())

                for D in (S_export_days, G_export_days):
                    D.setdefault(state, []).append(export_days)

                for D in (S_export_counts, G_export_counts):
                    D.setdefault(state, []).append(len(export_days))

        # ---------- BUILD PER-FOLDER ROWS ----------
        rows.extend(
            build_rows(
                folder_alpha,
                folder_beta,
                folder_gamma,
                S_intro_days,
                S_intro_counts,
                S_second_intro_cumu,
                S_final_cumu,
                S_export_days,
                S_export_counts,
            )
        )

    # ---------- BUILD ALL-PARAMETER ROWS ----------
    rows.extend(
        build_rows(
            "ALL",
            "ALL",
            "ALL",
            G_intro_days,
            G_intro_counts,
            G_second_intro_cumu,
            G_final_cumu,
            G_export_days,
            G_export_counts,
        )
    )

    summary_df = pd.DataFrame(rows).sort_values(
        ["mean_first_intro_day", "mean_total_cumu_cases"]
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(
        OUTPUT_DIR, f"dairy_network_import_summary_{dairy_id}.csv"
    )
    summary_df.to_csv(outpath, index=False)

    return dairy_id, outpath


# ---------------------------------------------------------
# Helper: build summary rows
# ---------------------------------------------------------
def build_rows(alpha, beta, gamma,
               intro_days, intro_counts,
               second_intro_cumu, final_cumu,
               export_days, export_counts):

    rows = []

    for state in intro_days.keys():

        intro_lists = intro_days[state]
        counts = intro_counts[state]
        final_cases = final_cumu[state]

        first_days = [lst[0] for lst in intro_lists]

        row = {
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "state": state,

            "mean_first_intro_day": np.mean(first_days),
            "earliest_first_intro_day": np.min(first_days),
            "latest_first_intro_day": np.max(first_days),
            "median_first_intro_day": np.median(first_days),

            "mean_intro_count": np.mean(counts),
            "median_intro_count": np.median(counts),
            "max_intro_count": np.max(counts),
        }

        if state in second_intro_cumu:
            row["mean_cumu_before_second_intro"] = np.mean(
                second_intro_cumu[state]
            )
            row["max_cumu_before_second_intro"] = np.max(
                second_intro_cumu[state]
            )
        else:
            row["mean_cumu_before_second_intro"] = np.nan
            row["max_cumu_before_second_intro"] = np.nan

        # only 2nd and 3rd introductions
        for k in [1, 2]:
            vals = [lst[k] for lst in intro_lists if len(lst) > k]
            row[f"mean_intro_day_{k+1}"] = np.mean(vals) if vals else np.nan
            row[f"median_intro_day_{k+1}"] = np.median(vals) if vals else np.nan

        if state in export_days:
            first_exports = [lst[0] for lst in export_days[state] if lst]
            row["mean_first_export_day"] = (
                np.mean(first_exports) if first_exports else np.nan
            )
            row["median_first_export_day"] = (
                np.median(first_exports) if first_exports else np.nan
            )
            row["mean_export_count"] = np.mean(export_counts[state])
            row["median_export_count"] = np.median(export_counts[state])
            row["max_export_count"] = np.max(export_counts[state])
        else:
            row["mean_first_export_day"] = np.nan
            row["median_first_export_day"] = np.nan
            row["mean_export_count"] = 0
            row["median_export_count"] = 0
            row["max_export_count"] = 0

        # cumulative cases LAST
        row["mean_total_cumu_cases"] = np.mean(final_cases)
        row["max_total_cumu_cases"] = np.max(final_cases)

        rows.append(row)

    return rows


# ---------------------------------------------------------
# Build file index
# ---------------------------------------------------------
def build_dairy_file_index(base_dir):

    result = {}

    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        alpha = beta = gamma = np.nan
        if m := re.search(r"_alpha([0-9.]+)", folder):
            alpha = float(m.group(1))
        if m := re.search(r"_beta([0-9.]+)", folder):
            beta = float(m.group(1))
        if m := re.search(r"_gamma_([0-9.]+)", folder):
            gamma = float(m.group(1))

        for fname in os.listdir(folder_path):
            match = FILE_PATTERN.match(fname)
            if not match:
                continue

            dairy_id = int(match.group(1))
            fpath = os.path.join(folder_path, fname)

            result.setdefault(dairy_id, []).append(
                (folder, fpath, alpha, beta, gamma)
            )

    return result


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":

    BASE_DIR = "outputs/simulations/"
    print(f"\nProcessing simulation folders in: {BASE_DIR}\n")

    dairy_network_files = build_dairy_file_index(BASE_DIR)

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(process_dairy_network, did, info)
            for did, info in dairy_network_files.items()
        ]

        for f in as_completed(futures):
            did, out = f.result()
            print(f"✔ Completed dairy network {did} → {out}")