import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# List of CSV files for different treadmill speeds
file_paths = ['PASSIVE_1_LONG.csv', 'PASSIVE_1.5_LONG.csv', 'PASSIVE_2_LONG.csv',
              'PASSIVE_3_LONG.csv']
speeds = [1, 1.5, 2, 3]  # Corresponding speeds in km/h

# Function to compute average position data across periods
def compute_average_positions(timestamps, foot_contact1, position1, position3, pressure1, pressure3, velocity1, velocity3):
    avg_position1 = []
    avg_position3 = []
    front_foot = []
    back_foot = []
    avg_velocity1 = []
    avg_velocity3 = []
    
    # Identify the transition points from False to True in foot_contact 1
    transitions = np.where((foot_contact1[:-1] == False) & (foot_contact1[1:] == True))[0]
    
    # List to store positions for each period
    periods_position1 = []
    periods_position3 = []
    
    for i in range(len(transitions)):
        start_index = transitions[i] - int(0.5 / 0.03)  # 0.5 seconds before transition
        
        if i < len(transitions) - 1:
            end_index = transitions[i + 1]
        else:
            end_index = len(timestamps) - 1
        
        period_positions1 = position1[start_index:end_index]
        period_positions3 = position3[start_index:end_index]
        
        periods_position1.append(period_positions1)
        periods_position3.append(period_positions3)
        
        # Determine footfall sequence for front foot (pressure 1)
        period_pressure1 = pressure1[start_index:end_index]
        front_foot_period = [1 if p > 102.5 else 0 for p in period_pressure1]
        front_foot.append(front_foot_period)
        
        # Determine footfall sequence for back foot (pressure 3)
        period_pressure3 = pressure3[start_index:end_index]
        back_foot_period = [1 if p > 104 else 0 for p in period_pressure3]
        back_foot.append(back_foot_period)
        
        # Calculate average velocity across periods
        avg_velocity1.append(np.mean(velocity1[start_index:end_index]))  # Compute average velocity 1
        avg_velocity3.append(np.mean(velocity3[start_index:end_index]))  # Compute average velocity 3
    
    # Find the maximum length of periods to align data
    max_length = max(len(periods_position1[i]) for i in range(len(periods_position1)))
    
    # Calculate average across all periods for each data point
    for j in range(max_length):
        avg_position1.append(np.mean([periods_position1[i][j] for i in range(len(periods_position1)) if j < len(periods_position1[i])]))
        avg_position3.append(np.mean([periods_position3[i][j] for i in range(len(periods_position3)) if j < len(periods_position3[i])]))
    
    return avg_position1, avg_position3, front_foot, back_foot, avg_velocity1, avg_velocity3

# Iterate over each file
fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)

for i, file_path in enumerate(file_paths):
    # Load the data from the CSV file
    data = pd.read_csv(file_path)
    
    # Extract the relevant columns
    timestamps = data['timestamp'].values
    foot_contact1 = data['foot_contact 1'].values
    position1 = data['position 1'].values
    position3 = data['position 3'].values
    pressure1 = data['pressure 1'].values
    pressure3 = data['pressure 3'].values
    velocity1 = data['velocity 1'].values
    velocity3 = data['velocity 3'].values
    
    # Compute average positions, footfall sequences, and velocities across periods
    avg_position1, avg_position3, front_foot, back_foot, avg_velocity1, avg_velocity3 = compute_average_positions(timestamps, foot_contact1, position1, position3, pressure1, pressure3, velocity1, velocity3)
    
    # Convert position 1 and position 3 to degrees and seconds
    avg_position1_deg = np.array(avg_position1) * (360 / 5)  # Assuming reduction ratio of 5
    avg_position3_deg = np.array(avg_position3) * (360 / 5)  # Assuming reduction ratio of 5
    periods = np.arange(len(avg_position1)) * 0.03  # Time in seconds (assuming each timestep is 0.03 seconds)
    
    # Crop data to x = 0 to 1
    mask = (periods >= 0) & (periods <= 1)
    periods_crop = periods[mask]
    avg_position1_deg_crop = avg_position1_deg[mask]
    avg_position3_deg_crop = avg_position3_deg[mask]
    
    # Plotting footfall sequences and average velocities on the same subplot
    axs[i].bar(periods_crop, front_foot[0][:len(periods_crop)], color='red', alpha=0.5, label='Front Foot')
    axs[i].bar(periods_crop, back_foot[0][:len(periods_crop)], bottom=-1, color='grey', alpha=0.5, label='Back Foot')
    axs[i].plot(periods_crop[:len(avg_velocity1)], avg_velocity1[:len(periods_crop)], color='blue', label='Average Velocity 1')
    axs[i].plot(periods_crop[:len(avg_velocity3)], avg_velocity3[:len(periods_crop)], color='green', label='Average Velocity 3')
    axs[i].set_title(f'Treadmill speed {speeds[i]} km/h', fontsize=14)
    axs[i].set_ylim(-1.2, 1.2)
    axs[i].set_yticks([-1, 0, 1])
    axs[i].legend(loc='upper left')

# Common X-axis label
fig.text(0.5, 0, 'Time [seconds]', ha='center', fontsize=12)

# Adjust layout
plt.tight_layout()
plt.show()
