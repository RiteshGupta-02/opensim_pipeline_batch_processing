import os
# import first_leg_using_just_acc as fl
import sys
from pathlib import Path
import setup_files.assign_leg_to_forceplate_decreptated as assign_leg_to_forceplate_decreptated
import first_leg_detection
BOLD_RED = "\033[1;91m" # Bold and bright red for extra attention
END = "\033[0m" # Reset code

# Template XML content
xml_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40500">
	<ExternalLoads name="externalloads">
		<objects>
			<ExternalForce name="{leg}_cal">
				<!--Name of the body the force is applied to.-->
				<applied_to_body>calcn_{leg}</applied_to_body>
				<!--Name of the body the force is expressed in (default is ground).-->
				<force_expressed_in_body>ground</force_expressed_in_body>
				<!--Name of the body the point is expressed in (default is ground).-->
				<point_expressed_in_body>ground</point_expressed_in_body>
				<!--Identifier (string) to locate the force to be applied in the data source.-->
				<force_identifier>ground_force_2_v</force_identifier>
				<!--Identifier (string) to locate the point to be applied in the data source.-->
				<point_identifier>ground_force_2_p</point_identifier>
				<!--Identifier (string) to locate the torque to be applied in the data source.-->
				<torque_identifier>ground_moment_2_m</torque_identifier>
				<!--Name of the data source (Storage) that will supply the force data.-->
				<data_source_name>stw{trial}.mot</data_source_name>
			</ExternalForce>
			<ExternalForce name="{leg1}_cal">
				<!--Name of the body the force is applied to.-->
				<applied_to_body>calcn_{leg1}</applied_to_body>
				<!--Name of the body the force is expressed in (default is ground).-->
				<force_expressed_in_body>ground</force_expressed_in_body>
				<!--Name of the body the point is expressed in (default is ground).-->
				<point_expressed_in_body>ground</point_expressed_in_body>
				<!--Identifier (string) to locate the force to be applied in the data source.-->
				<force_identifier>ground_force_3_v</force_identifier>
				<!--Identifier (string) to locate the point to be applied in the data source.-->
				<point_identifier>ground_force_3_p</point_identifier>
				<!--Identifier (string) to locate the torque to be applied in the data source.-->
				<torque_identifier>ground_moment_3_m</torque_identifier>
				<!--Name of the data source (Storage) that will supply the force data.-->
				<data_source_name>stw{trial}.mot</data_source_name>
			</ExternalForce>
		</objects>
		<groups />
		<!--Storage file (.sto) containing (3) components of force and/or torque and point of application.Note: this file overrides the data source specified by the individual external forces if specified.-->
		<datafile>{grf}</datafile>
	</ExternalLoads>
</OpenSimDocument>

''' 
if len(sys.argv) < 6:
        print("Usage: python grf_setup.py subject trial trc_file grf_file filepath")
        sys.exit(1)


subject = int(sys.argv[1])
subjdir = Path(sys.argv[2])
grf = Path(sys.argv[3])
trc_file = Path(sys.argv[4])
filepath = Path(sys.argv[5])
# Create output directory if it doesn't exist
output_dir = rf"{subjdir}\ID\grf"
os.makedirs(output_dir, exist_ok=True)


c3d_file = trc_file.parent.parent / f"{trc_file.stem}.c3d"

# _,leg = fl.calculate_marker_acceleration(trc_path=trc_file)
# leg = assign_leg_to_forceplate.run(trc_file, grf)
leg = first_leg_detection.detect_first_leg(trc_file, grf)
# Fill in the template with current trial number
xml_content = xml_template.format(trial=str(trc_file.stem)[-1],leg=leg[0].lower(),leg1='r' if leg[0].lower() == 'l' else 'l',grf=grf)

# Create filename
# filename = f"grf_{subject:02d}_stw{trial}.xml"
# filepath = os.path.join(output_dir, filename)

# Write to file
with open(filepath, 'w', encoding='UTF-8') as f:
	f.write(xml_content)

print(f"Created: {filepath}")


# for trial in range(1, 6):
#     leg = fl.calculate_marker_acceleration(trc_path=trc_file)
#     # Fill in the template with current trial number
#     xml_content = xml_template.format(trial=trial,leg=leg[0].lower(),leg1='r' if leg[0].lower() == 'l' else 'l',grf=grf)
    
#     # Create filename
#     # filename = f"grf_{subject:02d}_stw{trial}.xml"
#     # filepath = os.path.join(output_dir, filename)
    
#     # Write to file
#     with open(filepath, 'w', encoding='UTF-8') as f:
#         f.write(xml_content)
    
#     print(f"Created: {filepath}")

# print(f"\nAll files created successfully in '{output_dir}' directory!")