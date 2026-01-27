import os
import sys
import csv
from xml.etree import ElementTree as ET
from pathlib import Path

def create_scale_setup(subject_id, mass, height, subj_dir):
    """Create a scale setup XML file for a subject."""
    
    # Template XML structure
    xml_template = """<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40500">
    <ScaleTool name="{subject_id}">
        <mass>{mass}</mass>
        <height>{height}</height>
        <age>0</age>
        <notes>Auto-generated scale setup for {subject_id}</notes>
        <GenericModelMaker>
            <model_file>..\\..\\model\\RajagopalLa2023_LL-stw_adjustedWieghts.osim</model_file>
            <marker_set_file>Unassigned</marker_set_file>
        </GenericModelMaker>
        <ModelScaler>
            <apply>true</apply>
            <scaling_order> measurements</scaling_order>
            <MeasurementSet name="RajagopalLa2023_LL-stw_adjustedWieghts">
                <objects>
                    <Measurement name="pelvis">
                        <apply>true</apply>
                        <MarkerPairSet>
                            <objects>
                                <MarkerPair>
                                    <markers> RASIS LASIS</markers>
                                </MarkerPair>
                            </objects>
                            <groups />
                        </MarkerPairSet>
                        <BodyScaleSet>
                            <objects>
                                <BodyScale name="pelvis">
                                    <axes> X Y Z</axes>
                                </BodyScale>
                            </objects>
                            <groups />
                        </BodyScaleSet>
                    </Measurement>
                </objects>
                <groups />
            </MeasurementSet>
            <marker_file>../ExpData/Mocap/trcResults/static.trc</marker_file>
            <time_range> 1 2.9500000000000001776</time_range>
            <preserve_mass_distribution>true</preserve_mass_distribution>
            <output_model_file>{subject_id}_scaledOnly.osim</output_model_file>
            <output_scale_file>{subject_id}_scaleSet_applied.xml</output_scale_file>
        </ModelScaler>
        <MarkerPlacer>
            <apply>true</apply>
            <IKTaskSet name="gait2392_Scale">
                <objects />
                <groups />
            </IKTaskSet>
            <marker_file>../ExpData/Mocap/trcResults/static.trc</marker_file>
            <time_range> 1 2.9500000000000001776</time_range>
            <output_motion_file>{subject_id}_static_output.mot</output_motion_file>
            <output_model_file>{subject_id}_simbody_scaled.osim</output_model_file>
            <output_marker_file>{subject_id}_marker_scaled.xml</output_marker_file>
            <max_marker_movement>-1</max_marker_movement>
        </MarkerPlacer>
    </ScaleTool>
</OpenSimDocument>"""
    
    # Format the XML with subject data
    xml_content = xml_template.format(
        subject_id=subject_id,
        mass=mass,
        height=height
    )
    
    # Write to file
    output_file = os.path.join(subj_dir, f"scale_{subject_id}_setup.xml")
    os.makedirs(subj_dir, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(xml_content)
    
    print(f"Created: {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python scale_setup.py <output_directory>")
        sys.exit(1)
    
    csv_file = 'subject_data.csv'  # CSV file with subject_id, mass, height
    output_dir = Path(sys.argv[1])
    
    # Read CSV file
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['subject_id'] == output_dir.name:
                    subject_id = row['subject_id']
                    mass = row['mass']
                    height = row['height']
                    
                    subj_dir = os.path.join(output_dir, subject_id)
                    create_scale_setup(subject_id, mass, height, subj_dir)
            # for row in reader:
            #     subject_id = row['subject_id']
            #     mass = row['mass']
            #     height = row['height']
                
            #     subj_dir = os.path.join(output_dir, subject_id)
            #     create_scale_setup(subject_id, mass, height, subj_dir)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required column {e} in CSV file")
        sys.exit(1)

if __name__ == "__main__":
    main()