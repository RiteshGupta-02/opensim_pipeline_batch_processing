"""
Setup generation module for OpenSim pipeline.

Handles generation of scale, GRF, ID, SO, and IK setup files.
Can be imported as a module or run independently.
"""

import sys
import os
import subprocess
import shutil
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


# ---------------------------------------------------------------------------
# Logger configuration
# ---------------------------------------------------------------------------

def setup_logger(name: str = "setup_generator", level_name: str = "INFO") -> logging.Logger:
    """Configure and return a logger for this module."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _dbg(tag: str, msg: str, value=None):
    """Debug printer (always flushes so output is visible even mid-crash)."""
    sep = "-" * 60
    if value is not None:
        print(f"\n{sep}\n[DBG] [{tag}] {msg}\n      >> {value}\n{sep}", flush=True)
    else:
        print(f"\n{sep}\n[DBG] [{tag}] {msg}\n{sep}", flush=True)


def _run_script(script_name: str, args: list, cwd: Path, logger: logging.Logger) -> bool:
    """Run a helper setup script and return True on success."""
    # _dbg("SCRIPT", f"Running: {script_name}", f"cwd={cwd}  args={args}")
    result = subprocess.run(
        [sys.executable, script_name] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    # _dbg("SCRIPT", f"Return code: {result.returncode}", script_name)
    if result.stdout.strip():
        print(f"[DBG] [SCRIPT stdout]\n{result.stdout.strip()}", flush=True)
    if result.returncode != 0:
        print(f"[DBG] [SCRIPT stderr]\n{result.stderr.strip()}", flush=True)
        logger.error("Script %s failed:\n%s", script_name, result.stderr.strip())
        return False
    return True


def replace_subject_in_path(path_str: str, old_subj: str, new_subj: str) -> str:
    """Replace subject number in path string."""
    return path_str.replace(old_subj, new_subj)


def load_and_adapt_template(template_path: Path, subject_num: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Load template JSON and adapt it for the given subject.
    
    Args:
        template_path: Path to template JSON file
        subject_num: Subject number (e.g., '01')
        logger: Logger instance
    
    Returns:
        Adapted template dictionary with subject-specific paths
    """
    # _dbg("TEMPLATE", f"Loading template from", template_path)
    
    if not template_path.is_file():
        logger.error("Template file not found: %s", template_path)
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    with open(template_path, "r") as fh:
        template = json.load(fh)
    
    # _dbg("TEMPLATE", "Template loaded — keys", list(template.keys()))
    
    # Deep-copy template and substitute '01' -> subject_num everywhere
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
    
    # _dbg("TEMPLATE", "Template adapted for subject", subject_num)
    return adapted


def get_trial_by_name(adapted_template: Dict[str, Any], trial_name: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Extract a specific trial from the adapted template by trial name.
    
    Args:
        adapted_template: Adapted template dictionary
        trial_name: Name of the trial to find (e.g., 'stw1')
        logger: Logger instance
    
    Returns:
        Trial dictionary if found, None otherwise
    """
    mapped_trials = adapted_template.get("mapped_trials", [])
    
    # _dbg("TRIAL-LOOKUP", f"Looking for trial: {trial_name}", f"total trials: {len(mapped_trials)}")
    
    for trial in mapped_trials:
        trc = trial.get("trial_trc", "")
        trial_stem = Path(trc).stem
        
        if trial_stem == trial_name:
            # _dbg("TRIAL-LOOKUP", f"Found trial: {trial_name}", "MATCH")
            return trial
    
    # _dbg("TRIAL-LOOKUP", f"Trial not found: {trial_name}", "NO MATCH")
    logger.warning("Trial %s not found in template", trial_name)
    return None


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def generate_setups_if_needed(
    subject_num: str,
    subj_dir: Path,
    trial: Any,
    model_file: str,
    xml: str = "",
    trial_name: str = "",
    logger: Optional[logging.Logger] = None,
) -> bool:
    """
    Generate setup files for a subject trial if they don't already exist.
    
    Args:
        subject_num: Subject identifier (e.g., '01')
        subj_dir: Path to subject directory
        trial: Trial data dictionary or trial index (0 for scale, dict for others)
        model_file: Path to model file
        xml: Path to XML setup file
        trial_name: Name of the trial (e.g., 'scale', 'stw1')
        logger: Logger instance (optional, will create one if not provided)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if logger is None:
        logger = setup_logger()
    
    script_dir = Path(__file__).parent
    setup_dir = script_dir.parent / "setup_files"

    # _dbg("SETUP", f"generate_setups_if_needed called",
        #   f"subject={subject_num}  trial_name={trial_name!r}  subj_dir={subj_dir}")
    # _dbg("SETUP", "Setup scripts directory", setup_dir)
    # _dbg("SETUP", "Setup dir exists?", setup_dir.exists())
    # _dbg("SETUP", "Model file", model_file)

    # ---- Scale setup ------------------------------------------------
    if trial_name == "scale":
        if not Path(xml).exists():
            # _dbg("SCALE-SETUP", "Entering scale setup branch")
            # _dbg("SCALE-SETUP", "Scale XML path", xml)
            # _dbg("SCALE-SETUP", "Scale XML exists?", Path(xml).exists() if xml else "no path given")
            logger.info("Generating scale setup for subject %s", subject_num)
            ok = True ;'''_run_script(
                "scale_setup.py",
                [subject_num, str(subj_dir), str(model_file), str(xml)],
                setup_dir,
                logger,
            )
            # _dbg("SCALE-SETUP", "scale_setup.py result", "SUCCESS" if ok else "FAILED") '''
            return ok
        
    # ---- GRF setup --------------------------------------
    
    # _dbg("GRF-SETUP", "Entering GRF setup branch (stw1 trial)")
    try:
        grf_xml_path = trial.get("grf_xml", "")
        
        # _dbg("GRF-SETUP", "GRF XML path (to be generated)", grf_xml_path)
        logger.info("Generating GRF setup for subject %s", subject_num)
        mot_path = trial.get("trial_mot", "")
        trc_path = trial.get("trial_trc", "")
        # _dbg("GRF-SETUP", "GRF XML path", grf_xml_path)
        # _dbg("GRF-SETUP", "GRF XML exists?", Path(grf_xml_path).exists() if grf_xml_path else "no path")
        # _dbg("GRF-SETUP", "MOT path", mot_path)
        # _dbg("GRF-SETUP", "MOT exists?", Path(mot_path).exists() if mot_path else "no path")
        # _dbg("GRF-SETUP", "TRC path", trc_path)
        # _dbg("GRF-SETUP", "TRC exists?", Path(trc_path).exists() if trc_path else "no path")
        
        logger.info("Generating GRF setups for subject %s", subject_num)
        ok = _run_script(
            "grf_setup.py",
            [subject_num, str(subj_dir), str(mot_path), str(trc_path), str(grf_xml_path)],
            setup_dir,
            logger,
        )
        # _dbg("GRF-SETUP", "grf_setup.py result", "SUCCESS" if ok else "FAILED")
    except Exception as exc:
        # _dbg("GRF-SETUP", "EXCEPTION in GRF setup", str(exc))
        logger.error("GRF setup error for %s: %s", subject_num, exc)

    # ---- ID setup ---------------------------------------------------
    # _dbg("ID-SETUP", "Entering ID setup branch")
    try:
        id_xml_path = trial.get("id_xml", "")
        if not id_xml_path:
            # _dbg("ID-SETUP", "ID XML path (to be generated)", id_xml_path)
            logger.info("Generating ID setups for subject %s", subject_num)
        
            ok = True ;'''_run_script(
                "id_setup.py",
                [str(subj_dir), str(trial_name), str(model_file), str(id_xml_path)],
                setup_dir,
                logger,
            ) '''
            # _dbg("ID-SETUP", "id_setup.py result", "SUCCESS" if ok else "FAILED")
    except Exception as exc:
        # _dbg("ID-SETUP", "EXCEPTION in ID setup", str(exc))
        logger.error("ID setup error for %s: %s", subject_num, exc)

    # ---- SO setup ---------------------------------------------------
    # _dbg("SO-SETUP", "Entering SO setup branch")
    try:
        so_dir = subj_dir / "SO"
        so_xml_path = trial.get("so_xml", "")
        # _dbg("SO-SETUP", "SO dir", so_dir)
        # _dbg("SO-SETUP", "SO dir exists?", so_dir.exists())
        # _dbg("SO-SETUP", "SO XML path", so_xml_path)
        # _dbg("SO-SETUP", "SO XML exists?", Path(so_xml_path).exists() if so_xml_path else "no path")
        if not so_dir.exists() or not Path(so_xml_path).exists():
            # _dbg("SO-SETUP", "SO XML or dir missing — running SO_setup.py")
            logger.info("Generating SO setups for subject %s", subject_num)
            ok = True ;'''_run_script(
                "SO_setup.py",
                [str(subj_dir), str(trial_name), str(model_file), str(so_xml_path)],
                setup_dir,
                logger,
            ) '''
            # _dbg("SO-SETUP", "SO_setup.py result", "SUCCESS" if ok else "FAILED")
        else:
            # _dbg("SO-SETUP", "SO XML already exists — skipping SO_setup.py")
            pass

        actuators_src = Path(r"d:\RESEARCH\STW_dataset\Extracted\model\cmc_actuators.xml")
        actuators_dst = so_dir / "cmc_actuators.xml"
        # _dbg("SO-SETUP", "Actuators source", actuators_src)
        # _dbg("SO-SETUP", "Actuators source exists?", actuators_src.exists())
        # _dbg("SO-SETUP", "Actuators destination", actuators_dst)
        # _dbg("SO-SETUP", "Actuators destination exists?", actuators_dst.exists())
        if actuators_src.exists() and not actuators_dst.exists():
            so_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(actuators_src), str(actuators_dst))
            # _dbg("SO-SETUP", "Copied cmc_actuators.xml to", actuators_dst)
            logger.info("Copied cmc_actuators.xml to %s", actuators_dst)
    except Exception as exc:
        # _dbg("SO-SETUP", "EXCEPTION in SO setup", str(exc))
        logger.error("SO setup error for %s: %s", subject_num, exc)

    # ---- IK setup ---------------------------------------------------
    # _dbg("IK-SETUP", "Entering IK setup branch")
    try:
        ik_xml_path = trial.get("ik_xml", "")
        trc_path = trial.get("trial_trc", "")
        # _dbg("IK-SETUP", "IK XML path (to be generated)", ik_xml_path)
        # _dbg("IK-SETUP", "TRC path", trc_path)
        # _dbg("IK-SETUP", "TRC exists?", Path(trc_path).exists() if trc_path else "no path")
        if not ik_xml_path or not Path(trc_path).exists():
            # _dbg("IK-SETUP", "IK XML or TRC missing — running ik_setup.py")
            logger.info("Generating IK setups for subject %s", subject_num)
            ok = True ;'''_run_script(
                "ik_setup.py",
                [str(subj_dir), str(trial_name), str(model_file), str(trc_path), str(ik_xml_path)],
                setup_dir,
                logger,
            ) '''
            # _dbg("IK-SETUP", "ik_setup.py result", "SUCCESS" if ok else "FAILED")
    except Exception as exc:
        # _dbg("IK-SETUP", "EXCEPTION in IK setup", str(exc))
        logger.error("IK setup error for %s: %s", subject_num, exc)

    return True


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Standalone execution with hardcoded variables for debugging.
    Modify the variables below to test different scenarios.
    """
    
    # =========================================================================
    # HARDCODED CONFIGURATION (Change these to test)
    # =========================================================================
    
    SUBJECT_NUM = "03"  # Subject number (e.g., "01", "02", "03")
    TEMPLATE_JSON_PATH = Path(r"D:\student\MTech\opensim_pipeline_batch_processing\pipeline\template_map.json")  # Path to template.json
    TRIAL_NAME = "stw3"  # Trial name (e.g., "scale", "stw1", "stw2") — use "scale" for scale setup
    LOG_LEVEL = "DEBUG"  # Logging level (DEBUG, INFO, WARNING, ERROR)
    
    # Root directory (will be read from template if available)
    ROOT_DIR = Path(r"d:\student\MTech\opensim_pipeline_batch_processing")
    
    # =========================================================================
    # End of configuration — no changes needed below
    # =========================================================================
    
    sep = "=" * 70
    print(f"\n{sep}")
    print("[STANDALONE] generate_setup_files.py — Independent Execution")
    print(f"{sep}")
    print(f"  Subject Number      : {SUBJECT_NUM}")
    print(f"  Template JSON       : {TEMPLATE_JSON_PATH}")
    print(f"  Trial Name          : {TRIAL_NAME}")
    print(f"  Root Directory      : {ROOT_DIR}")
    print(f"  Log Level           : {LOG_LEVEL}")
    print(f"{sep}\n")
    
    # Setup logger
    logger = setup_logger(level_name=LOG_LEVEL)
    
    try:
        # =====================================================================
        # Load and adapt template
        # =====================================================================
        print("[STANDALONE] Loading and adapting template...")
        adapted_template = load_and_adapt_template(TEMPLATE_JSON_PATH, SUBJECT_NUM, logger)
        
        # Get root_dir from template if not set
        template_root_dir = adapted_template.get("root_dir", "")
        if template_root_dir:
            ROOT_DIR = Path(template_root_dir)
            # _dbg("MAIN", "Using root_dir from template", ROOT_DIR)
        
        # =====================================================================
        # Resolve subject directory
        # =====================================================================
        subj_dir = ROOT_DIR / f"S{SUBJECT_NUM}"
        # _dbg("MAIN", "Subject directory", subj_dir)
        # _dbg("MAIN", "Subject directory exists?", subj_dir.exists())
        
        if not subj_dir.exists():
            logger.error("Subject directory not found: %s", subj_dir)
            print(f"\n[STANDALONE] ERROR: Subject directory not found!")
            sys.exit(1)
        
        # =====================================================================
        # Resolve model file
        # =====================================================================
        model_file = adapted_template.get("model", "")
        # _dbg("MAIN", "Model file path", model_file)
        # _dbg("MAIN", "Model file exists?", Path(model_file).exists() if model_file else "no path")
        
        if not model_file:
            logger.error("Model file not found in template")
            print(f"\n[STANDALONE] ERROR: Model file not specified in template!")
            sys.exit(1)
        
        # =====================================================================
        # Resolve trial and setup
        # =====================================================================
        trial = {}
        xml_path = ""
        
        if TRIAL_NAME.lower() == "scale":
            print("[STANDALONE] Processing SCALE setup...")
            xml_path = adapted_template.get("scale_xml", "")
            # _dbg("MAIN", "Scale XML path", xml_path)
            
            success = generate_setups_if_needed(
                subject_num=SUBJECT_NUM,
                subj_dir=subj_dir,
                trial={},
                model_file=model_file,
                xml=xml_path,
                trial_name="scale",
                logger=logger,
            )
        else:
            print(f"[STANDALONE] Processing trial: {TRIAL_NAME}...")
            
            # Find the trial in the adapted template
            trial = get_trial_by_name(adapted_template, TRIAL_NAME, logger)
            
            if trial is None:
                logger.error("Trial %s not found in template", TRIAL_NAME)
                print(f"\n[STANDALONE] ERROR: Trial '{TRIAL_NAME}' not found in template!")
                print(f"[STANDALONE] Available trials:")
                mapped_trials = adapted_template.get("mapped_trials", [])
                for t in mapped_trials:
                    trc = t.get("trial_trc", "")
                    trial_stem = Path(trc).stem
                    print(f"              - {trial_stem}")
                sys.exit(1)
            
            # _dbg("MAIN", "Trial data found", f"keys: {list(trial.keys())}")
            
            # Get model file (might be scaled if available)
            model_for_trial = adapted_template.get("model", "")
            # _dbg("MAIN", "Model for trial", model_for_trial)
            
            success = generate_setups_if_needed(
                subject_num=SUBJECT_NUM,
                subj_dir=subj_dir,
                trial=trial,
                model_file=model_for_trial,
                xml="",
                trial_name=TRIAL_NAME,
                logger=logger,
            )
        
        # =====================================================================
        # Result
        # =====================================================================
        print(f"\n{sep}")
        if success:
            print("[STANDALONE] ✓ Setup generation completed successfully")
            print(f"{sep}\n")
            sys.exit(0)
        else:
            print("[STANDALONE] ✗ Setup generation completed with errors")
            print(f"{sep}\n")
            sys.exit(1)
    
    except Exception as exc:
        print(f"\n[STANDALONE] UNHANDLED EXCEPTION:")
        import traceback
        traceback.print_exc()
        print(f"\n{sep}\n")
        sys.exit(1)
