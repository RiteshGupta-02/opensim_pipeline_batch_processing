import json
import subprocess
import sys
from pathlib import Path
import multiprocessing as mp
import logging
import os
import opensim as osim

def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
BOLD_RED = "\033[1;91m" # Bold and bright red for extra attention
END = "\033[0m" # Reset code


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def replace_subject_in_path(path_str, old_subj, new_subj):
    """Replace subject number in path strings."""
    return path_str.replace(old_subj, new_subj)

def generate_setups_if_needed(subject_num, subj_dir,trial_name, dry_run=False):
    """Generate setup XMLs if they don't exist."""
    script_dir = Path(__file__).parent
    # GRF
    grf_dir = subj_dir / "ID" / "grf"
    if not grf_dir.exists() or not list(grf_dir.glob("*.xml")):
        logging.info(f"Generating GRF setups for subject {subject_num}")
        if not dry_run:
            result = subprocess.run(['python', 'grf_setup.py', subject_num, subj_dir], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"GRF setup failed for {subject_num}: {result.stderr}")
                return False

    # ID
    id_dir = subj_dir / "ID"
    if not id_dir.exists() or not list(id_dir.glob("id_setup_*.xml")):
        logging.info(f"Generating ID setups for subject {subject_num}")
        if not dry_run:
            result = subprocess.run(['python', 'id_setup.py', subject_num], cwd=str(script_dir), capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"ID setup failed for {subject_num}: {result.stderr}")
                return False

    # SO
    so_dir = subj_dir / "SO"
    if not so_dir.exists() or not list(so_dir.glob("so_setup_*.xml")):
        logging.info(f"Generating SO setups for subject {subject_num}")
        if not dry_run:
            result = subprocess.run(['python', 'SO_setup.py', subject_num], cwd=str(script_dir), capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"SO setup failed for {subject_num}: {result.stderr}")
                return False
        
    # IK
    ik_dir = subj_dir / "IK"
    if not ik_dir.exists() or not list(ik_dir.glob("ik_setup_*.xml")):
        logging.info(f"Generating IK setups for subject {subject_num}")
        if not dry_run:
            result = subprocess.run(['python', 'ik_setup.py', subject_num], cwd=str(script_dir), capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"IK setup failed for {subject_num}: {result.stderr}")
                return False

    return True

def run_pipeline_for_subject(subject_num, template, root_dir, dry_run=False):
    """Run the OpenSim pipeline for a single subject."""
    subj_dir = root_dir / f"S{subject_num}"
    if not subj_dir.exists():
        logging.warning(f"Subject {subject_num} directory not found; skipping.")
        return



    # Deep copy and adapt paths
    adapted = json.loads(json.dumps(template))
    for key, value in adapted.items():
        if isinstance(value, str):
            adapted[key] = replace_subject_in_path(value, "01", subject_num)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, str):
                            item[k] = replace_subject_in_path(v, "01", subject_num)
    # prRed(adapted)
    # Print adapted paths in dry mode
    if dry_run:
        logging.info(f"Adapted paths for subject {subject_num}: {json.dumps(adapted, indent=2)}")

    # Change to subject directory for relative paths
    scaled_model = "" #----------------for global use
    original_cwd = os.getcwd()
    try:
        os.chdir(str(subj_dir))
        logging.info(f"Processing subject {subject_num} in {subj_dir}")
        # osim.Logger_setLevelString("error")  # Suppress OpenSim output except errors

        # Run scaling if scale_xml exists
        scale_xml = Path(adapted['scale_xml'])
        os.chdir(str(scale_xml.parent))
        if scale_xml.exists():
            logging.info(f"Running scaling for subject {subject_num}")
            if not dry_run:
                try:
                    scale_tool = osim.ScaleTool(str(scale_xml))
                    scale_tool.createModel()
                    scaled_model = scale_tool.getMarkerPlacer().getOutputModelFileName()
                    success = scale_tool.run()
                    
                    if not success:
                        logging.error(f"Scaling failed for {subject_num}")
                        return
                except Exception as e:
                    logging.error(f"Scaling failed for {subject_num}: {str(e)}")
                    return
        else:
            logging.warning(f"Scale XML not found for {subject_num}; skipping scaling.")

        # Run for each trial
        for trial in adapted['mapped_trials']:
            trial_name = trial['trial_trc'].split('stw')[1].split('.')[0]  # Extract trial number, e.g., '1'
            logging.info(f"Processing trial {trial_name} for subject {subject_num}")
            # Generate setups if needed
            if not generate_setups_if_needed(subject_num, subj_dir, trial_name,dry_run):
                logging.error(f"Setup generation failed for {subject_num}; skipping.")
                return

            # IK
            ik_tool = None
            ik_xml = Path(trial['ik_xml'])
            os.chdir(str(ik_xml.parent))
            if ik_xml.exists():
                logging.info(f"Running IK for trial {trial_name}")
                if not dry_run:
                    try:
                        ik_tool = osim.InverseKinematicsTool(str(ik_xml))
                        ik_tool.set_model_file((os.path.join(scale_xml.parent,(scaled_model))))
                        ik_tool.setMarkerDataFileName(trial['trial_trc'])
                        success = True #ik_tool.run()                                              #do  it
                        if not success:
                            logging.error(f"IK failed for {trial_name}")
                            continue
                    except Exception as e:
                        logging.error(f"IK failed for {trial_name}: {str(e)}")
                        continue
            else:
                logging.warning(f"IK XML not found for {trial_name}; skipping IK.")
            # ID (requires GRF)
            id_xml = Path(trial['id_xml'])
            os.chdir(str(id_xml.parent))
            grf_xml = Path(trial['grf_xml'])
            print(id_xml.exists())
            print(grf_xml.exists())
            if id_xml.exists() and grf_xml.exists():
                logging.info(f"Running ID for trial {trial_name}")
                if not dry_run:
                    try:
                        id_tool = osim.InverseDynamicsTool(str(id_xml))
                        id_tool.setModelFileName((os.path.join(scale_xml.parent,(scaled_model))))
                        if ik_tool is not None:
                            id_tool.setCoordinatesFileName(os.path.join(ik_xml.parent, ik_tool.getOutputMotionFileName()))
                        id_tool.setExternalLoadsFileName(str(grf_xml))
                        success = id_tool.run()
                        if not success:
                            logging.error(f"ID failed for {trial_name}")
                            continue
                    except Exception as e:
                        logging.error(f"ID failed for {trial_name}: {str(e)}")
                        continue
            else:
                logging.warning(f"ID or GRF XML not found for {trial_name}; skipping ID.")

            # SO   
            so_xml = Path(trial['so_xml'])
            os.chdir(str(so_xml.parent))
            if so_xml.exists():
                logging.info(f"Running SO for trial {trial_name}")
                if not dry_run:
                    try:
                        so_tool = osim.AnalyzeTool(str(so_xml))
                        so_tool.setExternalLoadsFileName(str(grf_xml))
                        so_tool.setModelFilename((os.path.join(scale_xml.parent,(scaled_model))))
                        if ik_tool is not None:
                            so_tool.setCoordinatesFileName(ik_tool.getOutputMotionFileName())
                        success = True #so_tool.run()
                        if not success:
                            logging.error(f"SO failed for {trial_name}")
                    except Exception as e:
                        logging.error(f"SO failed for {trial_name}: {str(e)}")
            else:
                logging.warning(f"SO XML not found for {trial_name}; skipping SO.")

    finally:
        os.chdir(original_cwd)

def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py /path/to/template.json [--parallel] [--dry]")
        sys.exit(1)
    
    
    template_path = Path(sys.argv[1])
    if not template_path.exists():
        print(f"Template file {template_path} does not exist.")
        sys.exit(1)

    parallel = "--parallel" in sys.argv
    dry_run = "--dry" in sys.argv

    # Load template
    with open(template_path, 'r') as f:
        template = json.load(f)

    root_dir = Path(template["root_dir"])

    # Find subjects
    subjects = []
    subj_num = 1
    while True:
        subj_str = f"{subj_num:02d}"
        subj_dir = root_dir / f"S{subj_str}"
        if not subj_dir.exists():
            break
        subjects.append(subj_str)
        subj_num += 1

    if not subjects:
        print("No subjects found.")
        sys.exit(1)

    logging.info(f"Found subjects: {subjects}")
    y = input(f"Proceed to run pipeline for {len(subjects)} subjects? \n Enter to continue: ")

    if parallel:
        logging.info("Running in parallel mode.")
        with mp.Pool(processes=min(mp.cpu_count()-2, len(subjects))) as pool:
            pool.starmap(run_pipeline_for_subject, [(s, template, root_dir, dry_run) for s in subjects])
    else:
        logging.info("Running in sequential mode.")
        for s in subjects:
            if s == '02':
                print(f"Starting subject {s}...")
                run_pipeline_for_subject(s, template, root_dir, dry_run)

    logging.info("Pipeline completed.")

if __name__ == "__main__":
    main()

    