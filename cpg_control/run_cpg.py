import numpy as np
import asyncio
import moteus

from HopfNetwork import HopfNetwork

TIMESTEP = 0.002
PRESSURE_THRESHOLD = 104
REDUCTION_RATIO = 5

async def main():

    cpg = HopfNetwork(dt=TIMESTEP,
                  gait="TROT",
                  omega_stance=5*2*np.pi,
                  omega_swing=2*2*np.pi,
                  amp_swing=REDUCTION_RATIO*np.pi/8,
                  amp_stance=REDUCTION_RATIO*np.pi/8,
                  coupling_strength=1)

    qr = moteus.QueryResolution()
    qr._extra = {
        moteus.Register.MOTOR_TEMPERATURE : moteus.F32
        }
    
    # create a list of 4 c moteus controllers
    print("Creating controllers...")
    c = []
    
    for i in range(4):
        c.append(moteus.Controller(id=i+1, query_resolution = qr))
        await c[i].set_stop()

    # create array of two bools to keep track of foot contact
    foot_contact = np.array([False, False, False , False])

    cmd_angle = np.zeros(4)
    pressure = np.zeros(4)

    while True:

        for i in range(4):
            if pressure[i] > PRESSURE_THRESHOLD:
                foot_contact[i] = True
            else:
                foot_contact[i] = False  

            # print(f"Pressure {i+1}: {pressure[i]:.2f}, Foot contact {i}: {foot_contact[i]}")
        cmd_angle = cpg.update(foot_contact)/(2*np.pi)
        # print cmd_angle
        print(f"Commanded angle: {cmd_angle}")

        for i in range(4):
            if (i == 0 or i == 2):
                state = await c[i].set_position(
                    position=cmd_angle[i], 
                    velocity=0,
                    accel_limit=30,
                    velocity_limit=20.0,
                    query=True)
                pressure[i] = state.values[moteus.Register.MOTOR_TEMPERATURE]

        await asyncio.sleep(TIMESTEP)

    
if __name__ == "__main__":
    asyncio.run(main())