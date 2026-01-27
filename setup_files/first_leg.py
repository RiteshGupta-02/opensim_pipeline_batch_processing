import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import sys
from pathlib import Path

def calculate_marker_acceleration(trc_path, trial = 0,subject = 0,output_csv='marker_accelerations.csv', cutoff_freq=6.0):
    # 1. Load TRC file
    # We read the headers carefully to find RFCC and LFCC
    with open(Path(trc_path), 'r') as f:
        lines = f.readlines()
    
    # Marker names are usually on line 3, components (X, Y, Z) on line 4
    marker_names = lines[3].split('\t')
    
    # Find the column index for RFCC and LFCC
    # TRC format: Frame (0), Time (1), M1_X (2), M1_Y (3), M1_Z (4)...
    rfcc_idx = -1
    lfcc_idx = -1
    
    current_col = 2
    for m in marker_names:
        m = m.strip()
        if m == 'RFCC': rfcc_idx = current_col
        if m == 'LFCC': lfcc_idx = current_col
        if m: current_col += 3 # Each marker has 3 columns (X, Y, Z)

    if rfcc_idx == -1 or lfcc_idx == -1:
        raise ValueError("RFCC or LFCC markers not found in the TRC file.")

    # 2. Load the numerical data
    data = pd.read_csv(trc_path, sep='\t', skiprows=5, header=None)
    time = data.iloc[:, 1].values
    fs = 1.0 / np.mean(np.diff(time)) # Sampling frequency
    
    # Extract X, Y, Z for both markers
    rfcc_pos = data.iloc[:, rfcc_idx:rfcc_idx+3].values
    lfcc_pos = data.iloc[:, lfcc_idx:lfcc_idx+3].values

    # 3. Filter the Position Data (Butterworth Low-pass)
    # This is mandatory; differentiating raw noise creates huge errors.
    b, a = butter(4, cutoff_freq / (fs / 2), btype='low',fs = fs) # type: ignore
    rfcc_filt = filtfilt(b, a, rfcc_pos, axis=0)
    lfcc_filt = filtfilt(b, a, lfcc_pos, axis=0)

    # 4. Differentiate twice to get Acceleration (m/s^2)
    # Velocity
    rfcc_vel = np.gradient(rfcc_filt, time, axis=0)
    lfcc_vel = np.gradient(lfcc_filt, time, axis=0)
    # Acceleration
    rfcc_acc = np.gradient(rfcc_vel, time, axis=0)
    lfcc_acc = np.gradient(lfcc_vel, time, axis=0)

    # 5. Determine which leg steps first
    # We look for the first peak in Vertical (Y) acceleration (index 1)
    # A threshold of 0.5 m/s^2 is usually enough to detect movement
    threshold = 2
    r_start_idx = np.where(np.abs(rfcc_acc[:, 1]) > threshold)[0][0]
    l_start_idx = np.where(np.abs(lfcc_acc[:, 1]) > threshold)[0][0]
    
    first_leg = "Right (RFCC)" if r_start_idx < l_start_idx else "Left (LFCC)"
    # print(f"The {first_leg} leg starts moving first at {time[min(r_start_idx, l_start_idx)]:.3f}s")
    

    # # 6. Save and Plot
    # results = pd.DataFrame({
    #     'time': time,
    #     'RFCC_Acc_Y': rfcc_acc[:, 1],
    #     'LFCC_Acc_Y': lfcc_acc[:, 1]
    # })
    # results.to_csv(output_csv, index=False)
    # os.chdir(os.path.dirname(rf'd:\UG_Proj\Human Sitting to Walking Transitions\S{subject:02d}'))
    
    # plt.figure(figsize=(10, 5))
    # plt.plot(time, rfcc_acc[:, 1], label='RFCC (Right) Vertical Accel')
    # plt.plot(time, lfcc_acc[:, 1], label='LFCC (Left) Vertical Accel')
    # plt.axvline(time[r_start_idx], color='blue', linestyle='--', alpha=0.5, label='R-Start')
    # plt.axvline(time[l_start_idx], color='red', linestyle='--', alpha=0.5, label='L-Start')
    # plt.title('Heel Marker Vertical Acceleration')
    # plt.ylabel('Acceleration ($m/s^2$)')
    # plt.xlabel('Time (s)')
    # plt.legend()
    # plt.savefig(f'heel_acceleration_plot_{trial}.png')
    
    return first_leg


      


# To run:
# if __name__ == "__main__":
#     leg = {}
#     for subject in range(1,11):
#         leg[subject] = []  # Add this line
#         for trial in range(1,6):
#             trc_file = rf'd:\UG_Proj\Human Sitting to Walking Transitions\S{subject:02d}\ExpData\Mocap\trcResults\stw{trial}.trc'
#             print(f"Processing {trc_file}...")
#             df,first_leg = calculate_marker_acceleration(trc_file, output_csv=rf'd:\UG_Proj\Human Sitting to Walking Transitions\S{subject:02d}\subject_{subject:02d}_trial_{trial}_accelerations.csv',trial=trial,subject=subject)
#             leg[subject].append({trial:first_leg})
#     leg_df = pd.DataFrame(leg).T
    
#     os.chdir(os.path.dirname(rf'd:\UG_Proj\Human Sitting to Walking Transitions'))
#     leg_df.to_excel('leg_results.xlsx')
#     print("Saved to leg_results.xlsx")
