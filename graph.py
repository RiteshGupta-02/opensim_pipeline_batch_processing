import pandas as pd

import matplotlib.pyplot as plt

def plot_muscle_forces(sto_file, muscles=None):
    """
    Plot muscle forces vs time from a .sto file
    
    Args:
        sto_file: path to the force.sto file
        muscles: list of muscle names to plot
    """
    if muscles is None:
        muscles = ['bflh_r', 'bfsh_r', 'gaslat_r', 'gasmed_r', 'glmax1_r', 
                   'glmax2_r', 'glmax3_r', 'glmed1_r', 'glmed2_r', 'glmed3_r', 
                   'recfem_r', 'semimem_r', 'semiten_r', 'soleus_r', 'tibant_r', 
                   'tibpost_r', 'vasint_r', 'vaslat_r', 'vasmed_r']
    
    # Read the .sto file (skip header rows if present)
    df = pd.read_csv(sto_file, sep='\t', skiprows=14)
    
    # Get time column (column 0)
    time = df.iloc[:, 0]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each muscle force
    for muscle in muscles:
        if muscle in df.columns:
            ax.plot(time, df[muscle], label=muscle, linewidth=1.5)
    
    # Customize plot
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Force (N)', fontsize=12)
    ax.set_title('Muscle Forces vs Time', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# Usage
if __name__ == '__main__':
    plot_muscle_forces(r'd:\student\MTech\test\output\subject01_StaticOptimization_force.sto')