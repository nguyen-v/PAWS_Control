import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Define the conversion factor from motor turns to degrees and reduction ratio
turns_to_degrees = 360
reduction_ratio = 5

# File paths and corresponding treadmill speeds
file_paths = {
    "1 km/h": ['PASSIVE_REPAIR1_1KMH.csv', 'PASSIVE_REPAIR1_1KMH_2.csv'],
    "1.5 km/h": ['PASSIVE_REPAIR1_1.5KMH.csv'],
    "2 km/h": ['PASSIVE_REPAIR1_2KMH.csv'],
    "2.5 km/h": ['PASSIVE_REPAIR1_2.5KMH.csv'],
    "3 km/h": ['PASSIVE_REPAIR1_3KMH.csv']
    # "3.5 km/h": ["PASSIVE_3.5_LONG.csv", "ANOTHER_3.5KMH.csv"]
}

speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

# Initialize lists to store results
speeds = []
avg_p2p_synergy_1 = []
avg_p2p_synergy_3 = []

# Function to calculate peak-to-peak value
def calculate_p2p(data):
    return data.max() - data.min()

# Loop through each speed and process the corresponding files
for speed, files in file_paths.items():
    # Initialize lists to store peak-to-peak values for the current speed
    p2p_synergy_1_list = []
    p2p_synergy_3_list = []
    
    for file_path in files:
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Convert positions from motor turns to degrees and apply reduction ratio
        df['position 1'] = (df['position 1'] * turns_to_degrees) / reduction_ratio
        df['position 3'] = (df['position 3'] * turns_to_degrees) / reduction_ratio
        
        # Calculate peak-to-peak values for positions
        p2p_synergy_1 = calculate_p2p(df['position 1'])
        p2p_synergy_3 = calculate_p2p(df['position 3'])
        
        # Append the peak-to-peak values to the lists
        p2p_synergy_1_list.append(p2p_synergy_1)
        p2p_synergy_3_list.append(p2p_synergy_3)
    
    # Calculate the average of the peak-to-peak values for the current speed
    avg_p2p_synergy_1.append(np.mean(p2p_synergy_1_list))
    avg_p2p_synergy_3.append(np.mean(p2p_synergy_3_list))
    speeds.append(float(speed.split()[0]))  # Extract the numeric part of the speed

# Plotting
plt.figure(figsize=(8, 8))
plt.scatter(speeds, avg_p2p_synergy_1, color='red', marker='o', s=100, label='Synergy 1')  # Increased marker size
plt.scatter(speeds, avg_p2p_synergy_3, color='gray', marker='s', label='Synergy 2')

# Formatting the plot
hl = plt.legend(fontsize=18, loc='upper left')
hl.get_frame().set_alpha(None)
hl.get_frame().set_facecolor((1, 1, 1, 0.8))
plt.xlabel('Treadmill Speed [km/h]', fontsize=20, labelpad=0)
plt.ylabel('Synergy Activation [deg]', fontsize=20, labelpad=0)  # Updated y-label
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.box(True)
plt.gca().tick_params(labelsize=18)

# Display the plot
plt.show()
