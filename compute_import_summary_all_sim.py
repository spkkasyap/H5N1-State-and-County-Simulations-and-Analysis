import os
import pandas as pd
import numpy as np

# Base directory containing all simulation folders
base_dir = "outputs/simulations/"

# Seed state name
SEED_STATE = "Texas"

print(f"\nProcessing all subfolders in: {base_dir}")

# Dictionary: state -> list of first import days across all subfolders/files
state_first_imports = {}

# Loop through all simulation subfolders
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue  # skip files

    print(f"  Processing folder: {folder}")

    # Loop over all processed network files in each subfolder
    for file in os.listdir(folder_path):
        if file.endswith("_state.network.csv"):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)

            # Validate columns
            if not {'head', 'tail', 'day'}.issubset(df.columns):
                print(f"    Skipping {file}: missing columns")
                continue

            # Get first day each state appears in 'tail'
            first_imports = (
                df.groupby('tail')['day']
                .min()
                .reset_index()
                .rename(columns={'tail': 'state', 'day': 'first_import_day'})
            )

            # Ensure the seed state (e.g., Texas) has day 28
            if SEED_STATE not in first_imports['state'].values:
            	first_imports = pd.concat(
                    [first_imports, pd.DataFrame({'state': [SEED_STATE], 'first_import_day': [28]})],
                    ignore_index=True
                )
            else:
                first_imports.loc[first_imports['state'] == SEED_STATE, 'first_import_day'] = 28

            # Accumulate first import days per state across all subfolders
            for _, row in first_imports.iterrows():
                state = row['state']
                day = row['first_import_day']
                state_first_imports.setdefault(state, []).append(day)

if not state_first_imports:
    print("No processed network files found in any subfolder.")
    exit()

# Compute summary statistics for each state
summary_rows = []
for state, days in state_first_imports.items():
    percentiles = np.percentile(days, [2.5, 5, 25, 75, 95, 97.5])
    summary_rows.append({
        'state': state,
        'mean_first_import_day': np.mean(days),
        'median_first_import_day': np.median(days),
        'earliest_first_import_day': np.min(days),
        'latest_first_import_day': np.max(days),
        'p2_5_first_import_day': percentiles[0],
        'p5_first_import_day': percentiles[1],
        'p25_first_import_day': percentiles[2],
        'p75_first_import_day': percentiles[3],
        'p95_first_import_day': percentiles[4],
        'p97_5_first_import_day': percentiles[5],
        'num_files': len(days)
    })

# Create summary DataFrame
summary_df = pd.DataFrame(summary_rows).sort_values('median_first_import_day').reset_index(drop=True)

# Save combined summary
output_path = os.path.join(base_dir, "all_import_summary.csv")
summary_df.to_csv(output_path, index=False)

print(f"\n Combined summary saved to: {output_path}")
print("All subfolders processed successfully.")
