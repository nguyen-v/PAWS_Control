import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# List of treadmill speeds and corresponding CSV files
speeds = [1, 1.5, 2, 2.5, 3]  # in km/h
file_paths = {
    # 1: ['PASSIVE_REPAIR1_1KMH.csv', 'PASSIVE_REPAIR1_1KMH_2.csv'],
    # 1.5: ['PASSIVE_REPAIR1_1.5KMH.csv'],
    # 2: ['PASSIVE_REPAIR1_2KMH.csv'],
    # 2.5: ['PASSIVE_REPAIR1_2.5KMH.csv'],
    # 3: ['PASSIVE_REPAIR1_3KMH.csv'],
    # 1: ['PASSIVE_1KMH_NEW_TENDONS2.csv'],
    # 1.5: ['PASSIVE_1.5KMH_NEW_TENDONS2.csv'],
    # 2: ['PASSIVE_2KMH_NEW_TENDONS2.csv'],
    # 2.5: ['PASSIVE_2.5KMH_NEW_TENDONS2.csv'],
    # 3: ['PASSIVE_3KMH_NEW_TENDONS2.csv']
    1: ['PASSIVE_LONGER_NEWTENDONS_1KMH.csv'],
    1.5: ['PASSIVE_LONGER_NEWTENDONS_1.5KMH.csv'],
    2: ['PASSIVE_LONGER_NEWTENDONS_2KMH.csv'],
    2.5: ['PASSIVE_LONGER_NEWTENDONS_2.5KMH.csv'],
    3: ['PASSIVE_LONGER_NEWTENDONS_3KMH.csv']
}

# Initialize lists to store average periods
average_periods = []

# Function to calculate average period from a list of periods
def calculate_average_period(periods_list):
    # Find the maximum length of periods
    max_length = max(len(periods) for periods in periods_list)
    
    # Pad periods with NaN values to make them the same length
    for i in range(len(periods_list)):
        periods_list[i] = np.pad(periods_list[i], (0, max_length - len(periods_list[i])), constant_values=np.nan)
    
    # Compute the average period, ignoring NaN values
    average_period = np.nanmean(periods_list, axis=0)
    
    return np.nanmean(average_period)  # Overall average period

# Iterate over each speed
for speed in speeds:
    periods_list = []
    
    # Iterate over each file for the current speed
    for file_path in file_paths[speed]:
        # Load the data from the CSV file
        data = pd.read_csv(file_path)
        
        # Extract the relevant columns
        timestamps = data['timestamp'].values
        foot_contact1 = data['foot_contact 1'].values
        
        # Identify the transition points from False to True in foot_contact1
        transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]
        
        # Get the timestamps at these transition points
        transition_times = timestamps[transitions + 1]
        
        # Calculate the periods
        periods = np.diff(transition_times)
        
        # Append periods to the list
        periods_list.append(periods)
    
    # Calculate the average period for the current speed
    average_period = calculate_average_period(periods_list)
    
    # Append average period to the list
    average_periods.append(average_period)

# Convert average_periods to numpy array for easier manipulation
average_periods = np.array(average_periods)

# Plotting
plt.figure(figsize=(8, 8))
plt.scatter(speeds, average_periods, color='blue', marker='o', s=100)  # Scatter plot of average periods
plt.xlabel('Treadmill Speed [km/h]', fontsize=20, labelpad=10)
plt.ylabel('Average Period [seconds]', fontsize=20, labelpad=10)
plt.title('Average Period vs Treadmill Speed', fontsize=22)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()
plt.show()
