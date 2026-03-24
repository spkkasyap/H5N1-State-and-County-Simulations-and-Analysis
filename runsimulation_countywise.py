#Load necessary packages
import sys
import networkx as nx
import os
import pandas as pd
import numpy as np
import random
import math
import csv
import matplotlib.pyplot as plt
from tqdm import tqdm 
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor

# Select only those rows of dairy network that correspond to the days between start_day and end_day
# Nodes in this network are counties and edges correspond to cattle movement between them
def get_dairy_movements_per_period(dairy_net, start_day, end_day):
    dairy_net_season = dairy_net.loc[
        (dairy_net.dayOfYear >= start_day) & (dairy_net.dayOfYear <= end_day),
        ['oCountyId', 'dCountyId', 'dayOfYear', 'volume']
    ]
    dairy_net_season = dairy_net_season.rename(columns={'oCountyId': 'origin'})
    dairy_net_season = dairy_net_season.rename(columns={'dCountyId': 'destination'})
    dairy_net_period = dairy_net_season.groupby(['origin', 'destination'])['volume'].sum().reset_index()
    dairy_net_period = dairy_net_period[dairy_net_period['origin'] != dairy_net_period['destination']]
    return dairy_net_period


# Create a function to construct the temporal network G(t) from county dairy networks
# dairy_net is the dairy network instance
# start_day is the day of the year on which the seed premises got infected
# end_day is the end day of simulation
def construct_temporal_network(dairy_net, start_day, end_day):
    G = {}
    counties = set()
    for t in range(start_day, end_day+1):
        G[t] = nx.DiGraph() 
        dairy_net_t = get_dairy_movements_per_period(dairy_net, t, t)
        for index, row in dairy_net_t.iterrows():
            origin = row['origin']
            destination = row['destination']
            volume = row['volume']
            G[t].add_edge(origin, destination, weight=volume)
            if origin not in counties:
                counties.add(origin)
            if destination not in counties:
                counties.add(destination)
    return G, counties


# recovery period of a county mu(C_i) is defined as follows:
# mu_C(i) = mu_c (1 + alpha * math.log(S(C_i))); where S(C_i) denotes the number of dairy cows in county C_i
def compute_county_recovery_period(S, P, alpha, gamma, mu_c):
    # Recovery period of a county depends on the number of cattle in it
    mu_C = {}
    for cid in S.keys():
        mu_C[cid] = round(mu_c * (1 + alpha * math.log(S[cid]) * (1 + gamma * math.log(P[cid])) ))
    return mu_C


# Function to initialize the state of the nodes
def initialize_states(counties, seeds):
    S = set()
    I = set()
    R = set()
    for u in counties:
        S.add(u)
    for v in seeds:
        I.add(v)
        S.remove(v)
    return S, I, R

# Function to simulate the SIR model
def simulate_SIR(G, counties, seeds, start_day, end_day, sim_id, network_name, mu_c, beta, alpha, gamma, num_sim, mu_C, out_dir_path):
    S, I, R = initialize_states(counties, seeds)
    fp = open(out_dir_path+'sir_compartments_mu_c'+str(mu_c)+'_alpha'+str(alpha)+'_beta'+str(beta)+'_gamma'+str(gamma)+'_'+sim_id+'_'+network_name+'.csv', 'w')
    fw = open(out_dir_path+'sir_edgelist_mu_c'+str(mu_c)+'_alpha'+str(alpha)+'_beta'+str(beta)+'_gamma'+str(gamma)+'_'+sim_id+'_'+network_name+'.csv', 'w')
    fp.write("day,S,cI,R,nI,S_exact\n")
    fw.write("head,tail,day\n")
    infected_time = {}
    for u in I:
        infected_time[u] = start_day

    for day in range(start_day, end_day+1):
        d = day if day % 365 == 0 else day % 365
        snapshot_t = G[d] #get snapshot of cattle movement network for given day
        new_infections = set()
        new_recoveries = set()
        
        for u in I:
            if day == infected_time[u] + mu_C[u]:
                new_recoveries.add(u)
                continue
            if u not in snapshot_t.nodes():
                continue
            for v in snapshot_t.successors(u):
                if v in S and v in mu_C:
                    w_uv = snapshot_t[u][v]['weight']
                    inf_prob = 1 - math.exp(-beta * w_uv)
                    if random.random() < inf_prob:
                        new_infections.add(v)
                        fw.write(str(u)+","+str(v)+","+str(day)+"\n")
                        S.remove(v)
        for v in new_infections:
            I.add(v)
            infected_time[v] = day
        for w in new_recoveries:
            R.add(w)
            I.remove(w)
        N = 2504
        no_S = N - (len(I) + len(R))
        fp.write(str(day)+","+str(no_S)+","+str(len(I))+","+str(len(R))+","+str(len(new_infections))+","+str(len(S))+"\n")
        # Write the new infections on day t as a string
        new_inf_str = ""
        for v in new_infections:
            new_inf_str += str(v)+","
        new_inf_str[:-1]
        #fw.write(str(day)+","+str(new_inf_str)+"\n")
    fp.close()
    fw.close()
    return S, I, R

def run_simulations_on_one_dairy_network_realisation(net_file_path, net_file_name, mu_c, beta, alpha, gamma, num_sim, epi_start_day, sim_end_day, seeds, mu_C, out_dir_path):
    # Load a dairy network file
    dairy_net = pd.read_csv(net_file_path, sep = "\t")
    # Construct temporal network with start date on January 28 and end date of July 31
    G, counties = construct_temporal_network(dairy_net, 1, 365)

    #Simulate SIR Model
    with ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(lambda i: simulate_SIR(G, counties, seeds, epi_start_day, sim_end_day, str(i), net_file_name, mu_c, beta, alpha, gamma, num_sim, mu_C, out_dir_path),range(num_sim))


# Main function
if __name__ == "__main__":
    # Input arguments and parameters to be changed as needed
    seed = int(sys.argv[1])
    # Change the code repo directory according to your local paths
    code_repo_dir = '/Users/user/Documents/Codes/H5N1/H5N1-State-and-County-Simulations-and-Analysis/'
    input_dir_path = code_repo_dir + 'data/raw/USAMMv3_cattle_networks/dairy/'

    # example filename is dairy_network_92.network
    file_template = "dairy_network_{}.network"

    # Set Initially Infected Nodes. From observed data we expect the seed to be Castro County, Texas. Therefore, seed is set to Castro County (48069)
    seeds = []
    seeds.append(seed)

    # Recovery period of H5N1 in cattle 
    mu_c = int(sys.argv[2]) 
    
    # probability of infection, we use low, medium, and high values for beta.
    beta = float(sys.argv[3]) 
    alpha = float(sys.argv[4])
    gamma = float(sys.argv[5])

    # Total number of Counties. Those counties with at at least one dairy cow
    N = 2504

    # Scaling factor for impact of number of cattle on recovery period of a county is given by following equation. 
    # mu(C_i) = mu_c (1 + alpha * math.log(S(C_i)) + gamma * math.log(P(C_i))
    # where S(C_i) denotes the number of dairy cows in county C_i and P(C_i) denotes the number of premises in county C_i
   
    out_dir_path = f'/Users/user/Documents/Codes/H5N1/H5N1-State-and-County-Simulations-and-Analysis/outputs/simulations/seed{seed}_mu_c{mu_c}_beta{beta}_alpha{alpha}_gamma_{gamma}/'
    os.makedirs(os.path.dirname(out_dir_path), exist_ok=True)
    print("Seed, mu_c, beta, alpha, gamma: ", seed, mu_c, beta, alpha, gamma)

    #Start and end days of each month (given by its number) in a leap year (2024)
    s_day = {}
    e_day = {}
    
    #Expected start date of the epidemic
    epi_start_day = int(sys.argv[6])
    sim_end_day = int(sys.argv[7])
    
    num_sim = int(sys.argv[8]) #number of simulations per dairy network realisation
    num_dairy_networks = int(sys.argv[9]) #number of dairy network realisations
    total_num_sim = num_sim * num_dairy_networks #total number of simulations to be run

    dc_count_filepath = code_repo_dir+'data/processed/dairy_cows_by_counties.csv'
    dc_counties = pd.read_csv(dc_count_filepath)
    dc_counties['County'] = dc_counties['County'].astype(int)
    print(dc_counties.head(10))
    Sz = {} #Sz is the size of each county in terms of number of dairy cows
    Sz = dict(zip(dc_counties['County'], dc_counties['d']))

    Pz = {} #Pz is the number of premises in a county
    Pz = dict(zip(dc_counties['County'], dc_counties['p']))

    print(Pz)
    #compute recovery period for a farm
    mu_C = compute_county_recovery_period(Sz, Pz, alpha, gamma, mu_c)

    for i in tqdm(range(0, num_dairy_networks), desc="Processing", unit="iteration"):
        net_file_name = os.path.join(input_dir_path, file_template.format(i))
        #print(net_file_name, file_template.format(i))
        run_simulations_on_one_dairy_network_realisation(net_file_name, file_template.format(i), mu_c, beta, alpha, gamma, num_sim, epi_start_day, sim_end_day, seeds, mu_C, out_dir_path)
    
