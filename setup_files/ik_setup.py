import os

# Template XML content
xml_template = rf'''<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40500">
	<InverseKinematicsTool name="{subject:02d}_stw{trial}">
		<!--Name of the directory where results are written. Be default this is the directory in which the setup file is be  executed.-->
		<results_directory>./results_stw</results_directory>
		<!--Name/path to the xml .osim file.-->
		<model_file>../Scale/subject_scaled_walk.osim</model_file>
		<!--The relative weighting of kinematic constraint errors. By default this is Infinity, which means constraints are strictly enforced as part of the optimization and are not appended to the objective (cost) function. Any other non-zero positive scalar is the penalty factor for constraint violations.-->
		<constraint_weight>Inf</constraint_weight>
		<!--The accuracy of the solution in absolute terms, i.e. the number of significant digits to which the solution can be trusted. Default 1e-5.-->
		<accuracy>1.0000000000000001e-05</accuracy>
		<!--The time range for the study.-->
		<time_range>0 5.4550000000000001</time_range>
		<!--Name of the resulting inverse kinematics motion (.mot) file.-->
		<output_motion_file>D:\student\MTech\Sakshi\STW\S{subject:02d}\IK\ik_output_stw{trial}_S{subject:02d}.mot</output_motion_file>
		<!--Flag (true or false) indicating whether or not to report errors from the inverse kinematics solution. Default is true.-->
		<report_errors>true</report_errors>
		<!--Markers and coordinates to be considered (tasks) and their weightings. The sum of weighted-squared task errors composes the cost function.-->
		<IKTaskSet>
			<objects>
				<IKMarkerTask name="RASIS">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>100</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LASIS">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>100</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RPSIS">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>50</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LPSIS">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>50</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RTH1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RTH2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RTH3">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RTH4">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFLE">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFAL">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RSK1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RSK2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RSK4">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RSK3">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFCC">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFMT1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFMT2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="RFMT5">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LTH1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LTH2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LTH3">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LTH4">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFLE">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LSK1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LSK2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LSK4">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LSK3">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFAL">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFCC">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>15</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFMT1">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFMT2">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
				<IKMarkerTask name="LFMT5">
					<!--Whether or not this task will be used during inverse kinematics solve, default is true.-->
					<apply>true</apply>
					<!--Weight given to the task when solving inverse kinematics problems, default is 0.-->
					<weight>10</weight>
				</IKMarkerTask>
			</objects>
			<groups />
		</IKTaskSet>
		<!--TRC file (.trc) containing the time history of observations of marker positions obtained during a motion capture experiment. Markers in this file that have a corresponding task and model marker are included.-->
		<marker_file>../ExpData/Mocap/trcResults/stw{trial}.trc</marker_file>
		<!--The name of the storage (.sto or .mot) file containing the time history of coordinate observations. Coordinate values from this file are included if there is a corresponding model coordinate and task. -->
		<coordinate_file>Unassigned</coordinate_file>
		<!--Flag indicating whether or not to report model marker locations. Note, model marker locations are expressed in Ground.-->
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