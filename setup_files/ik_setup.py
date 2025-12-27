import os

# Template XML content
xml_template = r'''<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="30000">
	<InverseKinematicsTool name="subject{subject}_stw{trial}">
		<!--Directory used for writing results.-->
		<results_directory>./results_stw</results_directory>
		<!--Directory for input files-->
		<input_directory />
		<!--Name of the .osim file used to construct a model.-->
		<model_file>d:\UG_Proj\Human Sitting to Walking Transitions\S{subject}\scale\subject{subject}_simbody_scaled.osim</model_file>
		<!--A positive scalar that is used to weight the importance of satisfying constraints.A weighting of 'Infinity' or if it is unassigned results in the constraints being strictly enforced.-->
		<constraint_weight>Inf</constraint_weight>
		<!--The accuracy of the solution in absolute terms. I.e. the number of significantdigits to which the solution can be trusted.-->
		<accuracy>1e-05</accuracy>
		<!--Markers and coordinates to be considered (tasks) and their weightings.-->
		<IKTaskSet>
			<objects>
				<!-- Upper-body markers (anatomical and tracking). -->
				<IKMarkerTask name="R.Shoulder">
					<!--Whether or not this task will be used during inverse kinematics solve.-->
					<apply>true</apply>
					<!--Weight given to a marker or coordinate for solving inverse kinematics problems.-->
					<weight>5</weight>
				</IKMarkerTask>
				<IKMarkerTask name="L.Shoulder">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="R.Clavicle">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="L.Clavicle">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="R.Biceps">
					<apply>false</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="L.Biceps">
					<apply>false</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="R.Elbow">
					<apply>true</apply> <weight>2</weight> </IKMarkerTask>
				<IKMarkerTask name="L.Elbow">
					<apply>true</apply> <weight>2</weight> </IKMarkerTask>
				<IKMarkerTask name="R.MElbow">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="L.MElbow">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="R.Forearm">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="L.Forearm">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="R.Wrist">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="L.Wrist">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>

				<!-- Lower-body anatomical markers -->
				<IKMarkerTask name="RASIS">
					<apply>true</apply> <weight>50</weight> </IKMarkerTask>
				<IKMarkerTask name="LASIS">
					<apply>true</apply> <weight>50</weight> </IKMarkerTask>
				<IKMarkerTask name="S2">
					<apply>false</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="RPSIS">
					<apply>true</apply> <weight>40</weight> </IKMarkerTask>
				<IKMarkerTask name="LPSIS">
					<apply>true</apply> <weight>40</weight> </IKMarkerTask>
				<IKMarkerTask name="R_HJC">
					<apply>false</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="L_HJC">
					<apply>false</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="RFLE">
					<apply>true</apply> <weight>35</weight> </IKMarkerTask>
				<IKMarkerTask name="LFLE">
					<apply>true</apply> <weight>35</weight> </IKMarkerTask>
				<IKMarkerTask name="RFME">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="LFME">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="RFAL">
					<apply>true</apply> <weight>25</weight> </IKMarkerTask>
				<IKMarkerTask name="LFAL">
					<apply>true</apply> <weight>25</weight> </IKMarkerTask>
				<IKMarkerTask name="RTAM">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="LTAM">
					<apply>false</apply> <weight>0</weight> </IKMarkerTask>
				<IKMarkerTask name="RFMT1">
					<apply>true</apply> <weight>10</weight> </IKMarkerTask>
				<IKMarkerTask name="RFMT2">
					<apply>true</apply> <weight>10</weight> </IKMarkerTask>
				<IKMarkerTask name="LFMT1">
					<apply>true</apply> <weight>10</weight> </IKMarkerTask>
				<IKMarkerTask name="RFMT5">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="LFMT2">
					<apply>true</apply> <weight>10</weight> </IKMarkerTask>
				<IKMarkerTask name="LFMT5">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="RFCC">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>
				<IKMarkerTask name="LFCC">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>

				<!-- Lower-body tracking markers. -->
				<IKMarkerTask name="RTH1">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="RTH2">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="RTH3">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="RTH4">
					<apply>true</apply> <weight>5</weight> </IKMarkerTask>
				<IKMarkerTask name="RSK1">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="RSK2">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="RSK3">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="RSK4">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="LTH1">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>
				<IKMarkerTask name="LTH2">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>
				<IKMarkerTask name="LTH3">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>
				<IKMarkerTask name="LTH4">
					<apply>true</apply> <weight>15</weight> </IKMarkerTask>
				<IKMarkerTask name="LSK1">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="LSK2">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="LSK3">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
				<IKMarkerTask name="LSK4">
					<apply>true</apply> <weight>1</weight> </IKMarkerTask>
			</objects>
			<groups />
		</IKTaskSet>
		<!--TRC file (.trc) containing the time history of observations of marker positions.-->
		<marker_file>../ExpData/Mocap/trcResults/stw{trial}.trc</marker_file>
		<!--The name of the storage (.sto or .mot) file containing coordinate observations.Coordinate values from this file are included if there is a corresponding coordinate task. -->
		<coordinate_file>Unassigned</coordinate_file>
		<!--Time range over which the inverse kinematics problem is solved.-->
		<time_range> 0 5.62</time_range>
		<!--Flag (true or false) indicating whether or not to report marker errors from the inverse kinematics solution.-->
		<report_errors>true</report_errors>
		<!--Name of the motion file (.mot) to which the results should be written.-->
		<output_motion_file>./results_stw/ik_output_s{subject}_stw{trial}.mot</output_motion_file>
		<!--Flag indicating whether or not to report model marker locations in ground.-->
		<report_marker_locations>true</report_marker_locations>
	</InverseKinematicsTool>
</OpenSimDocument>

'''

# Create output directory if it doesn't exist

subject = "01"
output_dir = fr"D:\UG_Proj\Human Sitting to Walking Transitions\S{subject}\IK"
os.makedirs(output_dir, exist_ok=True)

# Generate files for trials 1 through 5
for trial in range(1, 6):
    # Fill in the template with current trial number
    xml_content = xml_template.format(trial=trial,subject=subject)
    
    # Create filename
    filename = f"ik_setup_S{subject}_stw{trial}.xml"
    filepath = os.path.join(output_dir, filename)
    
    # Write to file
    with open(filepath, 'w', encoding='UTF-8') as f:
        f.write(xml_content)
    
    print(f"Created: {filepath}")

print(f"\nAll files created successfully in '{output_dir}' directory!")