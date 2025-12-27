import os
BOLD_RED = "\033[1;91m" # Bold and bright red for extra attention
END = "\033[0m" # Reset code

# Template XML content
xml_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40500">
	<ExternalLoads name="externalloads">
		<objects>
			<ExternalForce name="l_cal">
				<!--Name of the body the force is applied to.-->
				<applied_to_body>calcn_l</applied_to_body>
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
			<ExternalForce name="r_cal">
				<!--Name of the body the force is applied to.-->
				<applied_to_body>calcn_r</applied_to_body>
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
		<datafile>../../ExpData/Mocap/grfResults/stw{trial}.mot</datafile>
	</ExternalLoads>
</OpenSimDocument>

'''

# Create output directory if it doesn't exist
output_dir = r"D:\UG_Proj\Human Sitting to Walking Transitions\S01\ID\grf"
os.makedirs(output_dir, exist_ok=True)

# Generate files for trials 1 through 5
print("{BOLD_RED}considering left leg on 2 and right leg on 3{END}")
for trial in range(1, 6):
    # Fill in the template with current trial number
    xml_content = xml_template.format(trial=trial)
    
    # Create filename
    filename = f"grf_S01_stw{trial}.xml" #=====================================change the S01 here for differnt subjects
    #=========================================
    filepath = os.path.join(output_dir, filename)
    
    # Write to file
    with open(filepath, 'w', encoding='UTF-8') as f:
        f.write(xml_content)
    
    print(f"Created: {filepath}")

print(f"\nAll files created successfully in '{output_dir}' directory!")