import sys
import os
import subprocess

def run_command(command):
    try:
        result = subprocess.run([sys.executable] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)
    
if __name__ == "__main__":    # Example command to run another Python script
    command = ["generate_setup_files.py","03", "stw_3", None, "xml", "ERROR"]  # Replace with your actual script and arguments
    stdout, stderr = run_command(command)
    
    print("Standard Output:")
    print(stdout)
    
    if stderr:
        print("Standard Error:")
        print(stderr)