import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FACTOR = 1
PERIOD_OFFSET = 0.5  # Offset in seconds before and after foot contact

# List of CSV files for different treadmill speeds
# file_paths = [
#     ['PASSIVE_LONGER_1KMH.csv', 'PASSIVE_LONGER_1KMH_2.csv'],
#     ['PASSIVE_LONGER_1.5KMH.csv', 'PASSIVE_LONGER_1.5KMH_2.csv'],
#     ['PASSIVE_LONGER_2KMH.csv', 'PASSIVE_LONGER_2KMH_2.csv'],
#     ['PASSIVE_LONGER_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH_2.csv'],
#     ['PASSIVE_LONGER_3KMH.csv', 'PASSIVE_LONGER_3KMH_2.csv']
# ]

file_paths = [
    ['PASSIVE_REPAIR1_1KMH.csv', 'PASSIVE_REPAIR1_1KMH_2.csv'],
    ['PASSIVE_REPAIR1_1.5KMH.csv'],
    ['PASSIVE_REPAIR1_2KMH.csv'],
    ['PASSIVE_REPAIR1_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH_2.csv'],
    # ['PASSIVE_REPAIR1_3KMH.csv']
    ['PASSIVE_LONGER_3KMH.csv', 'PASSIVE_LONGER_3KMH_2.csv']
]

speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

# Thresholds for each speed. Computed from plot_pressure_debouncing.py
thresholds = [0.4, 0.6, 0.8, 0.6, 0.4]

def compute_average_data(timestamps, foot_contact1, data1, data2, threshold, factor=1.0, offset=False):
    avg_data1 = []
    avg_data2 = []

    # Identify the transition points from False to True in foot_contact 1
    transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]

    # List to store data for each period
    periods_data1 = []
    periods_data2 = []

    for i in range(len(transitions)-1):
        start_index = transitions[i] - int(PERIOD_OFFSET / dt)  # 0.35 seconds before transition

        if start_index < 0:
            start_index = 0

        if i < len(transitions) - 1:
            end_index = transitions[i + 1] - int(PERIOD_OFFSET / dt)
        else:
            end_index = len(timestamps) - 1 - int(PERIOD_OFFSET / dt)

        period_data1 = data1[start_index:end_index]
        period_data2 = data2[start_index:end_index]

        periods_data1.append(period_data1)
        periods_data2.append(period_data2)

    # Debounce each period's data and then calculate the average
    debounced_periods_data1 = [debounce_foot_contact(pd, 2) for pd in periods_data1]
    debounced_periods_data2 = [debounce_foot_contact(pd, threshold) for pd in periods_data2]
    # print(debounced_periods_data2)

    # Find the maximum length of periods to align data
    max_length = max(len(debounced_periods_data1[i]) for i in range(len(debounced_periods_data1)))
    # print(max_length)
    # Calculate average across all periods for each data point
    for j in range(max_length):
        avg_data1.append(np.mean([debounced_periods_data1[i][j] for i in range(len(debounced_periods_data1)) if j < len(debounced_periods_data1[i])]))
        avg_data2.append(np.mean([debounced_periods_data2[i][j] for i in range(len(debounced_periods_data2)) if j < len(debounced_periods_data2[i])]))

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

def debounce_foot_contact(data, threshold):
    debounced = np.zeros_like(data, dtype=int)
    in_contact = False
    contact_start = -1
    for i in range(1, len(data)):
        if not in_contact and data[i] - data[0] > threshold:
            in_contact = True
            contact_start = i
        elif in_contact and data[i] - data[0] <= threshold:
            break
    if contact_start != -1:
        debounced[contact_start:i] = 1
    return debounced

# Helper function to pad arrays to the same length
def pad_to_max_length(arrays, pad_value=0):
    max_length = max(len(arr) for arr in arrays)
    padded_arrays = np.array([np.pad(arr, (0, max_length - len(arr)), 'constant', constant_values=pad_value) for arr in arrays])
    return padded_arrays

# Iterate over each speed
fig, axs = plt.subplots(len(speeds), 1, figsize=(10, 12), sharex=True)

for i, speed_files in enumerate(file_paths):
    # Initialize lists to store averaged data for each file
    all_avg_data1 = []
    all_avg_data2 = []

    for file_path in speed_files:
        # Load the data from the CSV file
        data = pd.read_csv(file_path)

        # Extract the relevant columns
        timestamps = data['timestamp'].values
        foot_contact1 = data['foot_contact 1'].values
        data1 = data['pressure 1'].values
        data2 = data['pressure 3'].values

        # Compute average dt from timestamps
        dt = compute_average_dt(timestamps)

        # Compute average data across periods
        avg_data1, avg_data2, _ = compute_average_data(timestamps, foot_contact1, data1, data2, threshold=thresholds[i], factor=FACTOR, offset=True)

        all_avg_data1.append(avg_data1)
        all_avg_data2.append(avg_data2)

    # Pad arrays to the same length before averaging
    all_avg_data1_padded = pad_to_max_length(all_avg_data1)
    all_avg_data2_padded = pad_to_max_length(all_avg_data2)

    # Calculate the overall average for all files for the current speed
    final_avg_data1 = np.mean(all_avg_data1_padded, axis=0)
    final_avg_data2 = np.mean(all_avg_data2_padded, axis=0)

    periods = np.arange(len(final_avg_data1)) * dt  # Time in seconds (dynamic timestep)

    # Plotting footfall sequences on the same subplot
    # print(avg_data2_crop)
    front_foot = [1 if p > 0.5 else 0 for p in final_avg_data1]
    back_foot = [-1 if p > 0.5 else 0 for p in final_avg_data2]

    # print(periods)

    # Convert boolean lists to numpy arrays for easier manipulation
    front_foot = np.array(front_foot)
    back_foot = np.array(back_foot)

    # Fill between True values for front foot
    axs[i].fill_between(periods, front_foot, where=front_foot==1, color='red', alpha=0.5, label='Front Foot')

    # Fill between True values for back foot
    axs[i].fill_between(periods, back_foot, where=back_foot==-1, color='grey', alpha=0.5, label='Back Foot')

    axs[i].set_title(f'Treadmill speed {speeds[i]} km/h', fontsize=14)
    axs[i].set_ylim(-1.2, 1.2)
    axs[i].set_xlim(0, max(periods))
    axs[i].set_yticks([-1, 0, 1])
    axs[i].legend(loc='upper left')

# Adjust layout
fig.text(0.5, 0.075, 'Time [seconds]', ha='center', fontsize=12)
plt.tight_layout(rect=[0, 0.1, 1, 1])
plt.show()
