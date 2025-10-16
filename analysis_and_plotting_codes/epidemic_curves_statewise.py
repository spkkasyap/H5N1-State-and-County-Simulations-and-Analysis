import matplotlib.pyplot as plt
import pandas as pd
import math
import csv
import sys
import fnmatch
import os
import random
import numpy as np

# Plotting function
def plot_epicurve(files, rec_pd, alpha, beta, seed):
    # Total number of Premises
    N = 63984.0
    color1 = 'tab:blue'
    color2 = 'tab:red'
    plt.figure(figsize=(10, 6))
    fig, ax1 = plt.subplots()
    # Create a second y-axis
    ax2 = ax1.twinx()
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Number of new counties infected by day', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax2.set_ylabel('Cumulative number of counties infected by day ', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    num_sim = 0
    count = 0
    df_list = []
    # Track if labels for the types have been added (so they only appear once in the legend)
    color1_label_added = False
    color2_label_added = False
    cum_infected_all_simulations = []
    for file_name in files:
        # Read the CSV file into a DataFrame
        count += 1
        #if count == 10:
        #    break
        df = pd.read_csv(file_name)
        #print(df)
        num_sim += 1
        # Calculate total population size, assuming it's constant
        #N = df['S'] + df['I'] + df['R']

        # Calculate the daily new infections as the decrease in susceptible individuals
        df['new_infections'] = df['S'].shift(1) - df['S']
        
        # Fill NaN in the first row (since there's no previous day to subtract) with zero or initial infection data
        df['new_infections'] = df['new_infections'].fillna(0)

        # Calculate the proportion of new infections on a given day
        df['prop'] = df['new_infections'] / N

        # Calculate the cumulative number of overall infections as N - S
        df['cum_infected'] = df['new_infections'].cumsum() + 1 

        # Calculate the cumulative proportion of overall infections
        df['cum_prop'] = df['cum_infected'] / N

        cum_infected_all_simulations.append(df['cum_infected'].values)
        #print(df.head(244))
        #df['prop'] = df['I']/N
        #df['cum_prop'] = (df['I'] -  df['R'])/ N
        # Plot the daily proportion of infections on the primary y-axis
        #if not color1_label_added:
        #    ax1.plot(df['day'], df['new_infections'], color=color1, alpha = 0.02, label = 'New infections')
        #    color1_label_added = True
        #else:
        ax1.plot(df['day'], df['new_infections'], color=color1, alpha = 0.02)
        #if not color2_label_added:
        #    ax2.plot(df['day'], df['cum_infected'], color=color2, alpha = 0.009, label = 'Cumulative infections')
        #    color2_label_added = True
        #else:
        ax2.plot(df['day'], df['cum_infected'], color=color2, alpha = 0.009)

    # Convert the list of arrays to a 2D numpy array (rows: simulations, columns: days)
    cum_infected_all_simulations = np.array(cum_infected_all_simulations)

    # Calculate the median and 95% confidence intervals
    median_cum_infected = np.median(cum_infected_all_simulations, axis=0)
    mean_cum_infected = np.mean(cum_infected_all_simulations, axis = 0)
    #ci_95_lower = np.percentile(cum_infected_all_simulations, 2.5, axis=0)  # Lower bound of 95% CI
    #ci_95_upper = np.percentile(cum_infected_all_simulations, 97.5, axis=0)  # Upper bound of 95% CI

    # Plot the median curve for cumulative infections
    ax2.plot(df['day'], median_cum_infected, color='gray', label='Median Cumulative Infected Counties')
    ax2.plot(df['day'], mean_cum_infected, color ='red', label='Mean Cumulative Infected Counties')
    # Fill the 95% confidence interval
    #ax2.fill_between(df['day'], ci_95_lower, ci_95_upper, color=color2, alpha=0.2, label='95% CI')


    # Spring: Days 60 to 152
    ax1.axvspan(60, 151, color='lightgreen', alpha=0.1, label='Spring')

    # Summer: Days 152 to 243
    ax1.axvspan(152, 243, color='yellow', alpha=0.1, label='Summer')

    # Autumn: Days 244 to 334
    ax1.axvspan(244, 334, color='lightcoral', alpha=0.1, label='Autumn')

    # Winter: Days 335 to 59
    ax1.axvspan(28, 59, color='black', alpha=0.1, label='Winter')
    ax1.axvspan(335, 424, color='black', alpha=0.1)

    # Add legends
    #print(df_list[0].head())
    #print(df_list[1].head())
    # Step 1: Combine data from all dataframes into a single list of values for each day
    #all_days = sorted(df_list[0]['day'].unique())  # Assuming each dataframe has the same 'day' values

    # Create empty lists to store the new infections and cumulative infected data for each day
    #new_infections_all = []
    #cum_infected_all = []

    #for day in all_days:
    #    new_infections_for_day = []
    #    cum_infected_for_day = []

    #    for df in df_list:
    #        new_infections_for_day.append(df.loc[df['day'] == day, 'new_infections'].values[0])
    #        cum_infected_for_day.append(df.loc[df['day'] == day, 'cum_infected'].values[0])

    #   new_infections_all.append(new_infections_for_day)
    #    cum_infected_all.append(cum_infected_for_day)

    #print(new_infections_all[0])
    #print(cum_infected_all[0])

    # Step 2: Calculate the median and 50% confidence interval (25th and 75th percentiles)
    #new_infections_median = [np.median(day) for day in new_infections_all]
    #new_infections_lower = [np.percentile(day, 25) for day in new_infections_all]
    #new_infections_upper = [np.percentile(day, 75) for day in new_infections_all]

    #cum_infected_median = [np.median(day) for day in cum_infected_all]
    #cum_infected_lower = [np.percentile(day, 25) for day in cum_infected_all]
    #cum_infected_upper = [np.percentile(day, 75) for day in cum_infected_all]
    
    #print(cum_infected_median)
    #print(cum_infected_all)
    # Plot the median and confidence intervals for 'cum_infected'
    #ax2.plot(all_days, cum_infected_median, color='tab:red', alpha=1, label='Median Cumulative Infections')
    #ax2.fill_between(all_days, cum_infected_lower, cum_infected_upper, color='tab:red', alpha=0.5, label='50% CI Cumulative Infections')

    # Add a legend
    ax1.legend(loc='upper left', framealpha = 0.5, fontsize = 8)
    ax2.legend(loc='upper right', framealpha = 0.5, fontsize=8)
    #ax1.set_yscale('log')
    #ax2.set_yscale('log')
    #fig.tight_layout()  # Adjust layout to accommodate both y-axes
    plt.title(r'$(seed, \mu_{c}, \alpha, \beta, s\_day )$=('+str(seed)+', '+str(rec_pd)+', '+str(alpha)+', '+str(beta)+', 28)', fontsize = 12)
    plt.savefig('figures25sw/sir_plot_mu_c'+str(rec_pd)+'_alpha'+str(alpha)+'_beta'+str(beta)+'_'+str(seed)+'_28.png', dpi = 600)
    # Show plot
    plt.show()

def find_matching_files(directory, rec_pd, alpha, beta):
    # Define the pattern you're looking for
    pattern = 'sir_compartments_mu_c'+rec_pd+'_alpha'+alpha+'_beta'+beta+'*.csv' 
    print(pattern)
    # Initialize a list to store matching file names
    matching_files = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Check if the filename matches the pattern and does not contain 'edgelist'
            if fnmatch.fnmatch(filename, pattern) and 'edgelist' not in filename:
                matching_files.append(os.path.join(root, filename))

    return matching_files



if __name__ == "__main__":
    rec_pd = sys.argv[2]
    alpha = sys.argv[3]
    beta = sys.argv[4]
    directory = sys.argv[1]
    seed = sys.argv[5]

    print(directory)
    matching_files = find_matching_files(directory, rec_pd, alpha, beta)
    count1 = 0
    count2 = 0
    random_files = []
    for curr_file in matching_files:
        count1 += 1
        rand = random.random()
        if rand < 0.5:
            continue
        count2 += 1
        random_files.append(curr_file)
        
    print(f'Number of matching files: {count1}')
    print(f'Number of files selected randomly from the matched files: {count2}')
    plot_epicurve(random_files, rec_pd, alpha, beta, seed)

