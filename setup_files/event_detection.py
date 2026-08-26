'''
for toe off, heel_strike, seat_off and peak_vetical_velocity :  Defining phases for the sit-to-walk movement 
                                                                Andy Kerr a and et.al https://doi.org/10.1016/j.clinbiomech.2003.12.012
for the gait intiation heel_off :                               Sit‑to‑walk strategy classification in healthy adults using hip and knee joint angles at gait initiation
                                                                https://doi.org/10.1038/s41598-023-43148-0
'''


import numpy as np
import pandas as pd
from setup_files.read_file import read_file
import numpy as np
from scipy.signal import savgol_filter

class gait:
    '''A class to detect gait events such as toe-off, heel strike, seat-off, and gait initiation based on vertical ground reaction force (GRF) data.
    The class takes in the GRF data file, body weight, and optional parameters for threshold and minimum width for event detection.'''

    def __init__(self, grf_file, body_weight, threshold = 20, min_width = 15):
        self.grf_data = read_file(grf_file, sep='\t')
        self.body_weight = body_weight
        self.threshold = threshold
        self.min_width = min_width


    def toe_off(self,forceplate = 2):
        '''Detects the frame of toe-off based on vertical ground reaction force (GRF) data.
        and return the frame in grf sampling rate.'''

        TO_idx = []
        i = 0
        min_width = self.min_width
        #checks for threshold and stays above for 15 frames to detect toe-off frame
        above = np.array(self.grf_data[f'ground_force_{forceplate}_vy'].values > self.threshold)
        # Find the indices where the condition changes from True to False (toe-off)
        while i < len(above) - min_width:
            # Toe Off: above → below threshold for >= min_width samples
            if above[i] and all(~above[i+1:i+1+min_width]):
                TO_idx.append(i + 1)
                i += min_width
                continue

            i += 1
        return TO_idx[0] if TO_idx else None  # Return the first toe-off index or None if not found
    
    def heel_strike(self,forceplate = 2):
        '''Detects the frame of heel strike based on vertical ground reaction force (GRF) data.
        and return the frame in grf sampling rate.'''

        HS_idx = []
        i = 0
        min_width = self.min_width
        #checks for threshold and stays above for 15 frames to detect heel strike frame
        above = np.array(self.grf_data[f'ground_force_{forceplate}_vy'].values > self.threshold)
        # Find the indices where the condition changes from True to False (heel strike)
        while i < len(above) - min_width:
            # Heel Strike: above → below threshold for >= min_width samples
            if not above[i] and all(above[i+1:i+1+min_width]):
                HS_idx.append(i + 1)
                i += min_width
                continue

            i += 1
        return HS_idx[0] if HS_idx else None  # Return the first heel strike index or None if not found

    def seat_off(self):
        '''Detects the frame of seat-off based on force plate data.
        and return the frame in force plate sampling rate.'''

        return int(np.where(self.grf_data['ground_force_1_vy'] == self.grf_data['ground_force_1_vy'].max())[0][0])

    def gait_intiation(self):
        '''Detects the frame of gait initiation based on force plate data.
        and return the frame in force plate sampling rate.'''

        #add toe off from marker position

        return int(np.where(self.grf_data['ground_force_1_vz'] > self.body_weight * 0.056)[0][0])
    
def gait_intiation_heel_off(marker_file_path,leg):
    '''
    Detects the frame of heel off during gait initiation based on marker data.
    It uses the vertical position of the heel marker to detect the frame where the heel starts to
    lift off the ground. The function applies a Savitzky-Golay filter to smooth the data, calculates the vertical velocity,
    and checks for a consistent upward motion over a specified window to identify the heel off event.
    inputs =    marker_file_path: path to the marker data file,
                leg: leg identifier ('r' for right, 'l' for left)
    output =    frame index of heel off event or None if not detected.
    '''
    markers = read_file(marker_file_path)
    if leg.lower()[0] == 'r':
        for i in range(0,len(markers.columns)):
            if markers.columns == 'RFCC':
                column = i+1
                break
    else:
        for i in range(0,len(markers.columns)):
            if markers.columns == 'LFCC':
                column = i+1
                break
    frame = detect_heel_off(markers[column].iloc[1:])
    return frame
    

def detect_heel_off(heel_z, dt=1/200):
    '''detect the heel off frame based on the heel marker just above the ground.
    It uses the vertical position of the heel marker to detect the frame where the heel starts to lift off the ground.
    The function applies a Savitzky-Golay filter to smooth the data, calculates the vertical velocity,
    and checks for a consistent upward motion over a specified window to identify the heel off event.
    inputs =    heel_z: vertical position of the heel marker,
                dt: time interval between frames (default is 1/200 seconds for 200 Hz sampling rate).
    output =    frame index of heel off event or None if not detected.'''
    # ---- Smooth ----
    heel_z_s = savgol_filter(heel_z, 21, 3)

    # ---- Velocity ----
    heel_v =  np.gradient(heel_z_s,dt)

    # ---- Parameters ----
    vel_thresh = 0.03          # m/s (small upward motion)
    window = int(0.08 / dt)    # ~80 ms window

    for i in range(len(heel_v) - window):
        cond1 = all(heel_v[i:i+window] > vel_thresh)
        cond2 = all(np.diff(heel_z_s[i:i+window]) > 0)

        if cond1 and cond2:
            return i

    return None
    
def peak_vertical_velocity(COM_vel):
    '''Detects the frame of peak vertical velocity based on biokinematics data.
    it use center_of_mass_Y column to detect the maximum com vertical velocity (y is vertical in opensim)
    and return the frame in force plate sampling rate.'''
    velocity_y_column = read_file(COM_vel, sep='\t', fs = 100)
    
    return int(np.where(velocity_y_column['center_of_mass_Y'] == velocity_y_column['center_of_mass_Y'].max())[0][0])