import os
import sys
import pandas as pd
from collections import defaultdict

base_dir = "outputs/simulations/"
sim_dir = sys.argv[1]
full_dir_path = base_dir + sim_dir
print(full_dir_path)

# Get list of all relevant files
files = [
    os.path.join(full_dir_path, f)
    for f in os.listdir(full_dir_path)
    if f.endswith("_state.network.csv") and "edgelist" in f
]

print(f"Found {len(files)} files to process.")

# Dictionary to accumulate edge counts
edge_counts = defaultdict(int)

# Process each file
for i, file_path in enumerate(files, 1):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()

    # Count how many times each (head, tail) pair appears in this file
    counts = df.groupby(['head', 'tail']).size()

    # Accumulate across all files
    for (h, t), c in counts.items():
        edge_counts[(h, t)] += c

    if i % 1000 == 0:
        print(f"Processed {i}/{len(files)} files...")

# Convert to a dataframe
result_df = pd.DataFrame(
    [(h, t, c / len(files)) for (h, t), c in edge_counts.items()],
    columns=['head', 'tail', 'avg_edges']
)

# Sort for readability
result_df = result_df.sort_values(by='avg_edges', ascending=False)

# Save the aggregate file
output_file = os.path.join(full_dir_path, "aggregate_state_edges.csv")
result_df.to_csv(output_file, index=False)

print(f"Aggregation complete! Saved to {output_file}")

