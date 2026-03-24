import os
import pandas as pd
import numpy as np

# Base directory containing all simulation folders
base_dir = "outputs/simulations/"

# Seed state name
SEED_STATE = "Texas"

# Loop through all simulation folders
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue  # skip files

    print(f"\nProcessing folder: {folder}")

    # Dictionary: state -> list of first import days across files
    state_first_imports = {}

    # Loop over all processed network files
    for file in os.listdir(folder_path):
        if file.endswith("_state.network.csv"):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)

            # Validate columns
            if not {'head', 'tail', 'day'}.issubset(df.columns):
                print(f"  Skipping {file}: missing columns")
                continue

            # Get first day each state appears in 'tail'
            first_imports = (
                df.groupby('tail')['day']
                .min()
                .reset_index()
                .rename(columns={'tail': 'state', 'day': 'first_import_day'})
            )

            # Ensure the seed state (e.g., Texas) has day 0
            if SEED_STATE not in first_imports['state'].values:
                first_imports = pd.concat(
                    [first_imports, pd.DataFrame({'state': [SEED_STATE], 'first_import_day': [28]})],
                    ignore_index=True
                )

            # Accumulate first import days per state
            for _, row in first_imports.iterrows():
                state = row['state']
                day = row['first_import_day']
                state_first_imports.setdefault(state, []).append(day)

    if not state_first_imports:
        print(f"  No processed network files found in {folder}")
        continue

    # Compute summary statistics for each state
    summary_rows = []
    for state, days in state_first_imports.items():
        summary_rows.append({
            'state': state,
            'mean_first_import_day': np.mean(days),
            'median_first_import_day': np.median(days),
            'earliest_first_import_day': np.min(days),
            'latest_first_import_day': np.max(days),
        })

    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_rows).sort_values('median_first_import_day').reset_index(drop=True)

    # Save results
    output_path = os.path.join(folder_path, f"{folder}_import_summary.csv")
    summary_df.to_csv(output_path, index=False)

    print(f" Saved summary file: {output_path}")

print("\n All simulation folders processed successfully.")

