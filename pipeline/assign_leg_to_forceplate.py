"""
assign_leg_to_forceplate.py
============================
Determines which leg (Left / Right) stepped on Force Plate 2 and Force Plate 3.

Dataset  : Sit-to-Walk (STW)
Subject  : S30, Trial stw4
FP1      : Skipped (subject seated on it at t=0)
FP2/FP3  : Assigned using LFCC / RFCC calcaneus markers + GRF onset detection

Logic
-----
For each force plate (FP2 then FP3):
  1. Detect activation onset from vertical GRF (adaptive noise threshold + min duration).
  2. Define an analysis window ending just before contact:
       - FP2 : from quiet-standing (~1.5s before onset) to 50ms before onset
       - FP3 : from 100ms AFTER FP2 contact (contralateral foot now planted)
               to 50ms before FP3 onset
         (this avoids the locomotion blur where both feet are moving)
  3. Compute three swing metrics on LFCC_X and RFCC_X:
       - Net forward displacement  (weight x2 - most reliable)
       - Total range of displacement
       - 95th-percentile velocity
  4. Vote: whichever foot scores higher is the swing foot -> steps on that plate.

Units   : TRC in metres, GRF in Newtons
TRC fs  : 200 Hz
GRF fs  : 1000 Hz
"""

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

# ── Hardcoded paths ──────────────────────────────────────────────────────────
TRC_PATH = r"D:\RESEARCH\STW_dataset\Extracted\S30\S30\Mocap\trcResults\stw4.trc"
GRF_PATH = r"D:\RESEARCH\STW_dataset\Extracted\S30\S30\Mocap\grfResults\stw4.mot"

# Calcaneus marker names (must match TRC file exactly)
LEFT_MARKER  = "LFCC"
RIGHT_MARKER = "RFCC"

# Anterior-posterior axis: X has std ~0.46 m (walking direction) vs Z ~0.008 m
AP_AXIS = "X"

# Force plate columns (FP1 is skipped - subject seated on it at t=0)
FP_COLS = {
    "FP2": "ground_force_2_vy",
    "FP3": "ground_force_3_vy",
}

# Signal processing settings
GRF_LOWPASS_HZ    = 20.0   # low-pass cutoff for GRF filtering
MARKER_LOWPASS_HZ =  6.0   # low-pass cutoff for marker trajectories
BASELINE_SEC      =  0.5   # quiet-standing baseline duration for noise estimation
NOISE_MULTIPLIER  =  5.0   # threshold = mean + N * std of baseline
MIN_CONTACT_MS    = 100.0  # min sustained activation to count as real contact (ms)


# ── File parsers ─────────────────────────────────────────────────────────────

def parse_trc(filepath: str):
    """Parse OpenSim / Vicon .trc file. Returns (DataFrame, sample_rate_Hz)."""
    with open(filepath, "r") as f:
        lines = f.readlines()

    # Line index 2: DataRate value
    trc_fs = float(lines[2].strip().split("\t")[0])

    # Line index 3: marker names row  (Frame#  Time  M1  ''  ''  M2 ...)
    marker_line  = lines[3].strip().split("\t")
    marker_names = [
        m.strip() for m in marker_line
        if m.strip() and m.strip() not in ("Frame#", "Time")
    ]

    col_labels = ["Frame", "Time"] + [
        f"{m}_{ax}" for m in marker_names for ax in ["X", "Y", "Z"]
    ]

    # Data starts at line index 6 (line 4 = X/Y/Z sub-header, line 5 = blank)
    rows = []
    for line in lines[6:]:
        line = line.strip()
        if not line:
            continue
        vals = line.split("\t")
        if len(vals) < 3:
            continue
        try:
            rows.append([float(v) if v.strip() else np.nan for v in vals])
        except ValueError:
            continue

    df = pd.DataFrame(rows, columns=col_labels)
    return df, trc_fs


def parse_grf(filepath: str):
    """Parse OpenSim .mot GRF file. Returns (DataFrame, sample_rate_Hz)."""
    with open(filepath, "r") as f:
        lines = f.readlines()

    col_names  = None
    data_start = 0
    for i, line in enumerate(lines):
        if line.strip().lower() == "endheader":
            col_names  = lines[i + 1].strip().split()
            data_start = i + 2
            break

    if col_names is None:
        raise ValueError("'endheader' not found in GRF file.")

    rows = []
    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append([float(v) for v in line.split()])
        except ValueError:
            continue

    df = pd.DataFrame(rows, columns=col_names)
    df.columns = [c.lower() for c in df.columns]
    grf_fs = 1.0 / (df["time"].iloc[1] - df["time"].iloc[0])
    return df, grf_fs


# ── Signal utilities ──────────────────────────────────────────────────────────

def lowpass(data: np.ndarray, cutoff: float, fs: float, order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth low-pass filter."""
    nyq    = 0.5 * fs
    cutoff = min(cutoff, nyq * 0.95)
    b, a   = butter(order, cutoff / nyq, btype="low")
    return filtfilt(b, a, data)


def find_onset(signal: np.ndarray, fs: float,
               baseline_sec: float = 0.5,
               noise_mult:   float = 5.0,
               min_dur_ms:   float = 100.0):
    """
    Find the first frame where |signal| exceeds an adaptive noise threshold
    and stays above it for at least min_dur_ms.

    Returns (onset_frame_index, threshold_value).
    """
    n_base = max(10, int(baseline_sec * fs))
    base   = np.abs(signal[:n_base])
    thresh = float(base.mean() + noise_mult * base.std())
    min_fr = max(3, int(min_dur_ms / 1000.0 * fs))

    above = np.abs(signal) > thresh
    count = 0
    for i, val in enumerate(above):
        if val:
            count += 1
            if count >= min_fr:
                return i - min_fr + 1, thresh
        else:
            count = 0
    return -1, thresh


# ── Swing leg detection ───────────────────────────────────────────────────────

def detect_swing_leg(left_pos: np.ndarray, right_pos: np.ndarray,
                     trc_fs: float, trc_time: np.ndarray,
                     window_start_s: float, window_end_s: float) -> dict:
    """
    Identify which foot is swinging inside [window_start_s, window_end_s].

    Scoring (votes):
      - Net forward displacement  × 2  (most reliable)
      - Total range of motion     × 1
      - 95th-percentile velocity  × 1
    A 15 % relative margin (+ 10 mm absolute for net) is required to cast a vote.

    Returns dict with leg, confidence, scores, votes, and metric details.
    """
    ws = int(np.searchsorted(trc_time, window_start_s))
    we = int(np.searchsorted(trc_time, window_end_s))

    if we - ws < 5:
        return {
            "leg": "Uncertain", "confidence": "Low",
            "votes": [],
            "scores": {"Left": 0, "Right": 0},
            "details": {"window_s": [round(window_start_s, 3), round(window_end_s, 3)],
                        "error": "Window too short"},
        }

    lw = lowpass(left_pos,  MARKER_LOWPASS_HZ, trc_fs)[ws:we]
    rw = lowpass(right_pos, MARKER_LOWPASS_HZ, trc_fs)[ws:we]
    dt = 1.0 / trc_fs

    # Metrics (positions in metres -> convert to mm for readability only)
    l_net  = float(lw[-1] - lw[0])
    r_net  = float(rw[-1] - rw[0])
    l_disp = float(np.nanmax(lw) - np.nanmin(lw))
    r_disp = float(np.nanmax(rw) - np.nanmin(rw))
    l_vel  = float(np.nanpercentile(np.abs(np.gradient(lw, dt)), 95))
    r_vel  = float(np.nanpercentile(np.abs(np.gradient(rw, dt)), 95))

    MARGIN        = 0.15   # 15 % relative margin
    NET_ABS_MARGIN = 0.010  # 10 mm absolute margin for net displacement

    left_score = right_score = 0
    votes = []

    # Net displacement (weight ×2)
    if l_net > r_net + NET_ABS_MARGIN:
        left_score  += 2; votes.append("net_displacement → Left  (×2)")
    elif r_net > l_net + NET_ABS_MARGIN:
        right_score += 2; votes.append("net_displacement → Right (×2)")

    # Total range (×1)
    if l_disp > r_disp * (1 + MARGIN):
        left_score  += 1; votes.append("range → Left")
    elif r_disp > l_disp * (1 + MARGIN):
        right_score += 1; votes.append("range → Right")

    # Velocity (×1)
    if l_vel > r_vel * (1 + MARGIN):
        left_score  += 1; votes.append("velocity → Left")
    elif r_vel > l_vel * (1 + MARGIN):
        right_score += 1; votes.append("velocity → Right")

    total = left_score + right_score
    if total == 0:
        leg = "Uncertain"; confidence = "Low"
    elif left_score > right_score:
        leg = "Left"
        confidence = "High" if left_score / total >= 0.75 else "Medium"
    elif right_score > left_score:
        leg = "Right"
        confidence = "High" if right_score / total >= 0.75 else "Medium"
    else:
        leg = "Uncertain"; confidence = "Low"

    return {
        "leg":        leg,
        "confidence": confidence,
        "votes":      votes,
        "scores":     {"Left": left_score, "Right": right_score},
        "details": {
            "window_s":           [round(trc_time[ws], 3), round(trc_time[we - 1], 3)],
            "left_net_mm":        round(l_net  * 1000, 1),
            "right_net_mm":       round(r_net  * 1000, 1),
            "left_range_mm":      round(l_disp * 1000, 1),
            "right_range_mm":     round(r_disp * 1000, 1),
            "left_peakvel_mm_s":  round(l_vel  * 1000, 1),
            "right_peakvel_mm_s": round(r_vel  * 1000, 1),
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def assign_legs() -> dict:
    """
    Assign left / right leg to Force Plate 2 and Force Plate 3.

    Returns:
        {
          "FP2": {"leg": "Left"|"Right"|"Uncertain", "confidence": "High"|"Medium"|"Low",
                  "fp_onset_s": float, "grf_thresh_N": float,
                  "votes": [...], "scores": {...}, "details": {...}},
          "FP3": { ... },
        }
    """
    # Load data
    df_trc, trc_fs = parse_trc(TRC_PATH)
    df_grf, grf_fs = parse_grf(GRF_PATH)

    trc_time  = df_trc["Time"].values
    left_pos  = df_trc[f"{LEFT_MARKER}_{AP_AXIS}"].values.astype(float)
    right_pos = df_trc[f"{RIGHT_MARKER}_{AP_AXIS}"].values.astype(float)

    # Detect GRF onset for each plate
    onsets = {}
    for fp_label, col in FP_COLS.items():
        sig_raw = np.abs(df_grf[col].values.astype(float))
        sig_flt = lowpass(sig_raw, GRF_LOWPASS_HZ, grf_fs)
        onset_fr, thresh = find_onset(
            sig_flt, grf_fs,
            baseline_sec=BASELINE_SEC,
            noise_mult=NOISE_MULTIPLIER,
            min_dur_ms=MIN_CONTACT_MS,
        )
        if onset_fr < 0:
            raise RuntimeError(
                f"{fp_label}: no sustained activation found above threshold "
                f"({thresh:.1f} N).  Check your GRF data or lower NOISE_MULTIPLIER."
            )
        onsets[fp_label] = {
            "frame": onset_fr,
            "time":  float(df_grf["time"].iloc[onset_fr]),
            "threshold_N": round(thresh, 2),
        }

    fp2_t = onsets["FP2"]["time"]
    fp3_t = onsets["FP3"]["time"]

    # Build analysis windows
    # FP2: quiet-standing epoch up to just before first foot lands
    fp2_win = (max(0.0, fp2_t - 1.5),  fp2_t - 0.05)

    # FP3: after FP2 foot is planted (100 ms grace) up to just before second foot lands
    #      Using a post-FP2-contact window prevents both-feet-moving ambiguity
    fp3_win = (fp2_t + 0.10,            fp3_t - 0.05)

    # Detect swing leg for each plate
    results = {}
    for fp_label, (win_start, win_end) in [("FP2", fp2_win), ("FP3", fp3_win)]:
        swing = detect_swing_leg(
            left_pos, right_pos, trc_fs, trc_time, win_start, win_end
        )
        results[fp_label] = {
            "leg":          swing["leg"],
            "confidence":   swing["confidence"],
            "fp_onset_s":   round(onsets[fp_label]["time"], 3),
            "grf_thresh_N": onsets[fp_label]["threshold_N"],
            "votes":        swing["votes"],
            "scores":       swing["scores"],
            "details":      swing["details"],
        }

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = assign_legs()

    print("\n" + "=" * 60)
    print("   LEG-TO-FORCE-PLATE ASSIGNMENT  (FP1 skipped)")
    print("=" * 60)
    for fp, res in results.items():
        d = res["details"]
        print(f"\n  {fp}  →  {res['leg']} leg   "
              f"[confidence: {res['confidence']}]")
        print(f"       GRF onset : {res['fp_onset_s']} s  "
              f"(threshold = {res['grf_thresh_N']} N)")
        print(f"       Window    : {d['window_s'][0]} – {d['window_s'][1]} s")
        print(f"       Scores    : Left = {res['scores']['Left']}  "
              f"Right = {res['scores']['Right']}")
        if res["votes"]:
            for v in res["votes"]:
                print(f"                   • {v}")
        else:
            print("                   • (no decisive vote)")
        print(f"       LFCC      : net={d['left_net_mm']:+.1f} mm  "
              f"range={d['left_range_mm']:.1f} mm  "
              f"vel={d['left_peakvel_mm_s']:.0f} mm/s")
        print(f"       RFCC      : net={d['right_net_mm']:+.1f} mm  "
              f"range={d['right_range_mm']:.1f} mm  "
              f"vel={d['right_peakvel_mm_s']:.0f} mm/s")
    print("\n" + "=" * 60)
