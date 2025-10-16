import pandas as pd
import os
import glob
import re
from tqdm import tqdm
import sys

# Function to extract numbers from the file name
def extract_numbers(filename):
    match = re.search(r'sir_mu_c(\d+)_alpha(\d+)_beta(\d+)_(\d+)_edgelist_dairy_network_(\d+).network.csv', filename)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
    return None

# Main function
if __name__ == "__main__":
    # Path to directory that contains edgelists of simulations for a particular seed
    file_path = sys.argv[1]
    # Pattern to match files
    pattern = os.path.join(file_path, "sir_edgelist_*_dairy_network_*.network.csv")
    # Day of year up to which the infections are counted; for instance a threshold of 50 means we only consider
    # nodes that are infected within first 50 days of the year
    end = int(sys.argv[2])
    #end = int(sys.argv[3])
    output_filename = sys.argv[3]
    #dc_premises_file_path = sys.argv[4]

    # Use glob to find files that match the pattern
    files = glob.glob(pattern)
    print("Total no. of simulations: "+str(len(files)))
        
    total_num_simulations = len(files)

    # Loading the dairy cows by premises file and creating a dictionary with key as premises id and
    # value as the number of dairy cows in it.
    #dc_premises = pd.read_csv(dc_premises_file_path)
    #S = {} #S is the size of each premises in terms of number of dairy cows
    #S = dict(zip(dc_premises['Id'], dc_premises['d']))
    #S.keys()# Dictionary to count the number of infections pernode
    dc_counties = pd.read_csv('/drives/sdd/H5N1/data/dairy_cows_by_counties.csv')
    S = {} #Sz is the size of each county in terms of number of dairy cows
    S = dict(zip(dc_counties['County'], dc_counties['d']))

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

    total_num_simulations = 10000
    print(total_num_simulations, count_files)
    # Calculate the risk of infection for each node
    node_risk = {node: count / count_files for node, count in infection_counts.items()}

    # Convert the result to a DataFrame
    node_risk_df = pd.DataFrame(list(node_risk.items()), columns=['Node', 'Risk'])

    node_risk = node_risk_df.sort_values(by = "Risk", ascending = False).reset_index()
    node_risk = node_risk.drop('index', axis=1)
    node_risk.to_csv(output_filename, index = False)

