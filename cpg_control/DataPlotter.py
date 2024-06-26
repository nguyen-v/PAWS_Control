import matplotlib.pyplot as plt
from matplotlib import animation
import csv
from multiprocessing import Process

class DataPlotter:
    def __init__(self, csv_file):
        self.processes = []
        self.csv_file = csv_file
    
    def create_process(self, numeric_fields, boolean_fields, title, max_data_points, update_interval):
        args = (self.csv_file, numeric_fields, boolean_fields, title, max_data_points, update_interval)
        p = Process(target=plot_live_data, args=args)
        self.processes.append(p)
        p.start()

    def terminate_processes(self):
        for p in self.processes:
            p.terminate()
            p.join()

def plot_live_data(csv_file, numeric_fields, boolean_fields, title, max_data_points=100, update_interval=20):
    num_numeric_fields = len(numeric_fields)
    num_boolean_fields = 0
    if boolean_fields is not None:
        num_boolean_fields = len(boolean_fields)
    colors = ['blue', 'red', 'green', 'yellow', 'purple']

    def update_plot(frame):
        nonlocal x_data, numeric_data, boolean_data, lines, fill_between_objs

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                x_data.append(float(row['timestamp']))
                for i in range(num_numeric_fields):
                    field_name = numeric_fields[i]
                    if field_name in row:
                        try:
                            numeric_data[i].append(float(row[field_name]))
                        except ValueError:
                            numeric_data[i].append(None)
                    else:
                        numeric_data[i].append(None)
                for i in range(num_boolean_fields):
                    field_name = boolean_fields[i]
                    if field_name in row:
                        value = row[field_name].lower()
                        if value == 'true':
                            boolean_data[i].append(1)
                        elif value == 'false':
                            boolean_data[i].append(0)
                        else:
                            boolean_data[i].append(None)
                    else:
                        boolean_data[i].append(None)

        if len(x_data) > max_data_points:
            x_data = x_data[-max_data_points:]
            for i in range(num_numeric_fields):
                numeric_data[i] = numeric_data[i][-max_data_points:]
            for i in range(num_boolean_fields):
                boolean_data[i] = boolean_data[i][-max_data_points:]

        for i in range(num_numeric_fields):
            lines[i].set_data(x_data, numeric_data[i])

        for i in range(num_boolean_fields):
            if fill_between_objs[i] is not None:
                fill_between_objs[i].remove()
            fill_between_objs[i] = ax.fill_between(x_data, 0, 1, where=[val == 1 for val in boolean_data[i]], 
                                                   color=colors[i % len(colors)], alpha=0.15, transform=ax.get_xaxis_transform())

        numeric_values = [data for sublist in numeric_data for data in sublist if data is not None]
        if numeric_values:
            min_y = min(numeric_values)
            max_y = max(numeric_values)
            ax.set_ylim(min_y - 0.5, max_y + 0.5)
        else:
            ax.set_ylim(0, 1)

        ax.set_xlim(min(x_data), max(x_data))

        return lines + fill_between_objs

    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Values")

    x_data = []
    numeric_data = [[] for _ in range(num_numeric_fields)]
    boolean_data = [[] for _ in range(num_boolean_fields)]
    lines = [ax.plot([], [], label=numeric_fields[i])[0] for i in range(num_numeric_fields)]
    fill_between_objs = [None] * num_boolean_fields

    # Create handles for legend
    handles = lines[:]
    for i in range(num_boolean_fields):
        boolean_patch = plt.Line2D([0], [0], color=colors[i % len(colors)], lw=4, alpha=0.15)
        handles.append(boolean_patch)
    if boolean_fields is not None:
        labels = numeric_fields + boolean_fields
    else:
        labels = numeric_fields

    ax.legend(handles, labels, loc='upper right')

    ani = animation.FuncAnimation(fig, update_plot, interval=update_interval)
    plt.show()
