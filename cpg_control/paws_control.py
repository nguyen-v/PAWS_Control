import asyncio
import time
import moteus
from PAWS import PAWS
from DataLogger import DataLogger
from DataPlotter import DataPlotter

TIMESTEP = 0.02
CONTROLLER_IDS = [1, 3]
MODE = "PASSIVE"

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

async def main():
    # Create new PAWS object
    paws = PAWS(controller_ids=CONTROLLER_IDS, mode=MODE, max_torque=3)
    await paws.create_controllers()
    await paws.set_zero_position()

    # Create new DataLogger object
    logger = DataLogger(MODE)

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

    # Create plotter object
    plotter = DataPlotter(logger.get_file_name())

    # create process for position 1 and posistion 3
    plotter.create_process(["position 1", "position 3", "foot_contact 1", "foot_contact 3"], "Position (trn)", 200, 20)

    # create process for velocity 1 and velocity 3 
    plotter.create_process(["velocity 1", "velocity 3", "foot_contact 1", "foot_contact 3"], "Velocity (trn/s)", 200, 20)

    try:
        # Start motor control task
        motor_task = asyncio.create_task(motor_control(logger, paws))
        await motor_task

    except KeyboardInterrupt:
        print("Main task interrupted. Cleaning up...")

    finally:
        # Terminate the plotting process when motor control stops
        plotter.terminate_processes()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
