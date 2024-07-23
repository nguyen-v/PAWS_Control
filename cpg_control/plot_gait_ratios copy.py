import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FACTOR = 1
PERIOD_OFFSET = 0.5

# List of CSV files for different treadmill speeds
# file_paths = [
#     ['PASSIVE_LONGER_1KMH.csv', 'PASSIVE_LONGER_1KMH_2.csv'],
#     ['PASSIVE_LONGER_1.5KMH.csv', 'PASSIVE_LONGER_1.5KMH_2.csv'],
#     ['PASSIVE_LONGER_2KMH.csv', 'PASSIVE_LONGER_2KMH_2.csv'],
#     ['PASSIVE_LONGER_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH_2.csv'],
#     ['PASSIVE_LONGER_3KMH.csv', 'PASSIVE_LONGER_3KMH_2.csv']
# ]

# speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

# file_paths = [
#     ['PASSIVE_REPAIR1_1KMH.csv', 'PASSIVE_REPAIR1_1KMH_2.csv'],
#     ['PASSIVE_REPAIR1_1.5KMH.csv'],
#     ['PASSIVE_REPAIR1_2KMH.csv'],
#     ['PASSIVE_REPAIR1_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH.csv', 'PASSIVE_LONGER_2.5KMH_2.csv'],
#     ['PASSIVE_LONGER_3KMH.csv', 'PASSIVE_LONGER_3KMH_2.csv']
# ]

# speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

# Thresholds for each speed. Computed from plot_pressure_debouncing.py
# thresholds = [0.4, 0.6, 0.8, 0.6, 0.4]

# WITH NEW TENDONS

file_paths = [
    ['PASSIVE_LONGER_NEWTENDONS_1KMH.csv'],
    ['PASSIVE_LONGER_NEWTENDONS_1.5KMH.csv'],
    ['PASSIVE_LONGER_NEWTENDONS_2KMH.csv'],
    ['PASSIVE_LONGER_NEWTENDONS_2.5KMH.csv'],
    ['PASSIVE_LONGER_NEWTENDONS_3KMH.csv']
]

FRONT_THR = 1

thresholds = [0.5, 0.5, 0.5, 0.8, 0.8]

speeds = [1, 1.5, 2, 2.5, 3]  # Corresponding speeds in km/h

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

        if i < len(transitions) - 1:
            end_index = transitions[i + 1] - int(PERIOD_OFFSET / dt)
        else:
            end_index = len(timestamps) - 1 - int(PERIOD_OFFSET / dt)

        period_data1 = data1[start_index:end_index]
        period_data2 = data2[start_index:end_index]

        periods_data1.append(period_data1)
        periods_data2.append(period_data2)

    # Debounce each period's data and then calculate the average
    debounced_periods_data1 = [debounce_foot_contact(pd, FRONT_THR) for pd in periods_data1]
    debounced_periods_data2 = [debounce_foot_contact(pd, threshold) for pd in periods_data2]

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

    return avg_data1, avg_data2, dt

# Function to compute average time step (dt) from timestamps
def compute_average_dt(timestamps):
    dt = np.mean(np.diff(timestamps))  # Calculate mean time difference
    return dt

def debounce_foot_contact(data, threshold, alpha = 1):
    debounced = np.zeros_like(data, dtype=int)
    in_contact = False
    contact_start = -1
    data_copy = data.copy()
    for i in range(1, len(data)):
        data_copy[i] = data_copy[i-1]*(1-alpha) + data[i]*alpha
        if not in_contact and data_copy[i] - data_copy[0] > threshold:
            in_contact = True
            contact_start = i
        elif in_contact and data_copy[i] - data_copy[0] <= threshold:
            break
    if contact_start != -1:
        debounced[contact_start:i] = 1
    return debounced

# Helper function to pad arrays to the same length
def pad_to_max_length(arrays, pad_value=0):
    max_length = max(len(arr) for arr in arrays)
    padded_arrays = np.array([np.pad(arr, (0, max_length - len(arr)), 'constant', constant_values=pad_value) for arr in arrays])
    return padded_arrays

# Compute metrics for plotting
stance_time_flight_time_ratio = []
stance_time_front_period_ratio = []
stance_time_back_period_ratio = []
double_support_stance_time_ratio = []

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

    #PRINT PERIOD
    print(len(final_avg_data1) * dt)


    # Compute metrics
    stance_time_front = np.sum(final_avg_data1 > 0.5) * dt
    print(stance_time_front)
    stance_time_back = np.sum(final_avg_data2 > 0.5) * dt
    # print(stance_time_back)
    double_support_time = np.sum((final_avg_data1 > 0.5) & (final_avg_data2 > 0.5)) * dt
    # print(double_support_time)
    flight_time = len(final_avg_data1) * dt - stance_time_front - stance_time_back + 2*double_support_time
    # print(flight_time)
    # print(len(final_avg_data1))

    # Append calculated ratios
    stance_time_flight_time_ratio.append(stance_time_front / flight_time)
    stance_time_front_period_ratio.append(stance_time_front / (len(final_avg_data1) * dt))
    stance_time_back_period_ratio.append(stance_time_back / (len(final_avg_data1) * dt))
    double_support_stance_time_ratio.append(double_support_time / stance_time_front)

# Plotting
fig, axs = plt.subplots(2, 2, figsize=(12, 8))

# Plot 1: Stance time / Flight time vs Treadmill speed
axs[0, 0].scatter(speeds, stance_time_flight_time_ratio, marker='o')
axs[0, 0].set_xlabel('Treadmill Speed (km/h)')
axs[0, 0].set_ylabel('Stance Time / Flight Time (-)')
axs[0, 0].set_title('Stance Time / Flight Time vs Treadmill Speed')

# Plot 2: Stance time (front foot) / period vs Treadmill speed
axs[0, 1].scatter(speeds, stance_time_front_period_ratio, marker='o')
axs[0, 1].set_xlabel('Treadmill Speed (km/h)')
axs[0, 1].set_ylabel('Stance Time (Front Foot) / Period (-)')
axs[0, 1].set_title('Stance Time (Front Foot) / Period vs Treadmill Speed')

# Plot 3: Stance time (back foot) / period vs Treadmill speed
axs[1, 0].scatter(speeds, stance_time_back_period_ratio, marker='o')
axs[1, 0].set_xlabel('Treadmill Speed (km/h)')
axs[1, 0].set_ylabel('Stance Time (Back Foot) / Period (-)')
axs[1, 0].set_title('Stance Time (Back Foot) / Period vs Treadmill Speed')

# Plot 4: Double support / stance time vs Treadmill speed
axs[1, 1].scatter(speeds, double_support_stance_time_ratio, marker='o')
axs[1, 1].set_xlabel('Treadmill Speed (km/h)')
axs[1, 1].set_ylabel('Double Support / Stance Time (-)')
axs[1, 1].set_title('Double Support / Stance Time vs Treadmill Speed')

# Adjust layout
plt.tight_layout()
plt.show()
