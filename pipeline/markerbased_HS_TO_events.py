from ezc3d import c3d
from scipy.signal import find_peaks, argrelmin, butter, filtfilt
import numpy as np


def align_axis(traj):
    """
    Find the dominant movement axis for a 3xN trajectory (X,Y,Z).
    Returns 0, 1, or 2.
    """
    diffs = traj[:, -1] - traj[:, 0]
    axis = np.argmax(np.abs(diffs))
    return axis


def absolute(x, axis):
    """
    Ensure motion along dominant axis is positive by reversing the time
    order if needed. x is 3xN.
    """
    if (x[axis][-1] - x[axis][0]) < 0:
        x[0] = list(reversed(x[0]))
        x[1] = list(reversed(x[1]))
        x[2] = list(reversed(x[2]))
    return x


def lowpass(signal, fs=200, cutoff=8, order=4):
    """
    Zero‑phase low‑pass Butterworth filter.
    fs: sampling rate (Hz)
    cutoff: cutoff frequency (Hz)
    """
    b, a = butter(order, cutoff / (fs / 2), btype='low')
    return filtfilt(b, a, signal)


def load_c3d_markers(c3d_path):
    """
    Load C3D file and return marker trajectories and labels.
    """
    c = c3d(c3d_path)
    markers = c['data']['points']          # (4, N_markers, N_frames)
    labels = c['parameters']['POINT']['LABELS']['value']
    xyz = markers[:3, :, :]                # (3, N_markers, N_frames)
    return xyz, labels


def compute_sacrum(xyz, labels):
    """
    Build pelvis reference trajectory as average of LASIS and RASIS.
    """
    rasis_idx = labels.index('RASIS')
    lasis_idx = labels.index('LASIS')

    trajectory_rasis = xyz[:, rasis_idx, :]
    trajectory_lasis = xyz[:, lasis_idx, :]

    trajectory_sacrum = (trajectory_lasis + trajectory_rasis) / 2.0
    return trajectory_sacrum


def extract_1d_marker(xyz, labels, name, axis, make_absolute=True):
    """
    Extract 1D trajectory of a marker along given axis, optionally applying
    absolute() to orient it consistently.
    """
    idx = labels.index(name)
    traj = xyz[:, idx, :]

    if make_absolute:
        traj = absolute(traj, axis)

    traj_1d = traj[axis]
    return traj_1d


def compute_relative_foot_signals(trajectory_sacrum_1d,
                                  trajectory_lfcc_1d,
                                  trajectory_rfcc_1d,
                                  trajectory_lfmt2_1d,
                                  trajectory_rfmt2_1d):
    """
    Compute pelvis-relative 1D signals: heel/toe (now LFCC/RFCC, LFMT2/RFMT2) minus sacrum.
    """
    lhs = trajectory_lfcc_1d - trajectory_sacrum_1d   # left heel vs sacrum (LFCC)
    rhs = trajectory_rfcc_1d - trajectory_sacrum_1d   # right heel vs sacrum (RFCC)
    lto = trajectory_lfmt2_1d - trajectory_sacrum_1d  # left toe vs sacrum (LFMT2)
    rto = trajectory_rfmt2_1d - trajectory_sacrum_1d  # right toe vs sacrum (RFMT2)
    return lhs, rhs, lto, rto


def detect_events(lhs, rhs, lto, rto, fs=200):
    """
    Coordinate-based gait event detection with filtering and constraints.
    - Heel strike: peaks in heel-sacro distance (lhs, rhs)
    - Toe off: minima in toe-sacro distance (lto, rto)
    """

    # 1) Low-pass filter the signals
    lhs_f = lowpass(lhs, fs=fs, cutoff=8)
    rhs_f = lowpass(rhs, fs=fs, cutoff=8)
    lto_f = lowpass(lto, fs=fs, cutoff=8)
    rto_f = lowpass(rto, fs=fs, cutoff=8)

    # 2) Peak/minimum detection parameters (tune as needed)
    min_step_frames = 180   # ~0.9 s at 200 Hz, adjust per dataset
    prominence = 30         # adjust based on signal amplitude

    left_hs_idx, _ = find_peaks(lhs_f,
                                distance=min_step_frames,
                                prominence=prominence)
    right_hs_idx, _ = find_peaks(rhs_f,
                                 distance=min_step_frames,
                                 prominence=prominence)

    left_to_idx = argrelmin(lto_f, order=40)[0][-1]
    right_to_idx = argrelmin(rto_f, order=40)[0][-1]

    return left_hs_idx[0], right_hs_idx[0], left_to_idx, right_to_idx


def main(c3d_path):
    # Path to your C3D file
    # c3d_path = r"D:\student\MTech\Sakshi\STW\S01\ExpData\Mocap\stw2.c3d"

    fs_markers = 200  # Hz

    # Load data
    xyz, labels = load_c3d_markers(c3d_path)

    # Pelvis reference trajectory (3D) from LASIS/RASIS
    trajectory_sacrum = compute_sacrum(xyz, labels)

    # Determine dominant axis from pelvis and orient positively
    axis = align_axis(trajectory_sacrum)
    trajectory_sacrum = absolute(trajectory_sacrum, axis)
    trajectory_sacrum_1d = trajectory_sacrum[axis]

    # Foot markers along dominant axis (using LFCC/RFCC and LFMT2/RFMT2)
    trajectory_rfcc_1d = extract_1d_marker(xyz, labels, 'RFCC', axis, make_absolute=True)
    trajectory_rfmt2_1d = extract_1d_marker(xyz, labels, 'RFMT2', axis, make_absolute=True)
    trajectory_lfcc_1d = extract_1d_marker(xyz, labels, 'LFCC', axis, make_absolute=True)
    trajectory_lfmt2_1d = extract_1d_marker(xyz, labels, 'LFMT2', axis, make_absolute=True)

    # Pelvis-relative signals
    lhs, rhs, lto, rto = compute_relative_foot_signals(
        trajectory_sacrum_1d,
        trajectory_lfcc_1d,
        trajectory_rfcc_1d,
        trajectory_lfmt2_1d,
        trajectory_rfmt2_1d
    )

    # Detect gait events
    left_hs, right_hs, left_to, right_to = detect_events(lhs, rhs, lto, rto, fs=fs_markers)

    # Print results
    print("Dominant axis:", axis)
    print("Left heel strike indices:", left_hs)
    print("Right heel strike indices:", right_hs)
    print("Left toe off indices:", left_to)
    print("Right toe off indices:", right_to)


# if __name__ == "__main__":
#     main()
