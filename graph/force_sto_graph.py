import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
from scipy.signal import butter, filtfilt


# -------------------------------------------------
# Read OpenSim .sto/.mot file with header preserved
# -------------------------------------------------
def read_mot_with_header(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    header_idx = next(
        (i for i, l in enumerate(lines) if 'endheader' in l.lower()),
        None
    )
    if header_idx is None:
        raise ValueError("No 'endheader' found in file")

    header_lines = lines[:header_idx + 1]
    colnames_line = lines[header_idx + 1].rstrip("\n")

    df = pd.read_csv(
        path,
        sep=r'\s+',
        engine='python',
        skiprows=header_idx + 1
    )

    return header_lines, colnames_line, df


# -------------------------------------------------
# Detect all muscle force columns
# -------------------------------------------------
def get_all_muscle_columns(df):
    """
    In Static Optimization force .sto files,
    everything except 'time' is a muscle force.
    """
    return [c for c in df.columns if c.lower() != 'time']


# -------------------------------------------------
# Butterworth low-pass filter (zero-phase)
# -------------------------------------------------
def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    wn = cutoff / nyq
    b, a = butter(order, wn, btype='low')
    return filtfilt(b, a, data, axis=0)


# -------------------------------------------------
# Main processing + plotting function
# -------------------------------------------------
def plot_all_muscles_filtered_0_100(
    in_path,
    out_path=None,
    cutoff=20.0,
    order=4,
    plot=True
):
    """
    Filter ALL muscle forces from Static Optimization output
    and plot them vs 0–100% movement cycle.
    """

    # ---- Read file ----
    header_lines, colnames_line, df = read_mot_with_header(in_path)

    # ---- Time and sampling frequency ----
    time_col = next(
        (c for c in df.columns if c.lower() == 'time'),
        df.columns[0]
    )
    time = df[time_col].values
    dt = np.mean(np.diff(time))
    fs = 1.0 / dt

    # ---- Normalize time to 0–100% ----
    percent = 100 * (time - time[0]) / (time[-1] - time[0])

    # ---- Detect muscle columns ----
    muscle_cols = get_all_muscle_columns(df)
    print(f"Found {len(muscle_cols)} muscles")

    # ---- Filter muscle forces only ----
    muscle_data = df[muscle_cols].values
    muscle_filt = butter_lowpass_filter(
        muscle_data,
        cutoff=cutoff,
        fs=fs,
        order=order
    )

    # ---- Store filtered data ----
    df_filt = df.copy()
    df_filt.loc[:, muscle_cols] = muscle_filt

    # ---- Optional: save filtered .sto ----
    if out_path is not None:
        with open(out_path, 'w', newline='\n') as f:
            f.writelines(header_lines)
            f.write(colnames_line + '\n')

        df_filt.to_csv(
            out_path,
            sep='\t',
            index=False,
            header=False,
            float_format='%.6f',
            mode='a'
        )

        print(f"Saved filtered file to: {out_path}")

    # ---------------- Plotting ----------------
    if plot:
        n = len(muscle_cols)
        ncols = 4
        nrows = math.ceil(n / ncols)

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(ncols * 4, nrows * 2.2),
            sharex=True
        )

        axes = np.atleast_1d(axes).ravel()

        for ax, muscle in zip(axes, muscle_cols):
            ax.plot(percent, df_filt[muscle].values, linewidth=1)
            ax.set_title(muscle, fontsize=9)
            ax.set_ylabel('Force (N)')
            ax.set_xlim(0, 100)              # ✅ force 0–100%
            ax.grid(True)

        # Hide unused axes
        for ax in axes[len(muscle_cols):]:
            ax.set_visible(False)

        # X-labels
        for ax in axes[:ncols]:
            ax.set_xlabel('Movement cycle (%)')

        plt.tight_layout()
        plt.savefig(
            f'sto_graph/{os.path.basename(in_path)}.png',
            dpi=300
        )
        plt.show()

    return df_filt


# =================================================
# USAGE
# =================================================

in_sto = r'd:\RESEARCH\STW_dataset\Extracted\S01\ID\results_ID\id_output_S01_stw1.sto'

df_filtered = plot_all_muscles_filtered_0_100(
    in_path=in_sto,
    cutoff=20,   # Hz (typical for muscle forces)
    order=4,
    plot=True,
    out_path=r'd:\RESEARCH\STW_dataset\Extracted\S01\ID\results_ID\id_output_S01_stw1_filtered.sto'
)
