import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression

# Function to process jump height data
def process_jump_height(file_path):
    jump_height_data = pd.read_csv(file_path)
    jump_height = jump_height_data.iloc[:, 28]
    jump_height_inverted = -jump_height
    threshold = (jump_height_inverted.min() + jump_height_inverted.max()) / 2
    base_height = 130
    crossings = (jump_height_inverted > threshold) & (jump_height_inverted.shift(1) <= threshold)
    crossing_indices = crossings[crossings].index
    jump_heights = []

    for i in range(len(crossing_indices) - 1):
        start_idx = crossing_indices[i]
        end_idx = crossing_indices[i + 1]
        max_height = jump_height_inverted[start_idx:end_idx].max()
        jump_heights.append(max_height - base_height)

    average_jump_height = sum(jump_heights) / len(jump_heights) if jump_heights else 0
    return average_jump_height

# Function to process motor controller data
def process_motor_data(file_path):
    motor_data = pd.read_csv(file_path)
    motor_data['timestamp'] = pd.to_numeric(motor_data['timestamp'])
    period_energies = []
    foot_contact = motor_data['foot_contact 1']
    transitions = (foot_contact.shift(1) == False) & (foot_contact == True)
    transition_indices = transitions[transitions].index

    def integrate_power(data, power_col, time_col):
        return np.trapz(data[power_col], x=data[time_col])

    for i in range(len(transition_indices) - 1):
        start_idx = transition_indices[i]
        end_idx = transition_indices[i + 1]
        period_data = motor_data.iloc[start_idx:end_idx]
        energy_1 = integrate_power(period_data, 'power 1', 'timestamp')
        energy_3 = integrate_power(period_data, 'power 3', 'timestamp')
        total_energy = energy_3
        period_energies.append(total_energy)

    average_energy = sum(period_energies) / len(period_energies) if period_energies else 0
    return average_energy

# Function to process a set of files
def process_file_set(file_set, jump_height_dir='./optitrack', motor_data_dir='./'):
    jump_heights = []
    energies = []
    for file_name in file_set:
        jump_height_file = os.path.join(jump_height_dir, file_name)
        motor_data_file = os.path.join(motor_data_dir, file_name)
        
        jump_height = process_jump_height(jump_height_file)
        energy = process_motor_data(motor_data_file)
        
        jump_heights.append(jump_height)
        energies.append(energy)
    
    return energies, jump_heights

# List of file sets
file_sets = [
    ['JUMP_0.1NM.csv', 'JUMP_0.2NM.csv', 'JUMP_0.3NM.csv', 'JUMP_0.4NM.csv', 'JUMP_0.5NM.csv', 'JUMP_0.6NM.csv'],
    ['JUMP2_0.1NM.csv', 'JUMP2_0.2NM.csv', 'JUMP2_0.3NM.csv', 'JUMP2_0.4NM.csv', 'JUMP2_0.5NM.csv', 'JUMP2_0.6NM.csv'],
    ['JUMP3_0.1NM.csv', 'JUMP3_0.2NM.csv', 'JUMP3_0.3NM.csv', 'JUMP3_0.4NM.csv', 'JUMP3_0.5NM.csv', 'JUMP3_0.6NM.csv'],
    ['SINE_0.1NM.csv', 'SINE_0.2NM.csv', 'SINE_0.3NM.csv', 'SINE_0.4NM.csv', 'SINE_0.5NM.csv', 'SINE_0.6NM.csv'],
    # ['AMPLIFY_CUSTOM_0.3NM.csv', 'AMPLIFY_CUSTOM_0.4NM.csv', 'AMPLIFY_CUSTOM_0.5NM.csv', 'AMPLIFY_CUSTOM_0.6NM.csv'],
    ['PASSIVE_JUMP_BENCHMARK.csv']
]

# Colors and markers for each file set
colors = ['brown', 'red', 'orange', 'gray', 'black', 'purple']
markers = ['o', 's', 'D', '^', 'v', '*']

# Custom legends
legends = [
    'Normal jump',
    'Delayed jump',
    'Crouching jump',
    'Amplified sinusoidal',
    # 'Amplified reflex-based',
    'Passive'
]

# Plot the results
plt.figure(figsize=(9, 9))

# Compute global x-axis range for full extension of linear fits
all_energies = [energy for file_set in file_sets for energy in process_file_set(file_set)[0]]
x_min, x_max = min(all_energies), max(all_energies)
x_range = np.linspace(x_min, x_max, 100).reshape(-1, 1)  # Adding some margin to the range

for idx, (file_set, color, marker, legend) in enumerate(zip(file_sets, colors, markers, legends)):
    energies, jump_heights = process_file_set(file_set)
    x = np.array(energies).reshape(-1, 1)
    y = np.array(jump_heights)
    
    if len(x) > 1 and len(y) > 1:
        model = LinearRegression()
        model.fit(x, y)
        y_pred = model.predict(x_range)  # Use global x_range for full extension
        plt.plot(x_range, y_pred, color=color, linestyle='--', alpha=0.7)  # Linear fit

    if idx == 4:  # Passive dataset (index 5)
        plt.scatter(energies, jump_heights, color=color, marker=marker, label=legend, s=50)
        plt.axhline(y=np.mean(jump_heights), color=color, linestyle='--', alpha=0.7)  # Horizontal line
    else:
        plt.scatter(energies, jump_heights, color=color, marker=marker, label=legend, s=50)

plt.xlabel('Energy [J]', fontsize=12)
plt.ylabel('Jump Height [mm]', fontsize=12)
plt.title('Jump Height vs Energy', fontsize=16)
plt.legend(fontsize = 12)
# plt.grid(True)
plt.show()
