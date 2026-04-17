import os
import numpy as np
import pandas as pd
import read_file

class gait:
    '''A class to detect gait events such as toe-off, heel strike, seat-off, and gait initiation based on vertical ground reaction force (GRF) data.
    The class takes in the GRF data file, body weight, and optional parameters for threshold and minimum width for event detection.'''

    def __init__(self, grf_file,body_weight, threshold = 20, min_width = 15):
        self.grf_data = read_file(grf_file, sep='\t', skiprows = 6)
        self.body_weight = body_weight
        self.threshold = threshold
        self.min_width = min_width


    def toe_off(self):
        '''Detects the frame of toe-off based on vertical ground reaction force (GRF) data.
        and return the frame in grf sampling rate.'''

        TO_idx = []

        #checks for threshold and stays above for 15 frames to detect toe-off frame
        above = self.grf_data['ground_force_vy'] > self.threshold
        # Find the indices where the condition changes from True to False (toe-off)
        while i < len(above) - self.min_width:
            # Toe Off: above → below threshold for >= min_width samples
            if above[i] and all(~above[i+1:i+1+self.min_width]):
                TO_idx.append(i + 1)
                i += self.min_width
                continue

            i += 1
        return TO_idx[0] if TO_idx else None  # Return the first toe-off index or None if not found
    
    def heel_strike(self):
        '''Detects the frame of heel strike based on vertical ground reaction force (GRF) data.
        and return the frame in grf sampling rate.'''

        HS_idx = []

        #checks for threshold and stays above for 15 frames to detect heel strike frame
        above = self.grf_data['ground_force_vy'] > self.threshold
        # Find the indices where the condition changes from True to False (heel strike)
        while i < len(above) - self.min_width:
            # Heel Strike: above → below threshold for >= min_width samples
            if not above[i] and all(above[i+1:i+1+self.min_width]):
                HS_idx.append(i + 1)
                i += self.min_width
                continue

            i += 1
        return HS_idx[0] if HS_idx else None  # Return the first heel strike index or None if not found

    def seat_off(self):
        '''Detects the frame of seat-off based on force plate data.
        and return the frame in force plate sampling rate.'''

        return int(np.where(self.grf_data['ground_force_vy'] == self.grf_data['ground_force_vy'].max())[0][0])

    def gait_intiation(self):
        '''Detects the frame of gait initiation based on force plate data.
        and return the frame in force plate sampling rate.'''

        return int(np.where(self.grf_data['ground_force_vz'] > self.body_weight * 0.056)[0][0])