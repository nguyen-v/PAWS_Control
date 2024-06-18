import numpy as np
import asyncio
import moteus

from HopfNetwork import HopfNetwork

TIMESTEP = 0.02
PRESSURE_THRESHOLD = 104
REDUCTION_RATIO = 5

async def main():

    cpg = HopfNetwork(dt=TIMESTEP,
                  gait="TROT",
                  omega_stance=0.1*REDUCTION_RATIO*6*2*np.pi,
                  omega_swing=0.1*REDUCTION_RATIO*3*2*np.pi,
                  amp_swing=np.pi/4,
                  amp_stance=np.pi/4,
                  coupling_strength=0)

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
        cmd_angle = cpg.update(foot_contact)
        # print cmd_angle
        print(f"Commanded angle: {cmd_angle}")

        for i in range(2):
            state = await c[i].set_position(
                position=REDUCTION_RATIO*cmd_angle[i], 
                velocity=0,
                accel_limit=30,
                velocity_limit=20.0,
                query=True)
            pressure[i] = state.values[moteus.Register.MOTOR_TEMPERATURE]

        await asyncio.sleep(TIMESTEP)

    
if __name__ == "__main__":
    asyncio.run(main())