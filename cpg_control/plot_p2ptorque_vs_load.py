import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PERIOD_OFFSET = 0.35  # Offset in seconds before and after foot contact

# List of CSV files for different loads
file_paths = {
    0.25: ['LOAD_0.25KG.csv'],
    0.50: ['LOAD_0.5KG.csv'],
    0.75: ['LOAD_0.75KG.csv'],
    1.00: ['LOAD_1KG.csv'],
    1.25: ['LOAD_1.25KG.csv'],
    1.50: ['LOAD_1.5KG.csv'],
    1.75: ['LOAD_1.75KG.csv']
}
loads = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75]  # Corresponding loads in kg

# Function to compute peak-to-peak power for each period and average them
def compute_peak_to_peak_power(timestamps, foot_contact1, power):
    # Identify the transition points from False to True in foot_contact1
    transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]

    # List to store peak-to-peak power for each period
    peak_to_peak_powers = []

    for i in range(len(transitions)):
        start_index = transitions[i] - int(PERIOD_OFFSET / dt)  # 0.35 seconds before transition

        if i < len(transitions) - 1:
            end_index = transitions[i + 1] - int(PERIOD_OFFSET / dt)
        else:
            end_index = len(timestamps) - 1 - int(PERIOD_OFFSET / dt)

        period_power = power[start_index:end_index]

        peak_to_peak_power = np.nanmax(period_power) - np.nanmin(period_power)
        peak_to_peak_powers.append(peak_to_peak_power)

    # Compute average peak-to-peak power
    avg_peak_to_peak_power = np.nanmean(peak_to_peak_powers)

    return avg_peak_to_peak_power

# Function to compute average time step (dt) from timestamps
def compute_average_dt(timestamps):
    dt = np.mean(np.diff(timestamps))  # Calculate mean time difference
    return dt

# Iterate over each load and process the corresponding files
average_peak_to_peak_powers1 = []
average_peak_to_peak_powers2 = []

for load in loads:
    peak_to_peak_powers1_list = []
    peak_to_peak_powers2_list = []

    for file_path in file_paths[load]:
        # Load the data from the CSV file
        data = pd.read_csv(file_path)

        # Extract the relevant columns
        timestamps = data['timestamp'].values
        foot_contact1 = data['foot_contact 1'].values
        power1 = data['torque 1'].values
        power2 = data['torque 3'].values

        # Compute average dt from timestamps
        dt = compute_average_dt(timestamps)

        # Compute peak-to-peak power for each period
        avg_peak_to_peak_power1 = compute_peak_to_peak_power(timestamps, foot_contact1, power1)
        avg_peak_to_peak_power2 = compute_peak_to_peak_power(timestamps, foot_contact1, power2)

        peak_to_peak_powers1_list.append(avg_peak_to_peak_power1)
        peak_to_peak_powers2_list.append(avg_peak_to_peak_power2)

    # Compute the overall average peak-to-peak power for the current load
    overall_avg_peak_to_peak_power1 = np.nanmean(peak_to_peak_powers1_list)
    overall_avg_peak_to_peak_power2 = np.nanmean(peak_to_peak_powers2_list)
    
    average_peak_to_peak_powers1.append(overall_avg_peak_to_peak_power1)
    average_peak_to_peak_powers2.append(overall_avg_peak_to_peak_power2)

# Plotting the average peak-to-peak power vs load using scatter plot
plt.figure(figsize=(6, 6))
plt.scatter(loads, average_peak_to_peak_powers1, color='red', marker='x', label='Peak-to-Peak Torque Synergy 1', linewidth=4)
plt.scatter(loads, average_peak_to_peak_powers2, color='gray', marker='p', label='Peak-to-Peak Torque Synergy 2')
plt.xlabel('Load [kg]', fontsize=12)
plt.ylabel('Average Peak-to-Peak Torque [Nm]', fontsize=12)
plt.title('Average Peak-to-Peak Torque vs Load', fontsize=12)
plt.legend()

# Set x-ticks to increments of 0.25 kg
plt.xticks(loads, [f'{load:.2f}' for load in loads])

plt.show()
