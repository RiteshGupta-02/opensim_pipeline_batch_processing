import os
import sys
from pathlib import Path

# Template XML content
xml_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40500">
	<InverseDynamicsTool name="{subject}_stw{trial}">
		<!--Name of the directory where results are written. Be default this is the directory in which the setup file is be  executed.-->
		<results_directory>./results_ID</results_directory>
		<!--Name of the .osim file used to construct a model.-->
		<model_file>{model_file}</model_file>
		<!--Time range over which the inverse dynamics problem is solved.-->
		<time_range>0 Inf</time_range>
		<!--List of forces by individual or grouping name (e.g. All, actuators, muscles, ...) to be excluded when computing model dynamics. 'All' also excludes external loads added via 'external_loads_file'.-->
		<forces_to_exclude> Muscles</forces_to_exclude>
		<!--XML file (.xml) containing the external loads applied to the model as a set of ExternalForce(s).-->
		<external_loads_file>grf/{subject}_stw{trial}_grf.xml</external_loads_file>
		<!--The name of the file containing coordinate data. Can be a motion (.mot) or a states (.sto) file.-->
		<coordinates_file>../IK/results_stw/ik_output_stw{trial}_{subject}.mot</coordinates_file>
		<!--Low-pass cut-off frequency for filtering the coordinates_file data (currently does not apply to states_file or speeds_file). A negative value results in no filtering. The default value is -1.0, so no filtering.-->
		<lowpass_cutoff_frequency_for_coordinates>6</lowpass_cutoff_frequency_for_coordinates>
		<!--Name of the storage file (.sto) to which the generalized forces are written. Only a filename should be specified here (not a full path); the file will appear in the location provided in the results_directory property.-->
		<output_gen_force_file>id_output_{subject}_stw{trial}.sto</output_gen_force_file>
		<!--List of joints (keyword All, for all joints) to report body forces acting at the joint frame expressed in ground.-->
		<joints_to_report_body_forces />
		<!--Name of the storage file (.sto) to which the body forces at specified joints are written.-->
		<output_body_forces_file>body_forces_at_joints_{subject}_stw{trial}.sto</output_body_forces_file>
	</InverseDynamicsTool>
</OpenSimDocument>
'''

if len(sys.argv) < 4:
	print("Usage: python id_setup.py <sub_directory> <trial_filename> <model_file>")
	sys.exit(1)
     
subjdir = Path(sys.argv[1])
trial = Path(sys.argv[2]).name.removesuffix('.trc').removeprefix('stw')  # Extract trial from filename
model_file = Path(sys.argv[3])
filepath = Path(sys.argv[4])
# Create output directory if it doesn't exist
output_dir = rf"{subjdir}\ID"
os.makedirs(output_dir, exist_ok=True)
subject = (subjdir.name)


xml_content = xml_template.format(trial=trial,subject=subject, model_file=model_file)

# Create filename
# filename = rf"id_setup_{subject.lower()}_stw{trial}.xml"
# filepath = os.path.join(output_dir, filename)

# Write to file
with open(filepath, 'w', encoding='UTF-8') as f:
	f.write(xml_content)

print(f"Created: {filepath}")

# Generate files for trials 1 through 5
# for trial in range(1, 6):
#     # Fill in the template with current trial number
#     xml_content = xml_template.format(trial=trial,subject=subject)
    
#     # Create filename
#     filename = rf"id_setup_{subject.lower()}_stw{trial}.xml"
#     filepath = os.path.join(output_dir, filename)
    
#     # Write to file
#     with open(filepath, 'w', encoding='UTF-8') as f:
#         f.write(xml_content)
    
#     print(f"Created: {filepath}")

# print(f"\nAll files created successfully in '{output_dir}' directory!")