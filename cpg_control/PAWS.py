import moteus
import asyncio
import numpy as np

class PAWS:
    def __init__(self,
                 mode = "AMPLIFY",
                 accel_limit = 30,
                 velocity_limit = 20,
                 max_torque = 3,
                 controller_ids = np.array([1, 2, 3, 4])
                 ):
        self.num_controllers = 4
        self.foot_contact_thr = np.array([104, 104, 102, 104])
        self.foot_contact = np.array([False, False, False, False])
        self.pressure = np.zeros(self.num_controllers)
        self.power = np.zeros(self.num_controllers)
        self.mode = mode
        self.accel_limit = accel_limit
        self.velocity_limit = velocity_limit
        self.max_torque = max_torque
        self.controller_ids = controller_ids
        self.LUT = np.zeros((2**self.num_controllers, self.num_controllers))
        if self.mode != "PASSIVE":
            self.set_LUT()
        self.states = [None, None, None, None]

    # Set LUT
    # Rows represent the foot contact state and columns represent the controllers
    # Each entry in the LUT is the position command for the corresponding controller
    # Order is FR, FL, RR, RL
    def set_LUT(self):
        if self.mode == "AMPLIFY":              

            #                    Commanded positions   Foot contact states
            #                    (Synergy space)
            #                    -------------------   -------------------
            #                     FR   FL   RR   RL     FR   FL   RR   RL

            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,   0,   0,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [1,   0,  -1,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [1,   0,   1,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        else:
            print("Mode not supported. Not setting LUT.")

    # Get index for LUT based on foot contact.
    def get_LUT_index(self):
        idx = 0
        for i in range(self.num_controllers):
            idx += self.foot_contact[i]*2**(self.num_controllers-i-1)
        return idx

    # Create and initialize the controllers with the extra fields
    async def create_controllers(self):
        self.qr = moteus.QueryResolution()
        self.qr._extra = {
            moteus.Register.MOTOR_TEMPERATURE: moteus.F32,
            moteus.Register.POSITION: moteus.F32,
            moteus.Register.VELOCITY: moteus.F32,
            moteus.Register.TORQUE: moteus.F32,
            # used for power estimation
            moteus.Register.Q_CURRENT: moteus.F32,
            moteus.Register.D_CURRENT: moteus.F32,
            moteus.Register.VOLTAGEDQ_D: moteus.F32,
            moteus.Register.VOLTAGEDQ_Q: moteus.F32
        }

        # Create a list of moteus controllers
        self.controllers = [moteus.Controller(id=i + 1, query_resolution=self.qr) for i in range(self.num_controllers)]

        # Ensure all controllers are stopped
        for controller in self.controllers:
            await controller.set_stop()

    # Set zero position for all controllers
    async def set_zero_position(self):
        for i in self.controller_ids:
            await self.controllers[i-1].set_output_nearest(position=0)

    # Convert pressure values to foot contact boolean values
    def update_foot_contact(self):
        for i in self.controller_ids:
            if self.pressure[i-1] > self.foot_contact_thr[i-1]:
                self.foot_contact[i-1] = True
            else:
                self.foot_contact[i-1] = False

    # Return commands for the controllers according to selected mode
    def get_commands(self):
        if self.mode == "PASSIVE":
            return np.zeros(self.num_controllers), 0
        if self.mode == "AMPLIFY":
            return self.LUT[self.get_LUT_index()], self.max_torque
        else:
            print("Mode not supported. Not setting commands.")
            return np.zeros(self.num_controllers), 0
    
    def get_state(self):
        return self.states, self.power, self.foot_contact

    # Send commands to the controllers
    async def update(self):

        # Update foot contact
        self.update_foot_contact()

        for i in self.controller_ids:
                
            # Get commands
            position, max_torque = self.get_commands()

            if position[i-1] == 0:
                max_torque = 0
            else:
                await self.controllers[i-1].set_recapture_position_velocity()

            self.states[i-1] = await self.controllers[i-1].set_position(
                position=position[i-1],
                velocity=0,
                velocity_limit=self.velocity_limit,
                accel_limit=self.accel_limit,
                maximum_torque=max_torque,
                query=True
            )

            # Update pressure values. Analog pressure sensor is connected to motor temperature input
            self.pressure[i-1] = self.states[i-1].values[moteus.Register.MOTOR_TEMPERATURE]

            # Update power values in [W]
            self.power[i-1] = 1.5*(self.states[i-1].values[moteus.Register.Q_CURRENT]
                                *self.states[i-1].values[moteus.Register.VOLTAGEDQ_Q] 
                                + self.states[i-1].values[moteus.Register.D_CURRENT]
                                *self.states[i-1].values[moteus.Register.VOLTAGEDQ_D])
            # print(self.states[i-1].values[moteus.Register.VOLTAGEDQ_Q])



        
        