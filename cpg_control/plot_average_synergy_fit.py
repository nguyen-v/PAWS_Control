import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FACTOR = 180 / (np.pi)  # Conversion factor from radians to degrees
PERIOD_OFFSET = 0.35  # Offset in seconds before and after foot contact

# List of CSV files for different treadmill speeds
# file_paths = {
#     1: ['PASSIVE_LONGER_1KMH.csv', 'PASSIVE_LONGER_1KMH_2.csv'],
#     1.5: ['PASSIVE_LONGER_1.5KMH.csv', 'PASSIVE_LONGER_1.5KMH_2.csv'],
#     2: ['PASSIVE_LONGER_2KMH.csv', 'PASSIVE_LONGER_2KMH_2.csv'],
#     2.5: ['PASSIVE_LONGER_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH_2.csv'],
#     3: ['PASSIVE_LONGER_3KMH.csv', 'PASSIVE_LONGER_3KMH_2.csv']
# }
# speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

file_paths = {
    1.5: ['PASSIVE_LONGER_NEWTENDONS_1.5KMH.csv'],
}

# file_paths = {
#     1: ['PASSIVE_REPAIR1_1KMH.csv', 'PASSIVE_REPAIR1_1KMH_2.csv'],
#     1.5: ['PASSIVE_REPAIR1_1.5KMH.csv'],
#     2: ['PASSIVE_REPAIR1_2KMH.csv'],
#     2.5: ['PASSIVE_REPAIR1_2.5KMH.csv'],
#     3: ['PASSIVE_REPAIR1_3KMH.csv']
# }
speeds = [1.5]  # Corresponding speeds in km/h

# Function to compute average data across periods
def compute_average_data(timestamps, foot_contact1, data1, data2, factor=1.0, offset=False):
    avg_data1 = []
    avg_data2 = []

    # Identify the transition points from False to True in foot_contact1
    transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]

    # List to store data for each period
    periods_data1 = []
    periods_data2 = []

    for i in range(len(transitions)):
        start_index = transitions[i] - int(PERIOD_OFFSET / dt)  # 0.5 seconds before transition

        if i < len(transitions) - 1:
            end_index = transitions[i + 1] - int(PERIOD_OFFSET / dt)
        else:
            end_index = len(timestamps) - 1 - int(PERIOD_OFFSET / dt)

        period_data1 = data1[start_index:end_index]
        period_data2 = data2[start_index:end_index]

        periods_data1.append(period_data1)
        periods_data2.append(period_data2)

    # Find the maximum length of periods to align data
    max_length = max(len(period) for period in periods_data1)

    # Pad periods with NaN values to make them the same length
    for i in range(len(periods_data1)):
        periods_data1[i] = np.pad(periods_data1[i], (0, max_length - len(periods_data1[i])), constant_values=np.nan)
        periods_data2[i] = np.pad(periods_data2[i], (0, max_length - len(periods_data2[i])), constant_values=np.nan)

    # Calculate average across all periods for each data point
    avg_data1 = np.nanmean(periods_data1, axis=0)
    avg_data2 = np.nanmean(periods_data2, axis=0)

    # Apply the factor for unit conversion
    avg_data1 = np.array(avg_data1) * factor
    avg_data2 = np.array(avg_data2) * factor

    if offset:
        # Offset positions to start at y=0
        avg_data1 = np.array(avg_data1) - avg_data1[0]
        avg_data2 = np.array(avg_data2) - avg_data2[0]

    return avg_data1, avg_data2, dt

# Function to compute average time step (dt) from timestamps
def compute_average_dt(timestamps):
    dt = np.mean(np.diff(timestamps))  # Calculate mean time difference
    return dt

# Iterate over each speed and process the corresponding files
fig, axs = plt.subplots(1, 1, figsize=(6, 5), sharex=True)

# Variables to store global y-axis limits
global_min = float('inf')
global_max = float('-inf')

for idx, speed in enumerate(speeds):
    avg_data1_list = []
    avg_data2_list = []

    for file_path in file_paths[speed]:
        # Load the data from the CSV file
        data = pd.read_csv(file_path)

        # Extract the relevant columns
        timestamps = data['timestamp'].values
        foot_contact1 = data['foot_contact 1'].values
        data1 = data['position 1'].values
        data2 = data['position 3'].values

        # Compute average dt from timestamps
        dt = compute_average_dt(timestamps)

        # Compute average data across periods
        avg_data1, avg_data2, _ = compute_average_data(timestamps, foot_contact1, data1, data2, factor=FACTOR, offset=True)

        avg_data1_list.append(avg_data1)
        avg_data2_list.append(avg_data2)



    # Find the maximum length of averaged data for the current speed
    max_length = max(len(data) for data in avg_data1_list)

    # Pad averaged data with NaN values to make them the same length
    for i in range(len(avg_data1_list)):
        avg_data1_list[i] = np.pad(avg_data1_list[i], (0, max_length - len(avg_data1_list[i])), constant_values=np.nan)
        avg_data2_list[i] = np.pad(avg_data2_list[i], (0, max_length - len(avg_data2_list[i])), constant_values=np.nan)

    # Compute the overall average for the current speed
    avg_data1 = np.nanmean(avg_data1_list, axis=0)
    avg_data2 = np.nanmean(avg_data2_list, axis=0)
    
    periods = np.arange(len(avg_data1)) * dt  # Time in seconds (dynamic timestep)

    # Crop data to x = 0 to 1
    mask = (periods >= 0) & (periods <= 1.3)
    periods_crop = periods[mask]
    avg_data1_crop = avg_data1[mask]
    avg_data2_crop = avg_data2[mask]

    # Update global y-axis limits
    global_min = min(global_min, np.min(avg_data1_crop), np.min(avg_data2_crop))
    global_max = max(global_max, np.max(avg_data1_crop), np.max(avg_data2_crop))

    sine1 = np.sin(2 * np.pi * 1 * periods_crop)
    
    TURN_TO_DEG = 360
    AMPLIFIER = 1
    amp = [AMPLIFIER*29, AMPLIFIER*30] # 1

    period = [1, 0.7]

    omega = [2*np.pi/(period[0]), 2*np.pi/period[1]] # 1
        
    theta = [-0.5*np.pi, -np.pi*0.05] # 1.5

    offset = [1.5/(2*np.pi),-3/(2*np.pi)] # 1, 1.5

    t_off = [0.145, 0.17] #1

    sine1 = (-amp[0] * np.sin(omega[0] * (periods_crop - t_off[0]) + theta[0])
                                    + amp[0] * np.sin(theta[0]))

    sine1[periods_crop < t_off[0]] = 0
    sine1[periods_crop > period[0]+t_off[0]] = 0


    
    sine2 = (-amp[1] * np.sin(omega[1] * (periods_crop - t_off[1]) + theta[1])
                                    + amp[1] * np.sin(theta[1]))
    sine2[periods_crop < t_off[1]] = 0
    sine2[periods_crop > period[1]+t_off[1]] = 0
    # Plotting on subplots
    axs.plot(periods_crop, avg_data1_crop, color='red', label='Average Synergy 1', alpha=0.3, linewidth = 3)
    axs.plot(periods_crop, avg_data2_crop, color='black', label='Average Synergy 2', alpha=0.3, linewidth = 3)

    axs.plot(periods_crop, sine1, color='red', label='Synergy fit 1',linestyle='dashed', linewidth = 3)
    axs.plot(periods_crop, sine2, color='black', label='Synergy fit 2',linestyle='dashed', linewidth = 3)

    axs.set_title(f'Treadmill speed {speed} km/h', fontsize=14)
    axs.grid(True)
    axs.legend(loc='upper left', fontsize=10)


# Set x-axis labels for each column
axs.set_xlabel('Time [seconds]', fontsize=12)

# Common Y-axis label
fig.text(0.04, 0.5, 'Synergy [deg]', va='center', rotation='vertical', fontsize=12)

axs.set_ylim(-80, 30)

# Adjust layout
plt.tight_layout(rect=[0.05, 0.05, 1, 1])
plt.show()