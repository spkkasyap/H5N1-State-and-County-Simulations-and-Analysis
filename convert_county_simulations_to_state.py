import os
import pandas as pd
import sys

# Path to the main directory containing all simulation folders
base_dir = "outputs/simulations/"
#sim_dir = sys.argv[1]
#full_dir_path = base_dir + sim_dir

# Dictionary mapping county IDs to state names
# (You can read this from a CSV if needed)
county_to_state = pd.read_csv("data/processed/county_to_state_mapping.csv").set_index('County')['State'].to_dict()

# Loop through all subfolders (each seed_mu_beta_alpha_gamma folder)
count = 0
for folder in os.listdir(base_dir):
    count += 1
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue

    print(f"Processing folder {count}: {folder}")

    file_count = 0
    # Loop through all .network.csv files
    for file in os.listdir(folder_path):
        file_count += 1
        if file_count %1000 == 0:
            print(f"{file_count} files processed in folder")
        if "edgelist" in file and file.endswith(".network.csv") and not file.endswith("_state.network.csv"):
            file_path = os.path.join(folder_path, file)
            #print(f"Processing {file} in {file_path}")

            # Read the directed edgelist
            df = pd.read_csv(file_path, encoding='utf-8-sig', header=0)
            #print(df.head(5))
            # Replace county FIPS with state names
            df['head'] = df['head'].map(county_to_state)
            df['tail'] = df['tail'].map(county_to_state)

            # Drop edges with unmapped counties (optional)
            df = df.dropna(subset=['head', 'tail'])

            # Save with new name
            output_file = file.replace(".network.csv", "_state.network.csv")
            output_path = os.path.join(folder_path, output_file)
            df.to_csv(output_path, index=False)

print("All files processed successfully.")
    
