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
    ['PASSIVE_LONGER_3KMH.csv'],
    ['PASSIVE_LONGER_3KMH_2.csv'],
]

speeds = [3, 3]  # Corresponding speeds in km/h

# Thresholds for each speed
thresholds = [0.3, 0.3]

def compute_average_data(timestamps, foot_contact1, data1, data2, threshold, factor=1.0, offset=False):
    avg_data1 = []
    avg_data2 = []

    # Identify the transition points from False to True in foot_contact 1
    transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]

    # List to store data for each period
    periods_data1 = []
    periods_data2 = []

    for i in range(len(transitions)-1):
        start_index = transitions[i] - int(PERIOD_OFFSET / dt)  # 0.5 seconds before transition

        if start_index < 0:
            start_index = 0

        if i < len(transitions) - 1:
            end_index = transitions[i + 1] - int(PERIOD_OFFSET / dt)
        else:
            end_index = len(timestamps) - 1

        period_data1 = data1[start_index:end_index]
        period_data2 = data2[start_index:end_index]

        periods_data1.append(period_data1)
        periods_data2.append(period_data2)

    # Debounce each period's data and then calculate the average
    debounced_periods_data1 = [debounce_foot_contact(pd, 3) for pd in periods_data1]
    debounced_periods_data2 = [debounce_foot_contact(pd, threshold) for pd in periods_data2]

    # add padding to debounced_period to have the same length as the pressure data, aligned with it
    start_array1 = []
    start_array2 = []
    if (transitions[0]-int(PERIOD_OFFSET/dt)) > 0:
        start_array1 = np.zeros(transitions[0]-int(PERIOD_OFFSET/dt)).tolist()
        start_array2 = np.zeros(transitions[0]-int(PERIOD_OFFSET/dt)).tolist()

    end_array1 = []
    end_array2 = []
    if (transitions[-1]-int(PERIOD_OFFSET/dt)) < len(data1):
        end_array1 = np.zeros(len(data1)-(transitions[-1]-int(PERIOD_OFFSET/dt))).tolist()
        end_array2 = np.zeros(len(data2)-(transitions[-1]-int(PERIOD_OFFSET/dt))).tolist()


    # Find the maximum length of periods to align data
    max_length = max(len(debounced_periods_data1[i]) for i in range(len(debounced_periods_data1)))

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
    
    flattened_array1 = start_array1
    flattened_array2 = start_array2

    for i in range(len(debounced_periods_data1)):
        flattened_array1.extend(debounced_periods_data1[i])

    for i in range(len(debounced_periods_data2)):
        flattened_array2.extend(debounced_periods_data2[i])

    flattened_array1.extend(end_array1)
    flattened_array2.extend(end_array2)

    print(len(flattened_array1), len(data1))
    print(len(flattened_array2), len(data2))
    

    return np.array(flattened_array1), np.array(flattened_array2), avg_data1, avg_data2, dt

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

# Create a figure for plotting
fig, axs = plt.subplots(len(speeds), 1, figsize=(12, 10), sharex=True)

for i, speed_files in enumerate(file_paths):
    for j, file_path in enumerate(speed_files):
        # Load the data from the CSV file
        data = pd.read_csv(file_path)

        # Extract the relevant columns
        timestamps = data['timestamp'].values - data['timestamp'].values[0]
        foot_contact1 = data['foot_contact 1'].values
        data1 = data['pressure 1'].values
        data2 = data['pressure 3'].values

        # Compute average dt from timestamps
        dt = compute_average_dt(timestamps)

        # Compute average data across periods
        debounced_periods_data1, debounced_periods_data2, avg_data1, avg_data2, _ = compute_average_data(timestamps, foot_contact1, data1, data2, threshold=thresholds[i], factor=FACTOR, offset=True)
        
        # Plotting pressure 1 and pressure 3 against timestamps for current file
        # axs[i].plot(timestamps, data1, label=f'Pressure 1 - File {j+1}')
        axs[i].plot(timestamps, data2, label=f'Pressure 3 - File {j+1}')

        # Use axvspan to fill areas where debounced_periods_data1 is 100
        # for k in range(len(timestamps) - 1):
        #     if debounced_periods_data1[k] == 1:
        #         axs[i].axvspan(timestamps[k], timestamps[k+1], color='red', alpha=0.5, label='Front Foot' if j == 0 and k == 0 else "")

        for k in range(len(timestamps) - 1):
            if debounced_periods_data2[k] == 1:
                axs[i].axvspan(timestamps[k], timestamps[k+1], color='blue', alpha=0.1, label='Back Foot' if j == 0 and k == 0 else "")

        axs[i].set_title(f'Treadmill speed {speeds[i]} km/h', fontsize=12)
        axs[i].set_ylabel('Pressure')
        axs[i].legend()

# Adjust layout
fig.text(0.5, 0.04, 'Time [seconds]', ha='center', fontsize=12)
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.show()