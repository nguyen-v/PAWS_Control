import asyncio
import moteus
import math

async def main():
    # Create a moteus controller instance for ID=1
    qr = moteus.QueryResolution()
    qr._extra = {
        moteus.Register.MOTOR_TEMPERATURE : moteus.F32
        }

    c = moteus.Controller(id=1, query_resolution = qr)

    # Clear any faults.
    await c.set_stop()
    pressure = 0
    
    while True:

        command_position = 0
        if pressure > 105:
            command_position = 1
        state = await c.set_position(
            position=command_position, 
            velocity=0.0,
            accel_limit=30.0,
            velocity_limit=15.0,
            query=True)
        pressure = state.values[moteus.Register.MOTOR_TEMPERATURE]
        position = state.values[moteus.Register.POSITION]

        print(f"Pressure: {pressure:.2f}, Position: {position:.2f}")

        # Determine the target position based on the temperature
        # if temperature > 100:
        #     target_position = 0.5
        # else:
        #     target_position = 0.0

        # Command the movement
        # await controller.set_position(position=target_position)

        # Wait for a short duration before the next iteration
        await asyncio.sleep(0.02)

if __name__ == "__main__":
    asyncio.run(main())
