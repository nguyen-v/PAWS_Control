import moteus
import asyncio
import numpy as np

LUT_MODES = ["AMPLIFY", "AMPLIFY_FROM_DATA", "AMPLIFY_SPEED", "AMPLIFY_CUSTOM", "JUMP", "CUSTOM"]

class PAWS:
    def __init__(self,
                 mode = "AMPLIFY",
                 recovery = False,
                 accel_limit = 30,
                 velocity_limit = 20,
                 max_torque = 3,
                 controller_ids = np.array([1, 2, 3, 4])
                 ):
        self.num_controllers = 4
        self.foot_contact_thr = np.array([104, 104, 102.2, 104])
        self.foot_contact = np.array([False, False, False, False])
        self.pressure = np.zeros(self.num_controllers)
        self.power = np.zeros(self.num_controllers)
        self.mode = mode
        self.recovery = recovery
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
                                 [-1,  0,  -1,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [1,   0,   1,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [0,   0,   1,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
            
        elif self.mode == "AMPLIFY_FROM_DATA":
            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,  0,  -1,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [1,   0,   1,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [1,   0,   0,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
            
        elif self.mode == "AMPLIFY_SPEED":
            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,  0,  -1,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [1,   0,   0.5,   0],  # 1    0    0    0 # 0.5 plays a major role in front feet stiffness
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [1,   0,   0.9,   0],  # 1    0    1    0 # 0.5 plays a major role in front feet stiffness
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
            
        elif self.mode == "AMPLIFY_CUSTOM":
            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [1,   0,   -1,   0],  # 0    0    1    0
                                  # -1  -1: RR hits ground
                                  # -1   0: unregular gait, fails easily
                                  # -1   1: RR folds when in contact -> BAD
                                  # 0    -1: better
                                  # 0    1: RR folds when hitting the ground, which acts as a spring (in a bad way)
                                  # 1   -1: bounding
                                  # 1   0: no significant changes
                                  # 1   1: RR folds when in contact -> BAD
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [-1,   0,   0,   0],  # 1    0    0    0  
                                 # -1 -1: high jumps increasingly higher
                                 # -1  0: RR lifts higher -> GOOD
                                 # -1  1: RR lifts higher but fails
                                 #  0  -1: JUMPS
                                 #  0  1: RR hits ground
                                 #  1 -1: FR exerts more force on the ground, jumps a bit higher. RR lifts higher by pushing harder -> JUMPS
                                 #  1  0: FR exerts more force on the ground, jumps a bit higher
                                 #  1  1: RR hits ground
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [1,   0,   -1,   0],  # 1    0    1    0 
                                 # -1 -1: brings RR faster but hits ground ?
                                 # -1  0  brings RR faster but hits ground
                                 # -1  1  brings RR faster but hits ground
                                 #  0  -1 
                                 #  0  1  no improvement
                                 # 1  -1  better
                                 # 1   0  better but no improvement on RR
                                 # 1   1  RR hits ground
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        
        elif self.mode == "JUMP":
            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [-1,  0,  -1,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [1,   0,   0,   0],  # 1    0    0    0  # 1 -1 BEFORE
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [0,   0,   -1,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        elif self.mode == "CUSTOM":
            self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [-1,  0,  -1,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [-1,   0,   -1,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [0,   0,   -1,   0],  # 1    0    1    0
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
            moteus.Register.COMMAND_POSITION: moteus.F32,
            moteus.Register.VELOCITY: moteus.F32,
            moteus.Register.TORQUE: moteus.F32,
            # used for power estimation
            moteus.Register.POWER: moteus.F32,
        }

        # Create a list of moteus controllers
        self.controllers = [moteus.Controller(id=i + 1, query_resolution=self.qr) for i in range(self.num_controllers)]

        # Ensure all controllers are stopped
        for controller in self.controllers:
            await controller.set_stop()

    # Set zero position for all controllers
    async def set_zero_position(self):
        for i in self.controller_ids:
            # await self.controllers[i-1].set_output_exact(position=0)
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
        elif self.mode in LUT_MODES:
            return self.LUT[self.get_LUT_index()], self.max_torque
        else:
            print("Mode not supported. Not setting commands.")
            return np.zeros(self.num_controllers), 0
    
    def get_state(self):
        return self.states, self.foot_contact

    # Send commands to the controllers
    async def update(self):

        # Update foot contact
        self.update_foot_contact()

        for i in self.controller_ids:
                
            # Get commands
            position, max_torque = self.get_commands()

            if self.recovery and (max_torque != 0 or self.mode == "PASSIVE"):
                try:
                    # print velocity and position
                    # print(self.states[3-1].values[moteus.Register.VELOCITY], self.states[3-1].values[moteus.Register.POSITION])
                    if abs(self.states[3-1].values[moteus.Register.VELOCITY]) < 0.1 and self.states[3-1].values[moteus.Register.POSITION] < -0.2 and self.foot_contact[3-1] == True and self.foot_contact[1-1] == False:
                        if i == 1:
                            position[i-1] = 3
                        # elif i == 3:
                        #     position[i-1] = -1.5
                        max_torque = 4
                        # elif i == 3:
                        print("Recovery mode activated.")
                except:
                    pass
            
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




        
        