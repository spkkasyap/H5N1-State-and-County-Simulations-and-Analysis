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
# mu(C_i) = mu (1 + alpha * math.log(S(C_i))); where S(C_i) denotes the number of dairy cows in county C_i
def compute_county_recovery_period(S, alpha, mu_c):
    # Recovery period of a county depends on the number of cattle in it
    mu_Ci = {}
    for pid in S.keys():
        mu_Ci[pid] = round(mu_c * (1 + alpha * math.log(S[pid])))
    return mu_Ci


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
def simulate_SIR(G, counties, seeds, start_day, end_day, sim_id, network_name, mu_c, beta, alpha, num_sim, mu_Ci):
    # Loading the dairy cows by premises file and creating a dictionary with key as premises id and
    # value as the number of dairy cows in it.
    
    #dc_premises = pd.read_csv('/drives/sdd/H5N1/data/dairy_cows_by_premises.csv')
    #Sz = {} #Sz is the size of each premises in terms of number of dairy cows
    #Sz = dict(zip(dc_premises['Id'], dc_premises['d']))    
    #compute recovery period for a farm
    #mu_f = compute_farm_recovery_period(Sz, alpha, mu_c)
    
    S, I, R = initialize_states(counties, seeds)
    fp = open(output_dir_path+'sir_compartments_mu_c'+str(mu_c)+'_alpha'+str(alpha)+'_beta'+str(beta)+'_'+sim_id+'_'+network_name+'.csv', 'w')
    fw = open(output_dir_path+'sir_edgelist_mu_c'+str(mu_c)+'_alpha'+str(alpha)+'_beta'+str(beta)+'_'+sim_id+'_'+network_name+'.csv', 'w')
    fp.write("day,S,cI,R,nI\n")
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
            if day == infected_time[u] + mu_Ci[u]:
                new_recoveries.add(u)
                continue
            if u not in snapshot_t.nodes():
                continue
            for v in snapshot_t.successors(u):
                if v in S and v in mu_Ci:
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
        
        fp.write(str(day)+","+str(len(S))+","+str(len(I))+","+str(len(R))+","+str(len(new_infections))+"\n")
        # Write the new infections on day t as a string
        new_inf_str = ""
        for v in new_infections:
            new_inf_str += str(v)+","
        new_inf_str[:-1]
        #fw.write(str(day)+","+str(new_inf_str)+"\n")
    fp.close()
    fw.close()
    return S, I, R

def run_simulations_on_one_dairy_network_realisation(net_file_path, net_file_name, mu_c, beta, alpha, num_sim, epi_start_day, sim_end_day, seeds, mu_f):
    # Load a dairy network file
    dairy_net = pd.read_csv(net_file_path, sep = "\t")
    # Construct temporal network with start date on January 28 and end date of July 31
    G, counties = construct_temporal_network(dairy_net, 1, 365)

    #S, I, R = initialize_states(counties, seeds)
    #print(len(S), len(I), len(R))

    #Simulate SIR Model
    #for i in range(0, num_sim):
    #    S, I, R = simulate_SIR(G, premises, seeds, epi_start_day, sim_end_day, str(i), net_file_name, mu_c, beta, alpha, num_sim)
    with ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(lambda i: simulate_SIR(G, counties, seeds, epi_start_day, sim_end_day, str(i), net_file_name, mu_c, beta, alpha, num_sim, mu_f),range(num_sim))


# Main function
if __name__ == "__main__":
    # Input arguments and parameters to be changed as needed
    seed = int(sys.argv[1])
    #output_dir_path = f'/drives/sdd/H5N1/simulation_outputs_new/seed{seed}_mu_c{mu_c}_beta{beta}_alpha{alpha}/'
    input_dir_path = '/drives/sdd/H5N1/data/dairy_networks/'
    file_template = "dairy_network_{}.network"
    num_sim = int(sys.argv[7]) #number of simulations per dairy network realisation
    num_dairy_networks = int(sys.argv[8]) #number of dairy network realisations 
    total_num_sim = num_sim * num_dairy_networks #total number of simulations to be run
    # Set Initially Infected Nodes
    # Potential initially infected premises in Castro County, Texas. Therefore, seed is Castro County (48069)
    seeds = []
    seeds.append(seed)
    # Recovery period of H5N1 in cattle 
    mu_c = int(sys.argv[2]) 
    # probability of infection, we use low, medium, and high values for beta.
    beta = float(sys.argv[3]) 
    #output_dir_path = f'/drives/sdd/H5N1/simulation_outputs_new/seed{seed}_mu_c{mu_c}_beta{beta}_alpha{alpha}/'
    # Total number of Premises
    N = 3049.0
    # Scaling factor for impact of number of cattle in equation below. Can be changed at a later time
    # mu(f_i) = mu (1 + alpha * math.log(S(f))); where S(f_i) denotes the number of dairy cows in farm f_i
    alpha = float(sys.argv[4])
    output_dir_path = f'/drives/sdd/H5N1/simulation_outputs_statewise/seed{seed}_mu_c{mu_c}_beta{beta}_alpha{alpha}/'

    os.makedirs(os.path.dirname(output_dir_path), exist_ok=True)
    print("Seed, mu_c, beta, alpha: ", seed, mu_c, beta, alpha)
    #Start and end days of each month (given by its number) in a leap year (2024)
    s_day = {}
    e_day = {}
    #Expected start date of the epidemic
    epi_start_day = int(sys.argv[5])
    sim_end_day = int(sys.argv[6])
    
    dc_counties = pd.read_csv('/drives/sdd/H5N1/data/dairy_cows_by_counties.csv')
    Sz = {} #Sz is the size of each county in terms of number of dairy cows
    Sz = dict(zip(dc_counties['County'], dc_counties['d']))
    #compute recovery period for a farm
    mu_f = compute_county_recovery_period(Sz, alpha, mu_c)

    for i in tqdm(range(0, num_dairy_networks), desc="Processing", unit="iteration"):
        net_file_name = os.path.join(input_dir_path, file_template.format(i))
        #print(net_file_name, file_template.format(i))
        run_simulations_on_one_dairy_network_realisation(net_file_name, file_template.format(i), mu_c, beta, alpha, num_sim, epi_start_day, sim_end_day, seeds, mu_f)
    
