import asyncio
import time
import moteus
from PAWS import PAWS
from DataLogger import DataLogger
from DataPlotter import DataPlotter
import numpy as np

TIMESTEP = 0.01
CONTROLLER_IDS = [1, 3]
MODE = "SINE"
LOG_DATA = False
PLOT_DATA = True
RECOVERY = False
TRN_TO_RAD = 2*np.pi

async def motor_control(logger, paws):
    try:
        while True:
            await paws.update(time.time())
            state, foot_contact = paws.get_state()

            # Log values
            logger.set_field("timestamp", time.time())
            for i in CONTROLLER_IDS:
                logger.set_field("position " + str(i), state[i-1].values[moteus.Register.POSITION]*TRN_TO_RAD)
                logger.set_field("command_position " + str(i), state[i-1].values[moteus.Register.COMMAND_POSITION]*TRN_TO_RAD)
                logger.set_field("velocity " + str(i), state[i-1].values[moteus.Register.VELOCITY]*TRN_TO_RAD)
                logger.set_field("torque " + str(i), state[i-1].values[moteus.Register.TORQUE])
                logger.set_field("power " + str(i), state[i-1].values[moteus.Register.POWER])
                logger.set_field("pressure " + str(i), state[i-1].values[moteus.Register.MOTOR_TEMPERATURE])
                logger.set_field("foot_contact " + str(i), foot_contact[i-1])

            # Update CSV file
            logger.write_line()

            await asyncio.sleep(TIMESTEP)
    except KeyboardInterrupt:
        print("Motor control task interrupted.")

async def main():
    # Create new PAWS object
    paws = PAWS(controller_ids=CONTROLLER_IDS, mode=MODE, recovery=RECOVERY, max_torque=3)
    await paws.create_controllers()
    await paws.set_zero_position()

    # Create new DataLogger object
    logger = DataLogger(MODE)

    # Add fields to the logger
    logger.add_field("timestamp")
    for i in CONTROLLER_IDS:
        logger.add_field("position " + str(i), decimals=4)
        logger.add_field("command_position " + str(i), decimals=4)
        logger.add_field("velocity " + str(i), decimals=4)
        logger.add_field("torque " + str(i), decimals=4)
        logger.add_field("power " + str(i), decimals=4)
        logger.add_field("pressure " + str(i), decimals=4)
        logger.add_field("foot_contact " + str(i))

    # Use default name for CSV file (date and time)
    logger.create_file()

    if PLOT_DATA:

        # Create plotter object
        plotter = DataPlotter(logger.get_file_name())

        # create process for position 1 and posistion 3
        plotter.create_process(["position 1", "position 3"], ["foot_contact 1", "foot_contact 3"], "Motor position", "Angle (rad)", 200, 20)

        # create process for torque 1 and torque 3
        plotter.create_process(["torque 1", "torque 3"], ["foot_contact 1", "foot_contact 3"], "Motor torque", "Torque (Nm)", 200, 20)

        # create process for command position 1 and command position 3
        plotter.create_process(["command_position 1", "command_position 3"], ["foot_contact 1", "foot_contact 3"], "Commanded position", "Angle (rad)", 200, 20)

        # create process for velocity 1 and velocity 3 
        plotter.create_process(["velocity 1", "velocity 3"], ["foot_contact 1", "foot_contact 3"], "Motor velocity", "Angular speed (rad/s)", 200, 20)

        # create process for pressure 1 and pressure 3 
        plotter.create_process(["pressure 1", "pressure 3"], ["foot_contact 1", "foot_contact 3"], "Foot pressure", "Analog readings (-)", 200, 20)

        # create process for pressure 1 and pressure 3 
        plotter.create_process(["power 1", "power 3"], ["foot_contact 1", "foot_contact 3"], "Motor power", "Power (W)", 200, 20)

    try:
        # Start motor control task
        motor_task = asyncio.create_task(motor_control(logger, paws))
        await motor_task

    except KeyboardInterrupt:
        print("Main task interrupted. Cleaning up...")

    finally:

        if PLOT_DATA:
            # Terminate the plotting process when motor control stops
            plotter.terminate_processes()

        # Delete CSV file if logging is disabled
        if not LOG_DATA:
            logger.delete_file()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
