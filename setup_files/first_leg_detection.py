import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# trc_file = "stw1.trc"
# mot_file = "stw1.mot"

def detect_first_leg(trc_file, mot_file):
    trc_start = 6
    mot_start = 0

    trc = pd.read_csv(trc_file, sep="\t", skiprows=trc_start)

    # ---------- READ MOT ----------
    with open(mot_file) as f:
        for i, line in enumerate(f):
            if "endheader" in line.lower():
                mot_start = i + 1
                break

    mot = pd.read_csv(mot_file, sep="\t", skiprows=mot_start)

    # ---------- EXTRACT HEEL MARKERS ----------
    rfcc = trc.iloc[:,74:77].to_numpy()
    lfcc = trc.iloc[:,86:89].to_numpy()

    # ---------- EXTRACT COP ----------
    cop = mot[["ground_force_2_px","ground_force_2_py","ground_force_2_pz"]].to_numpy()

    # downsample GRF if higher frequency
    cop = cop[::5]

    # ---------- EXTRACT VERTICAL FORCE ----------
    fz = mot["ground_force_2_vy"].to_numpy()
    fz = fz[::5]

    # match frame counts
    min_frames = min(len(cop), len(rfcc))
    cop = cop[:min_frames]
    rfcc = rfcc[:min_frames]
    lfcc = lfcc[:min_frames]
    fz = fz[:min_frames]

    # ---------- DETECT STANCE FRAMES ----------
    threshold = 20  # Newton
    stance = fz > threshold

    cop_stance = cop[stance]
    rfcc_stance = rfcc[stance]
    lfcc_stance = lfcc[stance]

    # ---------- COMPUTE DISTANCES ----------
    dist_left = np.linalg.norm(cop_stance - lfcc_stance, axis=1)
    dist_right = np.linalg.norm(cop_stance - rfcc_stance, axis=1)

    mean_left = np.mean(dist_left)
    mean_right = np.mean(dist_right)

    # ---------- ASSIGN PLATE ----------
    if mean_left < mean_right:
        plate_owner = "Left Foot"
    else:
        plate_owner = "Right Foot"

    
    return plate_owner

# if __name__ == "__main__":
#     leg = detect_first_leg(trc_file, mot_file)
#     print("First leg on force plate:", leg)

# # ---------- PLOT COP VS HEELS ----------
# plt.figure(figsize=(6,6))

# plt.scatter(lfcc[:,0], lfcc[:,1], s=5, label="LFCC")
# plt.scatter(rfcc[:,0], rfcc[:,1], s=5, label="RFCC")
# plt.scatter(cop[:,0], cop[:,1], s=5, label="COP")

# plt.xlabel("X")
# plt.ylabel("Y")
# plt.title("COP vs Heel Markers")
# plt.legend()
# plt.axis("equal")
# plt.show()

# # ---------- PLOT VERTICAL FORCE ----------
# plt.figure(figsize=(10,4))
# plt.plot(fz)
# plt.axhline(threshold, color="red", linestyle="--")
# plt.title("Vertical Ground Reaction Force")
# plt.xlabel("Frame")
# plt.ylabel("Force (N)")
# plt.legend()
# plt.show()

# To run:
if __name__ == "__main__":
    leg = {}
    for subject in [53,55,45,54,42,56]:
        leg[subject] = []  # Add this line
        for trial in range(1,6):
            # trc_file = rf'd:\student\MTech\Sakshi\STW\S{subject:02d}\ExpData\Mocap\trcResults\stw{trial}.trc'
            trc_file = rf'D:\RESEARCH\STW_dataset\Extracted\S{subject:02d}\S{subject:02d}\Mocap\trcResults\stw{trial}.trc'
            mot_file = rf'D:\RESEARCH\STW_dataset\Extracted\S{subject:02d}\S{subject:02d}\Mocap\grfResults\stw{trial}.mot'
            print(f"Processing {trc_file}...")
            first_leg = detect_first_leg(trc_file, mot_file)
            leg[subject].append(first_leg)
    leg_df = pd.DataFrame(leg).T
    print(leg_df)
    
    os.chdir(os.path.dirname(r'D:\student\MTech\opensim_pipeline_batch_processing\pipeline'))
    leg_df.to_csv(r'pipeline\older.csv')
    print("Saved to older.csv")