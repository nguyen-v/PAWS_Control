import numpy as np

DEG_TO_TRN = 1/360
AMPLIFIER = 6

class SineNetwork:
    def __init__(self, amp=None, omega=None, theta=None, offset=None, t_off=None):
        if amp is None:
            # amp = [40*DEG_TO_TRN, 0*DEG_TO_TRN, 20*DEG_TO_TRN, 0*DEG_TO_TRN] # 1
            # amp = [AMPLIFIER*77*DEG_TO_TRN, 0*DEG_TO_TRN, AMPLIFIER*29*DEG_TO_TRN, 0*DEG_TO_TRN] # 1
            amp = [AMPLIFIER*29*DEG_TO_TRN, 0*DEG_TO_TRN, AMPLIFIER*30*DEG_TO_TRN, 0*DEG_TO_TRN] # 1

        if omega is None:
            # omega = [2*np.pi/(0.75), 2*np.pi/1, 2*np.pi/0.6, 2*np.pi/1] # 1
            omega = [2*np.pi/(1), 2*np.pi/1, 2*np.pi/0.7, 2*np.pi/1] # 1
        if theta is None:
            theta = [-np.pi/2, 0, -np.pi*0.05, 0] # 1.5

        if offset is None:
            # offset = [1.5/(2*np.pi), 0, -2/(2*np.pi), 0] # 1, 1.5
            offset = [-0.1, 0, 0, 0] # 1, 1.5

        if t_off is None:
            t_off = [0, 0, 0.03 ,0] #1

    # amp = [AMPLIFIER*29, AMPLIFIER*30] # 1

    # period = [1, 0.7]

    # omega = [2*np.pi/(period[0]), 2*np.pi/period[1]] # 1
        
    # theta = [-0.5*np.pi, -np.pi*0.05] # 1.5

    # offset = [1.5/(2*np.pi),-3/(2*np.pi)] # 1, 1.5

    # t_off = [0.145, 0.17] #1

        self.amp = amp
        self.omega = omega
        self.theta = theta
        self.offset = offset
        self.t_off = t_off
        self.t_start = None
        self.previous_foot_contact = False

    def update(self, foot_contact, timestamp):
        cmd_angle = np.zeros(4)

        if foot_contact[2] and not self.previous_foot_contact:
            self.t_start = timestamp

        self.previous_foot_contact = foot_contact[2]

        if self.t_start is not None:
            t = timestamp
            for i in range(4):
                period = (2 * np.pi) / self.omega[i] if self.omega[i] != 0 else np.inf
                if t - self.t_start < self.t_off[i]:
                    cmd_angle[i] = 0
                elif t - self.t_start <= period + self.t_off[i]:
                    cmd_angle[i] = (-self.amp[i] * np.sin(self.omega[i] * (t - self.t_start - self.t_off[i]) + self.theta[i])
                                    + self.amp[i] * np.sin(self.theta[i]))
                else:
                    cmd_angle[i] = 0

                cmd_angle[i] += self.offset[i]
        print(cmd_angle)
        return cmd_angle
