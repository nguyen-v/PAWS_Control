import asyncio
import time
import csv
import numpy as np
import moteus
from multiprocessing import Process, Queue
import matplotlib.pyplot as plt
from matplotlib import animation  # Import animation module
from PAWS import PAWS
from DataLogger import DataLogger

TIMESTEP = 0.02
CONTROLLER_IDS = [1, 3]

async def motor_control(logger, paws):
    try:
        while True:
            await paws.update()
            state, power, foot_contact = paws.get_state()

            # Log values
            logger.set_field("timestamp", time.time())
            for i in CONTROLLER_IDS:
                logger.set_field("position " + str(i), state[i-1].values[moteus.Register.POSITION])
                logger.set_field("velocity " + str(i), state[i-1].values[moteus.Register.VELOCITY])
                logger.set_field("torque " + str(i), state[i-1].values[moteus.Register.TORQUE])
                logger.set_field("power " + str(i), power[i-1])
                logger.set_field("pressure " + str(i), state[i-1].values[moteus.Register.MOTOR_TEMPERATURE])
                logger.set_field("foot_contact " + str(i), foot_contact[i-1])

            # Update CSV file
            logger.write_line()

            await asyncio.sleep(TIMESTEP)
    except KeyboardInterrupt:
        print("Motor control task interrupted.")

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


async def main():
    # Create new PAWS object
    paws = PAWS(controller_ids=CONTROLLER_IDS, mode="AMPLIFY", max_torque=3)
    await paws.create_controllers()
    await paws.set_zero_position()

    # Create new DataLogger object
    logger = DataLogger()

    # Add fields to the logger
    logger.add_field("timestamp")
    for i in CONTROLLER_IDS:
        logger.add_field("position " + str(i), decimals=4)
        logger.add_field("velocity " + str(i), decimals=4)
        logger.add_field("torque " + str(i), decimals=4)
        logger.add_field("power " + str(i), decimals=4)
        logger.add_field("pressure " + str(i), decimals=4)
        logger.add_field("foot_contact " + str(i))

    # Use default name for CSV file (date and time)
    logger.create_file()

    # Start live plotting process for position 1 and position 3
    plot_pos = Process(target=plot_live_data, args=(logger.get_file_name(), ["position 1", "position 3", "foot_contact 1", "foot_contact 3"], "Position (trn)", 200, 20))
    plot_pos.start()

    plot_vel = Process(target=plot_live_data, args=(logger.get_file_name(), ["velocity 1", "velocity 3", "foot_contact 1", "foot_contact 3"], "Velocity (trn/s)", 200, 20))
    plot_vel.start()
    



    try:
        # Start motor control task
        motor_task = asyncio.create_task(motor_control(logger, paws))
        await motor_task
    except KeyboardInterrupt:
        print("Main task interrupted. Cleaning up...")
    finally:
        # Terminate the plotting process when motor control stops
        plot_pos.terminate()
        plot_pos.join()

        plot_vel.terminate()
        plot_vel.join()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
