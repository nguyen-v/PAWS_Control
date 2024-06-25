import matplotlib.pyplot as plt
from matplotlib import animation  # Import animation module
import csv
from multiprocessing import Process, Queue

class DataPlotter:
    def __init__(self, csv_file):  
        #create an empty list of processes\
        self.processes = []
        self.csv_file = csv_file
    
    def create_process(self, data_types, title, max_data_points, update_interval):
        # Arguments passed to the target function
        args = (self.csv_file, data_types, title, max_data_points, update_interval)
        # Create a process with the target self.plot_live_data and the given arguments
        p = Process(target=plot_live_data, args=args)
        # Append the process to the list of processes
        self.processes.append(p)
        # Start the process
        p.start()

    def terminate_processes(self):
        #terminate all processes
        for p in self.processes:
            p.terminate()
            p.join()

def plot_live_data(csv_file, field_names, y_label, max_data_points=100, update_interval=20):
    
    num_fields = len(field_names)

    def update_plot(frame):
        nonlocal x_data, y_data, lines

        # Read new data from CSV file
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                x_data.append(float(row['timestamp']))
                for i in range(num_fields):
                    field_name = field_names[i]
                    if field_name in row:
                        value = row[field_name]
                        if value.lower() == 'true':
                            # Assign a unique y-value based on the index of the boolean field
                            y_data[i].append(i + 1)  # Plot as i+1 if true (1-based indexing)
                        elif value.lower() == 'false':
                            y_data[i].append(None)  # Plot nothing if false
                        else:
                            try:
                                y_data[i].append(float(value))  # Plot numeric values as they are
                            except ValueError:
                                y_data[i].append(None)  # Plot nothing if value cannot be converted to float
                    else:
                        y_data[i].append(None)  # Plot nothing if field is missing

        # Ensure only last MAX_DATA_POINTS are displayed
        if len(x_data) > max_data_points:
            x_data = x_data[-max_data_points:]
            for i in range(num_fields):
                y_data[i] = y_data[i][-max_data_points:]

        # Update plot data
        for i in range(num_fields):
            lines[i].set_data(x_data, y_data[i])

        # Update y-axis limits
        # Flatten and filter out None values
        valid_data = [data for data in y_data if data is not None]
        flattened_data = [item for sublist in valid_data for item in sublist if item is not None]
        
        if flattened_data:
            min_y = min(flattened_data)
            max_y = max(flattened_data)
            ax.set_ylim(min_y - 0.5, max_y + 0.5)  # Adjust y-axis limits to create space between boolean values
        else:
            ax.set_ylim(0, 1)  # Default y-axis limits if no valid numeric data

        # Update x-axis limits
        ax.set_xlim(min(x_data), max(x_data))

        return lines

    # Initialize plot
    fig, ax = plt.subplots()
    ax.set_title(f"Live Plot: {', '.join(field_names)}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(y_label)

    x_data = []
    y_data = [[] for _ in range(num_fields)]
    lines = [ax.plot([], [], label=field_names[i], marker='')[0] for i in range(num_fields)]
    ax.legend(loc='upper right')  # Set legend to upper right corner

    # Animate plot
    ani = animation.FuncAnimation(fig, update_plot, interval=update_interval)
    plt.show()