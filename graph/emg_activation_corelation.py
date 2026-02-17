import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# FILES
# -----------------------------
ACT_STO = "subject01_StaticOptimization_activation_r.sto"
EMG_CSV = "processed_normalized_emg.csv"

# -----------------------------
# READ STO
# -----------------------------
def read_sto(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    header_end = None
    for i, line in enumerate(lines):
        if "endheader" in line.lower():
            header_end = i
            break

    return pd.read_csv(filename, sep=r"\s+", skiprows=header_end + 1)

df_act = read_sto(ACT_STO)
time = df_act.iloc[:, 0].to_numpy()

# Convert time → 0–100%
x_act = (time - time[0]) / (time[-1] - time[0]) * 100

# -----------------------------
# LOAD EMG
# -----------------------------
df_emg = pd.read_csv(EMG_CSV)
x_emg = np.linspace(0, 100, len(df_emg))

# -----------------------------
# YOUR TARGET MUSCLES
# -----------------------------
target_right_muscles = [
    "bflh_r", "bfsh_r",
    "gaslat_r", "gasmed_r",
    "tibant_r",
    "vasmed_r", "vaslat_r",
    "recfem_r",
    "semiten_r"
]

muscle_to_emg = {
    "tibant_r": "Tibialis Anterior (%)",
    "gasmed_r": "Gastrocnemius Medialis (%)",
    "gaslat_r": "Gastrocnemius Lateralis (%)",
    "recfem_r": "Rectus Femoris (%)",
    "vaslat_r": "Vastus Lateralis (%)",
    "vasmed_r": "Vastus Medialis (%)",
    "semiten_r": "Semitendinosus (%)",
    "bflh_r": "Bicep Femoris (%)",
    "bfsh_r": "Bicep Femoris (%)",
}

# -----------------------------
# PLOT LOOP
# -----------------------------
for muscle in target_right_muscles:

    if muscle not in df_act.columns:
        print(f"Skipping {muscle} (not found in activation file)")
        continue

    if muscle not in muscle_to_emg:
        print(f"Skipping {muscle} (no EMG mapping)")
        continue

    emg_col = muscle_to_emg[muscle]

    if emg_col not in df_emg.columns:
        print(f"Skipping {muscle} (EMG column not found: {emg_col})")
        continue

    # Activation
    y_act = df_act[muscle].to_numpy()

    # Interpolate EMG to activation grid
    y_emg = np.interp(x_act, x_emg, df_emg[emg_col].to_numpy())

    # -----------------------------
    # PLOT (BLUE activation, RED EMG)
    # -----------------------------
    fig, ax1 = plt.subplots(figsize=(10, 4))

    # Activation (blue)
    ax1.plot(x_act, y_act, color="black", linewidth=2)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel("Gait Cycle (%)")
    ax1.set_ylabel("Activation (0–1)", color="black")
    ax1.tick_params(axis='y', labelcolor="black")
    ax1.grid(True, alpha=0.3)

    # EMG (red)
    ax2 = ax1.twinx()
    ax2.plot(x_act, y_emg, color="orange", linewidth=2)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("%MVC", color="orange")
    ax2.tick_params(axis='y', labelcolor="orange")

    plt.title(f"{muscle}: Activation (black) vs EMG %MVC (orange)")
    plt.tight_layout()
    plt.show()
