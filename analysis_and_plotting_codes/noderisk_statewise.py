import pandas as pd
import os
import glob
from tqdm import tqdm
import sys


# Main function
if __name__ == "__main__":
    # Path to directory that contains edgelists of simulations for a particular seed
    file_path = sys.argv[1]
    # Pattern to match files
    pattern = os.path.join(file_path, "sir_edgelist_*_dairy_network_*_state.network.csv")
    # Day of year up to which the infections are counted; for instance a threshold of 50 means we only consider
    # nodes that are infected within first 50 days of the year
    end = int(sys.argv[2])
    output_filename = '/Users/user/Documents/Codes/H5N1/H5N1-State-and-County-Simulations-and-Analysis/outputs/noderisk_end_of_autumn_730605.csv'
    base_path = '/Users/user/Documents/Codes/H5N1/H5N1-State-and-County-Simulations-and-Analysis/data/processed/'

    # Use glob to find files that match the pattern
    files = glob.glob(pattern)
    print("Total no. of simulations: "+str(len(files)))
        
    total_num_simulations = len(files)

    # Loading the dairy cows by premises file and creating a dictionary with key as state and
    # value as the number of dairy cows in it.
    dc_state = pd.read_csv(f'{base_path}dairy_cows_by_state.csv')
    S = {} #Sz is the size of each state in terms of number of dairy cows
    S = dict(zip(dc_state['NAME_1'], dc_state['d']))

    infection_counts = {node: 0 for node in S}
    print(len(infection_counts))

    # Iterate through each file and update the edges
    # Iterate over the files
    count_files = 0
    #for file in files:
    for file in tqdm(files, desc="Processing files", unit="file"):
        #print(file)
        count_files += 1
        # Check if file is empty
        if os.path.getsize(file) == 0:
            continue

        transmission_df = pd.read_csv(file)

        # Filter rows where the infection day is within the threshold
        transmission_df_filtered = transmission_df[transmission_df['day'] <= end]

        # Track infections for each node 'v'
        infected_nodes = transmission_df_filtered['tail'].unique()

        for node in infected_nodes:
            if node in infection_counts:
                infection_counts[node] += 1
            else:
                infection_counts[node] = 1

    total_num_simulations = count_files
    print(total_num_simulations, count_files)
    # Calculate the risk of infection for each node
    node_risk = {node: count / count_files for node, count in infection_counts.items()}

    # Convert the result to a DataFrame
    node_risk_df = pd.DataFrame(list(node_risk.items()), columns=['Node', 'Risk'])

    node_risk = node_risk_df.sort_values(by = "Risk", ascending = False).reset_index()
    node_risk = node_risk.drop('index', axis=1)
    node_risk.to_csv(output_filename, index = False)

