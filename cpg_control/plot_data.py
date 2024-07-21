import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RAD_TO_DEG = 180/np.pi

def plot_positions(data, fields_to_plot, boolean_fields, title, y_label, factor = 1):
    # Create a new figure for the plot
    plt.figure(figsize=(6, 4))
    
    colors_lines = ['red', 'black']
    color_lines_idx = 0

    for field in fields_to_plot:
        plt.plot(data['timestamp'], factor*data[field], label=field, color = colors_lines[color_lines_idx], linewidth = 2)
        color_lines_idx = (color_lines_idx + 1) % len(colors_lines)
    
    # Plot the boolean fields as shaded areas
    colors = ['red', 'gray', 'green', 'yellow', 'purple']
    color_idx = 0
    for boolean_field in boolean_fields:
        bool_series = data[boolean_field].astype(bool)
        plt.fill_between(data['timestamp'], 0, 1, where=bool_series, 
                         color=colors[color_idx], alpha=0.25, transform=plt.gca().get_xaxis_transform(), label=boolean_field)
        color_idx = (color_idx + 1) % len(colors)
    
    plt.xlabel('Timestamp [s]')
    plt.ylabel(y_label)
    # plt.xlim(data['timestamp'][640], data['timestamp'][750]) # LUT SINE
    # plt.xlim(data['timestamp'][340], data['timestamp'][425]) # SINE
    # plt.xlim(data['timestamp'][420], data['timestamp'][530]) # LOAD
    plt.legend(['Synergy 1', 'Synergy 2', 'Front foot contact', 'Rear foot contact'], loc='upper right')
    # plt.legend(['Motor command 1', 'Motor command 2', 'Front foot contact', 'Rear foot contact'], loc='upper right')
    plt.title(title)

# File path to the CSV file
file_path = './PASSIVE_FAIL_FRONT_LEG.csv'
# file_path = './SINE_1.5KMH.csv'

# Read the CSV file once
data = pd.read_csv(file_path)

# Create plot for positions
# plot_positions(data, ['position 1', 'position 3'], ['foot_contact 1', 'foot_contact 3'], 'Positions and Foot Contacts Over Time', 'Synergy [deg]', factor = RAD_TO_DEG)

plot_positions(data, ['command_position 1', 'command_position 3'], ['foot_contact 1', 'foot_contact 3'], 'Command Positions and Foot Contacts Over Time', 'Motor command [deg]', factor = RAD_TO_DEG)
plot_positions(data, ['position 1', 'position 3'], ['foot_contact 1', 'foot_contact 3'], 'Positions and Foot Contacts Over Time', 'Motor command [deg]', factor = RAD_TO_DEG)

# # Create plot for velocities
# plot_positions(data, ['velocity 1', 'velocity 3'], ['foot_contact 1', 'foot_contact 3'], 'Velocities and Foot Contacts Over Time', 'rad/s')

# # Create plot for power
plot_positions(data, ['power 1', 'power 3'], ['foot_contact 1', 'foot_contact 3'], 'Power and Foot Contacts Over Time', 'Motor power [W]')


plot_positions(data, ['pressure 1', 'pressure 3'], ['foot_contact 1', 'foot_contact 3'], 'Pressure and Foot Contacts Over Time', 'Motor power [W]')

# Create plot for pressures
# plot_positions(data, ['pressure 1', 'pressure 3'], ['foot_contact 1', 'foot_contact 3'], 'Pressures and Foot Contacts Over Time', 'Analog readings')

# Show all plots at once
plt.show()
