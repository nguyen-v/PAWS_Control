import moteus
import asyncio
import numpy as np
from HopfNetwork import HopfNetwork
from SineNetwork import SineNetwork

LUT_MODES = ["AMPLIFY", "AMPLIFY_FROM_DATA", "AMPLIFY_SPEED", "AMPLIFY_CUSTOM", "JUMP", "JUMP2", "JUMP3", "CUSTOM", "LOAD", "PERTURBATION", "PERTURBATION_LOAD"]

class PAWS:
    def __init__(self,
                 mode = "AMPLIFY",
                 recovery = False,
                 accel_limit = 30,
                 velocity_limit = 20,
                 max_torque = 3,
                 controller_ids = np.array([1, 2, 3, 4]),
                 once = False,
                 initial_jumps = 0,
                 sync_pressure = True,
                 period = 1
                 ):
        self.num_controllers = 4
        self.foot_contact_thr = np.array([103, 104, 103.5, 104])
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
        self.jump_counts = 0
        self.once = once
        self.initial_jumps = initial_jumps
        if self.mode in LUT_MODES:
            self.set_LUT()
        if self.mode == "CPG":
            self.hopf = HopfNetwork()
        if self.mode == "SINE":
            self.sine = SineNetwork(sync_pressure=sync_pressure, period=period)
        self.states = [None, None, None, None]

    # Set LUT
    # Rows represent the foot contact state and columns represent the controllers
    # Each entry in the LUT is the position command for the corresponding controller
    # Order is FR, FL, RR, RL
    def set_LUT(self):
        print("Setting LUT for mode: ", self.mode)
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
            # self.LUT = np.array([[0,   0,   0,   0],  # 0    0    0    0
            #                      [0,   0,   0,   0],  # 0    0    0    1
            #                      [1,   0,   -1,   0],  # 0    0    1    0
            #                       # -1  -1: RR hits ground
            #                       # -1   0: unregular gait, fails easily
            #                       # -1   1: RR folds when in contact -> BAD
            #                       # 0    -1: better
            #                       # 0    1: RR folds when hitting the ground, which acts as a spring (in a bad way)
            #                       # 1   -1: bounding
            #                       # 1   0: no significant changes
            #                       # 1   1: RR folds when in contact -> BAD
            #                      [0,   0,   0,   0],  # 0    0    1    1
            #                      [0,   0,   0,   0],  # 0    1    0    0
            #                      [0,   0,   0,   0],  # 0    1    0    1
            #                      [0,   0,   0,   0],  # 0    1    1    0
            #                      [0,   0,   0,   0],  # 0    1    1    1
            #                      [-1,   0,   0,   0],  # 1    0    0    0  
            #                      # -1 -1: high jumps increasingly higher
            #                      # -1  0: RR lifts higher -> GOOD
            #                      # -1  1: RR lifts higher but fails
            #                      #  0  -1: JUMPS
            #                      #  0  1: RR hits ground
            #                      #  1 -1: FR exerts more force on the ground, jumps a bit higher. RR lifts higher by pushing harder -> JUMPS
            #                      #  1  0: FR exerts more force on the ground, jumps a bit higher
            #                      #  1  1: RR hits ground
            #                      [0,   0,   0,   0],  # 1    0    0    1
            #                      [1,   0,   -1,   0],  # 1    0    1    0 
            #                      # -1 -1: brings RR faster but hits ground ?
            #                      # -1  0  brings RR faster but hits ground
            #                      # -1  1  brings RR faster but hits ground
            #                      #  0  -1 
            #                      #  0  1  no improvement
            #                      # 1  -1  better
            #                      # 1   0  better but no improvement on RR
            #                      # 1   1  RR hits ground
            #                      [0,   0,   0,   0],  # 1    0    1    1
            #                      [0,   0,   0,   0],  # 1    1    0    0
            #                      [0,   0,   0,   0],  # 1    1    0    1
            #                      [0,   0,   0,   0],  # 1    1    1    0
            #                      [0,   0,   0,   0]]) # 1    1    1    1
            # similar to sine
            self.LUT = np.array([
                                [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [-1,   0,   -0.5,   0],  # 0    0    1    0
                                  # -1  -1:both feet move away from center when hitting RR -> BAD
                                  # -1   0: both feet move away from center when hitting RR, and no force on front knee -> BAD
                                  # -1   1: Crouches on contact, looks like the start of a jump
                                  # 0    -1: Crouches on contact with both feet straight w.r.t. previous joint
                                  # 0    1: RR folds when hitting the ground, which hits the ground
                                  # 1   -1: bounding
                                  # 1   0: no significant changes
                                  # 1   1: RR folds when in contact -> BAD
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [-1,   0,   0.5,   0],  # 1    0    0    0  
                                 # -1 -1: high jumps increasingly higher
                                 # -1  0: RR lifts higher -> GOOD
                                 # -1  1: RR lifts higher but fails
                                 #  0  -1: JUMPS
                                 #  0  1: RR hits ground
                                 #  1 -1: FR exerts more force on the ground, jumps a bit higher. RR lifts higher by pushing harder -> JUMPS
                                 #  1  0: FR exerts more force on the ground, jumps a bit higher
                                 #  1  1: RR hits ground
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [-1,   0,   0.5,   0],  # 1    0    1    0 
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
                        # self.LUT = np.array([
                        #         [0.01,   0,   0.01,   0],  # 0    0    0    0
                        #          [0,   0,   0,   0],  # 0    0    0    1
                        #          [-0.5,   0,   1,   0],  # 0    0    1    0
                        #          [0,   0,   0,   0],  # 0    0    1    1
                        #          [0,   0,   0,   0],  # 0    1    0    0
                        #          [0,   0,   0,   0],  # 0    1    0    1
                        #          [0,   0,   0,   0],  # 0    1    1    0
                        #          [0,   0,   0,   0],  # 0    1    1    1
                        #          [1,   0,   -0.5,   0],  # 1    0    0    0  
                        #          [0,   0,   0,   0],  # 1    0    0    1
                        #          [1,   0,   -0.5,   0],  # 1    0    1    0 
                        #          [0,   0,   0,   0],  # 1    0    1    1
                        #          [0,   0,   0,   0],  # 1    1    0    0
                        #          [0,   0,   0,   0],  # 1    1    0    1
                        #          [0,   0,   0,   0],  # 1    1    1    0
                        #          [0,   0,   0,   0]]) # 1    1    1    1
            self.LUT = np.array([
                                [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0.01,   0,   -2,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [0,   0,   -2,   0],  # 1    0    0    0  
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [0,   0,   -2,   0],  # 1    0    1    0 
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        elif self.mode == "JUMP2":
            self.LUT = np.array([
                                [0.7,   0,   -0.7,   0],  # 0    0    0    0
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,   0,   0,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [-1,   0,   -2,   0],  # 1    0    0    0  
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [-1,   0,   -2,   0],  # 1    0    1    0 
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        elif self.mode == "JUMP3":
            self.LUT = np.array([
                                [-.5,   0,   .5,   0], # for lower CoM on when hitting ground, which increases how long it can accelerate
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0.01,   0,   -2,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                 [0,   0,   -2,   0],  # 1    0    0    0  
                                 [0,   0,   0,   0],  # 1    0    0    1
                                 [0,   0,   -2,   0],  # 1    0    1    0 
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        elif self.mode == "CUSTOM":
            self.LUT = np.array([
                                # [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [0.01,   0,   0.1,   0], # new tendons
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,  0,  0,   0],  # 0    0    1    0 #new tendons
                                #  [-0.7,  0,  -0.7,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                #  [1,   0,   2,   0],  # 1    0    0    0
                                [1,   0,   -1,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                #  [-0.7,   0,   -0.7,   0],  # 1    0    1    0
                                [1,   0,   -1.5,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1         
        elif self.mode == "LOAD":
            self.LUT = np.array([
                                # [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [0.01,   0,   0.1,   0], # new tendons
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [0,  0,  0,   0],  # 0    0    1    0 #new tendons
                                #  [-0.7,  0,  -0.7,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                #  [1,   0,   2,   0],  # 1    0    0    0
                                [0,   0,   0,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                #  [-0.7,   0,   -0.7,   0],  # 1    0    1    0
                                [0,   0,   -1.5,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1      
        elif self.mode == "PERTURBATION":
            self.LUT = np.array([
                                # [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [-.5,   0,   .5,   0], # new tendons
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [1,  0,  0,   0],  # 0    0    1    0 # [1000] works too but the -1 helps the front leg
                                #  [-0.7,  0,  -0.7,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                #  [1,   0,   2,   0],  # 1    0    0    0
                                [0,   0,   0,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                #  [-0.7,   0,   -0.7,   0],  # 1    0    1    0
                                [0,   0,  0,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
            
        elif self.mode == "PERTURBATION_LOAD":
            self.LUT = np.array([
                                # [0.01,   0,   0.01,   0],  # 0    0    0    0
                                 [-.5,   0,   .5,   0], # new tendons
                                 [0,   0,   0,   0],  # 0    0    0    1
                                 [1,  0,  0,   0],  # 0    0    1    0 # [1000] works too but the -1 helps the front leg
                                #  [-0.7,  0,  -0.7,   0],  # 0    0    1    0
                                 [0,   0,   0,   0],  # 0    0    1    1
                                 [0,   0,   0,   0],  # 0    1    0    0
                                 [0,   0,   0,   0],  # 0    1    0    1
                                 [0,   0,   0,   0],  # 0    1    1    0
                                 [0,   0,   0,   0],  # 0    1    1    1
                                #  [1,   0,   2,   0],  # 1    0    0    0
                                [0,   0,   0,   0],  # 1    0    0    0
                                 [0,   0,   0,   0],  # 1    0    0    1
                                #  [-0.7,   0,   -0.7,   0],  # 1    0    1    0
                                [0,   0,  -1,   0],  # 1    0    1    0
                                 [0,   0,   0,   0],  # 1    0    1    1
                                 [0,   0,   0,   0],  # 1    1    0    0
                                 [0,   0,   0,   0],  # 1    1    0    1
                                 [0,   0,   0,   0],  # 1    1    1    0
                                 [0,   0,   0,   0]]) # 1    1    1    1
        else:
            print("Mode not supported. Not setting LUT.")
            pass

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
    async def update(self, timestamp):

        # Update foot contact
        prev_foot_contact = self.foot_contact.copy()
        self.update_foot_contact()

        if prev_foot_contact[0] == False and self.foot_contact[0] == True:
            self.jump_counts += 1
            print("Jump counts: ", self.jump_counts)

        for i in self.controller_ids:
            position = np.zeros(self.num_controllers)
            # Get commands
            if self.mode in LUT_MODES:
                position, max_torque = self.get_commands()
            elif self.mode == "CPG":
                position = self.hopf.update(self.foot_contact)
                max_torque = self.max_torque
            elif self.mode == "PASSIVE":
                position = [0, 0, 0, 0]
            elif self.mode == "SINE":
                position = self.sine.update(self.foot_contact, timestamp)
                max_torque = self.max_torque
            elif self.mode == "STIFF":
                position = [1, 0, 0.01, 0]
                max_torque = self.max_torque
            
            if position[i-1] == 0 and self.mode != "SINE":
                max_torque = 0

            else:
                await self.controllers[i-1].set_recapture_position_velocity()

            if self.jump_counts < self.initial_jumps:
                max_torque = 0

            if self.once:
                if self.jump_counts > self.initial_jumps + 3:
                    # print("going back to passive mode")
                    position = [0, 0, 0, 0]
                    max_torque = 0

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




        
        