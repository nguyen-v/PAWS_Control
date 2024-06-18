import numpy as np

# CPG in polar coordinates

class HopfNetwork:
    def __init__(self,
                 mu = 1**2,                 # intrisic amplitude
                 omega_swing = 5*2*np.pi,   # frequency in swing phase
                 omega_stance = 2*2*np.pi,  # frequency in stance phase
                 gait="TROT",               # gait pattern
                 alpha = 50,                # amplitude convergence factor
                 coupling_strength = 1,     # coupling strength (for coupling matrix)
                 couple = True,             # True if oscillators should be coupled
                 dt=0.001,                  # time step
                 amp_swing = np.pi/4,        # desired amplitude in swing phase
                 amp_stance = np.pi/4):      # desired amplitude in stance phase
    
        print("Creating Hopf Network...")
        self.mu = mu
        self.omega_swing = omega_swing
        self.omega_stance = omega_stance
        self.alpha = alpha
        self.coupling_strength = coupling_strength
        self.couple = couple
        self.dt = dt
        self.gait = gait
        self.set_gait(gait)
        self.des_swing = amp_swing
        self.des_stance = amp_stance

        # Construct state variables (CPG amplicudes r at row 0 and CPG phases theta at row 1)
        self.X = np.zeros((2, 4))
        self.X_dot = np.zeros((2, 4))

    def calculate_PHI(self, F_seq):
        PHI = np.zeros((4,4))
        for i in range(len(F_seq)):
            for j in range(len(F_seq)):
                PHI[i][j] = (F_seq[i] - F_seq[j])*2*np.pi
        return PHI
  
    def set_gait(self,gait):

        print("Setting gait to: ", gait)

        # F_seq_trot = np.array([0.5, 0, 0, 0.5])
        # F_seq_pace = np.array([0.5, 0, 0.5, 0])
        # F_seq_bound = np.array([0.5, 0.5, 0, 0])
        # F_seq_walk = np.array([0.5, 0, 0.25, 0.75])
        # REWRITE but with FR RR FL RL
        F_seq_trot = np.array([0.5, 0, 0.5, 0])
        F_seq_pace = np.array([0.5, 0, 0, 0.5])
        F_seq_bound = np.array([0.5, 0.5, 0, 0])
        F_seq_walk = np.array([0.5, 0, 0.25, 0.75])

        self.PHI_trot = self.calculate_PHI(F_seq_trot)
        self.PHI_pace = self.calculate_PHI(F_seq_pace)
        self.PHI_bound = self.calculate_PHI(F_seq_bound)
        self.PHI_walk = self.calculate_PHI(F_seq_walk)

        if gait == "TROT":
            self.PHI = self.PHI_trot
        elif gait == "PACE":
            self.PHI = self.PHI_pace
        elif gait == "BOUND":
            self.PHI = self.PHI_bound
        elif gait == "WALK":
            self.PHI = self.PHI_walk
        else:
            raise ValueError( gait + ' not implemented.')
        
    def update(self, foot_contact):
        self.integrate_hopf(foot_contact)
        cmd_angle = np.zeros(4)

        for i in range(4):
            if (foot_contact[i] == True):
                cmd_angle[i] = self.des_stance * np.sin(self.get_theta()[i])
            else:
                cmd_angle[i] = self.des_swing * np.sin(self.get_theta()[i])
        return cmd_angle


    # Get CPG amplitudes (r)
    def get_r(self):
        return self.X[0, :]
    
    # Get CPG phases (theta)
    def get_theta(self):
        return self.X[1, :]
    
    # Get CPG amplitudes derivatives
    def get_r_dot(self):
        return self.X_dot[0, :]
    
    # Get CPG phases derivatives
    def get_theta_dot(self):
        return self.X_dot[1, :]
    
    def integrate_hopf(self, foot_contact):
        X_dot = np.zeros((2, 4))

        for i in range(4):
            r, theta = self.get_r()[i], self.get_theta()[i]
            r_dot = self.alpha*(self.mu - r**2)*r

            if foot_contact[i]:
                theta_dot = self.omega_stance
            else:
                theta_dot = self.omega_swing
            
            if self.couple:
                theta_dot += self.coupling_strength*np.sum(self.get_r()*np.sin(self.get_theta() - theta - self.PHI[i, :]))

            X_dot[:, i] = [r_dot, theta_dot]

            # Integrate
            self.X = self.X + self.dt*X_dot
            self.X_dot = X_dot

            self.X[1, :] = np.mod(self.X[1, :], 2*np.pi)
