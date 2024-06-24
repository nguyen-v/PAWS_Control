# live_plot.py

import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

class LivePlot:
    MAX_DATA_POINTS = 100  # Maximum number of data points to display
    UPDATE_INTERVAL = 20  # Update interval for animation in milliseconds

    def __init__(self, csv_file, field_name):
        self.csv_file = csv_file
        self.field_name = field_name
        self.fig, self.ax = plt.subplots()
        self.ax.set_title(f"Live Plot: {field_name}")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel(field_name)
        self.x_data, self.y_data = [], []
        self.line, = self.ax.plot([], [], marker='')  # Empty line plot with markers at data points
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=self.UPDATE_INTERVAL)

    def update_plot(self, frame):
        # Read new data from CSV file
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.x_data.append(float(row['timestamp']))
                self.y_data.append(float(row[self.field_name]))

        # Ensure only last MAX_DATA_POINTS are displayed
        if len(self.x_data) > self.MAX_DATA_POINTS:
            self.x_data = self.x_data[-self.MAX_DATA_POINTS:]
            self.y_data = self.y_data[-self.MAX_DATA_POINTS:]

        # Update line plot data
        self.line.set_data(self.x_data, self.y_data)

        # Update y-axis limits
        if self.y_data:
            self.ax.set_ylim(min(self.y_data), max(self.y_data))

        # Update x-axis limits
        if self.x_data:
            self.ax.set_xlim(min(self.x_data), max(self.x_data))

        return self.line,

    def start_animation(self):
        plt.show()
