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

def plot_live_data(csv_file, field_name):
    # Function to plot live data from CSV file
    def update_plot(frame):
        nonlocal x_data, y_data, sc

        # Read CSV and filter data for the last 10 seconds
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = float(row['timestamp'])
                if x_data and timestamp >= max(0, x_data[-1] - 10):
                    x_data.append(timestamp)
                    y_data.append(float(row[field_name]))
                elif not x_data:
                    x_data.append(timestamp)
                    y_data.append(float(row[field_name]))

        # Update scatter plot
        sc.set_offsets(np.c_[x_data[-int(10/TIMESTEP):], y_data[-int(10/TIMESTEP):]])
        ax.relim()
        ax.autoscale_view()
        return sc,


    # Initialize plot
    fig, ax = plt.subplots()
    ax.set_title(f"Live Plot: {field_name}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(field_name)

    x_data, y_data = [], []
    sc = ax.scatter(x_data, y_data)

    # Animate plot
    ani = animation.FuncAnimation(fig, update_plot, interval=100)
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
        logger.add_field("power " + str(i), decimals=8)
        logger.add_field("pressure " + str(i), decimals=4)
        logger.add_field("foot_contact " + str(i))

    # Use default name for CSV file (date and time)
    logger.create_file()

    # Start live plotting process
    plot_process = Process(target=plot_live_data, args=(logger.get_file_name(), "position 1"))  # Adjust field_name as needed
    plot_process.start()

    try:
        # Start motor control task
        motor_task = asyncio.create_task(motor_control(logger, paws))
        await motor_task
    except KeyboardInterrupt:
        print("Main task interrupted. Cleaning up...")
    finally:
        # Terminate the plotting process when motor control stops
        plot_process.terminate()
        plot_process.join()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
