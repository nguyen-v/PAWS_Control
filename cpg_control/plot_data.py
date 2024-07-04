import pandas as pd
import matplotlib.pyplot as plt

def plot_positions(data, fields_to_plot, boolean_fields, title, y_label):
    # Create a new figure for the plot
    plt.figure(figsize=(12, 8))
    
    for field in fields_to_plot:
        plt.plot(data['timestamp'], data[field], label=field)
    
    # Plot the boolean fields as shaded areas
    colors = ['blue', 'red', 'green', 'yellow', 'purple']
    color_idx = 0
    for boolean_field in boolean_fields:
        bool_series = data[boolean_field].astype(bool)
        plt.fill_between(data['timestamp'], 0, 1, where=bool_series, 
                         color=colors[color_idx], alpha=0.15, transform=plt.gca().get_xaxis_transform(), label=boolean_field)
        color_idx = (color_idx + 1) % len(colors)
    
    plt.xlabel('Timestamp [s]')
    plt.ylabel(y_label)
    plt.legend()
    plt.title(title)

# File path to the CSV file
file_path = './PASSIVE_LONGER_3KMH_2.csv'

# Read the CSV file once
data = pd.read_csv(file_path)

# Create plot for positions
# plot_positions(data, ['position 1', 'position 3'], ['foot_contact 1', 'foot_contact 3'], 'Positions and Foot Contacts Over Time', 'tr')

# # Create plot for velocities
# plot_positions(data, ['velocity 1', 'velocity 3'], ['foot_contact 1', 'foot_contact 3'], 'Velocities and Foot Contacts Over Time', 'tr/s')

# # Create plot for power
# plot_positions(data, ['power 1', 'power 3'], ['foot_contact 1', 'foot_contact 3'], 'Power and Foot Contacts Over Time', 'W')

# Create plot for pressures
plot_positions(data, ['pressure 1', 'pressure 3'], ['foot_contact 1', 'foot_contact 3'], 'Pressures and Foot Contacts Over Time', 'Analog readings')

# Show all plots at once
plt.show()
