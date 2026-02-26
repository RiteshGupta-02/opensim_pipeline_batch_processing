"""
CLI Pipeline for OpenSim processing.

Usage:
    python pipeline_cli.py --template path/to/template.json [OPTIONS]

Options:
    --template      Path to template JSON (required)
    --subjects      Comma-separated subject numbers e.g. 01,02,05
                    If omitted, all discovered subjects under root_dir are used.
    --trials        Comma-separated trial names e.g. stw1,stw2
                    Applied to all selected subjects. If omitted, all trials run.
    --steps         Comma-separated steps: scale,ik,id,so  (default: all)
    --parallel      Enable parallel processing across physical CPU cores
    --cores         Number of cores to use (default: physical_core_count - 1, min 1)
    --log-level     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    --log-file      Optional path to write log output to a file

Example:
    python pipeline_cli.py --template D:/study/template.json --subjects 01,02 --steps ik,id --parallel
"""

import sys
import os
import json
import logging
import subprocess
import shutil
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Physical core detection (psutil preferred, graceful fallback)
# ---------------------------------------------------------------------------
try:
    import psutil
    def physical_core_count() -> int:
        count = psutil.cpu_count(logical=False)
        return count if count and count > 0 else 1
except ImportError:
    def physical_core_count() -> int:
        logical = os.cpu_count() or 2
        return max(1, logical // 2)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def replace_subject_in_path(path_str: str, old_subj: str, new_subj: str) -> str:
    return path_str.replace(old_subj, new_subj)


def setup_logging(level_name: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configure root logger for CLI use."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    handlers: list = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    return logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Pipeline Engine
# ---------------------------------------------------------------------------

class PipelineEngine:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Debug printer  (always flushes so output is visible even mid-crash)
    # ------------------------------------------------------------------
    @staticmethod
    def _dbg(tag: str, msg: str, value=None):
        sep = "-" * 60
        if value is not None:
            print(f"\n{sep}\n[DBG] [{tag}] {msg}\n      >> {value}\n{sep}", flush=True)
        else:
            print(f"\n{sep}\n[DBG] [{tag}] {msg}\n{sep}", flush=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_script(self, script_name: str, args: List[str], cwd: Path) -> bool:
        """Run a helper setup script and return True on success."""
        self._dbg("SCRIPT", f"Running: {script_name}", f"cwd={cwd}  args={args}")
        result = subprocess.run(
            [sys.executable, script_name] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        self._dbg("SCRIPT", f"Return code: {result.returncode}", script_name)
        if result.stdout.strip():
            print(f"[DBG] [SCRIPT stdout]\n{result.stdout.strip()}", flush=True)
        if result.returncode != 0:
            print(f"[DBG] [SCRIPT stderr]\n{result.stderr.strip()}", flush=True)
            self.logger.error("Script %s failed:\n%s", script_name, result.stderr.strip())
            return False
        return True

    def generate_setups_if_needed(
        self,
        subject_num: str,
        subj_dir: Path,
        trial,
        model_file,
        xml: str = "",
        trial_name: str = "",
    ) -> bool:
        script_dir = Path(__file__).parent
        setup_dir = script_dir.parent / "setup_files"

        self._dbg("SETUP", f"generate_setups_if_needed called",
                  f"subject={subject_num}  trial_name={trial_name!r}  subj_dir={subj_dir}")
        self._dbg("SETUP", "Setup scripts directory", setup_dir)
        self._dbg("SETUP", "Setup dir exists?", setup_dir.exists())
        self._dbg("SETUP", "Model file", model_file)

        # ---- Scale setup ------------------------------------------------
        if trial_name == "scale":
            self._dbg("SCALE-SETUP", "Entering scale setup branch")
            self._dbg("SCALE-SETUP", "Scale XML path", xml)
            self._dbg("SCALE-SETUP", "Scale XML exists?", Path(xml).exists() if xml else "no path given")
            self.logger.info("Generating scale setup for subject %s", subject_num)
            ok = self._run_script(
                "scale_setup.py",
                [subject_num, str(subj_dir), str(model_file), str(xml)],
                setup_dir,
            )
            self._dbg("SCALE-SETUP", "scale_setup.py result", "SUCCESS" if ok else "FAILED")
            return ok
            
        # ---- GRF setup --------------------------------------
        
        self._dbg("GRF-SETUP", "Entering GRF setup branch (stw1 trial)")
        try:
            grf_xml_path = trial.get("grf_xml", "")
            mot_path = trial.get("trial_mot", "")
            trc_path = trial.get("trial_trc", "")
            self._dbg("GRF-SETUP", "GRF XML path", grf_xml_path)
            self._dbg("GRF-SETUP", "GRF XML exists?", Path(grf_xml_path).exists() if grf_xml_path else "no path")
            self._dbg("GRF-SETUP", "MOT path", mot_path)
            self._dbg("GRF-SETUP", "MOT exists?", Path(mot_path).exists() if mot_path else "no path")
            self._dbg("GRF-SETUP", "TRC path", trc_path)
            self._dbg("GRF-SETUP", "TRC exists?", Path(trc_path).exists() if trc_path else "no path")
            if not Path(grf_xml_path).exists() or not Path(mot_path).exists() or not Path(trc_path).exists():
                self._dbg("GRF-SETUP", "Missing GRF/MOT/TRC path — skipping GRF setup")
                self.logger.warning("Missing GRF/MOT/TRC path for trial %s; skipping GRF setup.", trial_name)  # Not an error if GRF setup is just not applicable for this trial
                self.logger.info("Generating GRF setups for subject %s", subject_num)
                ok = self._run_script(
                    "grf_setup.py",
                    [subject_num, str(subj_dir), str(trial_name), str(mot_path), str(trc_path), str(grf_xml_path)],
                    setup_dir,
                )
                self._dbg("GRF-SETUP", "grf_setup.py result", "SUCCESS" if ok else "FAILED")
        except Exception as exc:
            self._dbg("GRF-SETUP", "EXCEPTION in GRF setup", str(exc))
            self.logger.error("GRF setup error for %s: %s", subject_num, exc)

        # ---- ID setup ---------------------------------------------------
        self._dbg("ID-SETUP", "Entering ID setup branch")
        try:
            id_xml_path = trial.get("id_xml", "")
            if not id_xml_path:
                self._dbg("ID-SETUP", "ID XML path (to be generated)", id_xml_path)
                self.logger.info("Generating ID setups for subject %s", subject_num)
            
                ok = self._run_script(
                    "id_setup.py",
                    [str(subj_dir), str(trial_name), str(model_file), str(id_xml_path)],
                    setup_dir,
                )
                self._dbg("ID-SETUP", "id_setup.py result", "SUCCESS" if ok else "FAILED")
        except Exception as exc:
            self._dbg("ID-SETUP", "EXCEPTION in ID setup", str(exc))
            self.logger.error("ID setup error for %s: %s", subject_num, exc)

        # ---- SO setup ---------------------------------------------------
        self._dbg("SO-SETUP", "Entering SO setup branch")
        try:
            so_dir = subj_dir / "SO"
            so_xml_path = trial.get("so_xml", "")
            self._dbg("SO-SETUP", "SO dir", so_dir)
            self._dbg("SO-SETUP", "SO dir exists?", so_dir.exists())
            self._dbg("SO-SETUP", "SO XML path", so_xml_path)
            self._dbg("SO-SETUP", "SO XML exists?", Path(so_xml_path).exists() if so_xml_path else "no path")
            if not so_dir.exists() or not Path(so_xml_path).exists():
                self._dbg("SO-SETUP", "SO XML or dir missing — running SO_setup.py")
                self.logger.info("Generating SO setups for subject %s", subject_num)
                ok = self._run_script(
                    "SO_setup.py",
                    [str(subj_dir), str(trial_name), str(model_file), str(so_xml_path)],
                    setup_dir,
                )
                self._dbg("SO-SETUP", "SO_setup.py result", "SUCCESS" if ok else "FAILED")
            else:
                self._dbg("SO-SETUP", "SO XML already exists — skipping SO_setup.py")

            actuators_src = Path(r"d:\RESEARCH\STW_dataset\Extracted\model\cmc_actuators.xml")
            actuators_dst = so_dir / "cmc_actuators.xml"
            self._dbg("SO-SETUP", "Actuators source", actuators_src)
            self._dbg("SO-SETUP", "Actuators source exists?", actuators_src.exists())
            self._dbg("SO-SETUP", "Actuators destination", actuators_dst)
            self._dbg("SO-SETUP", "Actuators destination exists?", actuators_dst.exists())
            if actuators_src.exists() and not actuators_dst.exists():
            # if actuators_src.exists():
                so_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(actuators_src), str(actuators_dst))
                self._dbg("SO-SETUP", "Copied cmc_actuators.xml to", actuators_dst)
                self.logger.info("Copied cmc_actuators.xml to %s", actuators_dst)
        except Exception as exc:
            self._dbg("SO-SETUP", "EXCEPTION in SO setup", str(exc))
            self.logger.error("SO setup error for %s: %s", subject_num, exc)

        # ---- IK setup ---------------------------------------------------
        self._dbg("IK-SETUP", "Entering IK setup branch")
        try:
            ik_xml_path = trial.get("ik_xml", "")
            trc_path = trial.get("trial_trc", "")
            self._dbg("IK-SETUP", "IK XML path (to be generated)", ik_xml_path)
            self._dbg("IK-SETUP", "TRC path", trc_path)
            self._dbg("IK-SETUP", "TRC exists?", Path(trc_path).exists() if trc_path else "no path")
            if not ik_xml_path or not Path(trc_path).exists():
                self._dbg("IK-SETUP", "IK XML or TRC missing — running ik_setup.py")
                self.logger.info("Generating IK setups for subject %s", subject_num)
                ok = self._run_script(
                    "ik_setup.py",
                    [str(subj_dir), str(trial_name), str(model_file), str(trc_path), str(ik_xml_path)],
                    setup_dir,
                )
                self._dbg("IK-SETUP", "ik_setup.py result", "SUCCESS" if ok else "FAILED")
        except Exception as exc:
            self._dbg("IK-SETUP", "EXCEPTION in IK setup", str(exc))
            self.logger.error("IK setup error for %s: %s", subject_num, exc)

        return True

    # ------------------------------------------------------------------
    # Main per-subject runner
    # ------------------------------------------------------------------

    def run_pipeline_for_subject(
        self,
        subject_num: str,
        template: dict,
        root_dir: Path,
        enabled_steps: dict,
        selected_trials: Optional[List[str]] = None,
    ) -> bool:
        # Defer opensim import so each spawned process loads it cleanly
        import opensim as osim  # type: ignore

        self._dbg("SUBJECT", f"===== START subject {subject_num} =====")
        self._dbg("SUBJECT", "enabled_steps", enabled_steps)
        self._dbg("SUBJECT", "selected_trials", selected_trials or "all")
        self._dbg("SUBJECT", "root_dir", root_dir)

        subj_dir = root_dir / f"S{subject_num}"
        self._dbg("SUBJECT", "subj_dir", subj_dir)
        self._dbg("SUBJECT", "subj_dir exists?", subj_dir.exists())

        osim.Logger.setLevelString("Warn")

        if not subj_dir.exists():
            self.logger.warning("Subject %s directory not found; skipping.", subject_num)
            return False

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

        self._dbg("SUBJECT", "Adapted template keys", list(adapted.keys()))
        self._dbg("SUBJECT", "model path (adapted)", adapted.get("model", "NOT SET"))
        self._dbg("SUBJECT", "model file exists?",
                  Path(adapted.get("model", "")).exists() if adapted.get("model") else "no path")
        self._dbg("SUBJECT", "static_trc (adapted)", adapted.get("static_trc", "NOT SET"))
        self._dbg("SUBJECT", "static_trc exists?",
                  Path(adapted.get("static_trc", "")).exists() if adapted.get("static_trc") else "no path")
        self._dbg("SUBJECT", "scale_xml (adapted)", adapted.get("scale_xml", "NOT SET"))
        self._dbg("SUBJECT", "mapped_trials count", len(adapted.get("mapped_trials", [])))

        original_cwd = os.getcwd()
        self._dbg("SUBJECT", "original working directory", original_cwd)

        try:
            self.logger.info("Processing subject %s in %s", subject_num, subj_dir)

            scale_xml: Optional[Path] = None
            scaled_model: Optional[str] = None

            # ================================================================
            # SCALING
            # ================================================================
            self._dbg("SCALE", f"Step enabled? {enabled_steps.get('scale', True)}")

            if enabled_steps.get("scale", True):
                scale_dir = subj_dir / "scale"
                self._dbg("SCALE", "scale_dir", scale_dir)
                self._dbg("SCALE", "scale_dir exists (before mkdir)?", scale_dir.exists())
                scale_dir.mkdir(exist_ok=True)
                self._dbg("SCALE", "scale_dir exists (after mkdir)?", scale_dir.exists())

                scale_xml = Path(adapted.get("scale_xml", ""))
                self._dbg("SCALE", "scale_xml path", scale_xml)
                self._dbg("SCALE", "scale_xml exists (before setup)?", scale_xml.exists())
                if not scale_xml.exists():

                    self.generate_setups_if_needed(
                        subject_num=subject_num,
                        subj_dir=subj_dir,
                        trial=0,
                        model_file=adapted.get("model", ""),
                        xml=str(scale_xml),
                        trial_name="scale",
                    )

                self._dbg("SCALE", "scale_xml exists (after setup)?", scale_xml.exists())

                if scale_xml.exists():
                    self._dbg("SCALE", "Changing cwd to scale_xml parent", scale_xml.parent)
                    os.chdir(str(scale_xml.parent))
                    self._dbg("SCALE", "Current working directory", os.getcwd())
                    self.logger.info("Running scaling for subject %s", subject_num)
                    try:
                        self._dbg("SCALE", "Loading ScaleTool from", scale_xml)
                        scale_tool = osim.ScaleTool(str(scale_xml))
                        scale_tool.setPathToSubject("")
                        scaled_model = scale_tool.getMarkerPlacer().getOutputModelFileName()
                        self._dbg("SCALE", "Output scaled model filename", scaled_model)

                        generic_model = adapted.get("model", "")
                        static_trc = adapted.get("static_trc", "")
                        self._dbg("SCALE", "Setting generic model", generic_model)
                        self._dbg("SCALE", "Setting static TRC", static_trc)

                        scale_tool.getGenericModelMaker().setModelFileName(generic_model)
                        scale_tool.getMarkerPlacer().setMarkerFileName(static_trc)
                        scale_tool.getModelScaler().setMarkerFileName(static_trc)
                        scale_tool.printToXML(str(scale_xml))
                        self._dbg("SCALE", "ScaleTool XML saved, now running tool...")

                        success = scale_tool.run()
                        self._dbg("SCALE", "ScaleTool.run() returned", success)

                        if not success:
                            self.logger.error("Scaling failed for subject %s", subject_num)
                            return False

                        full_scaled_path = Path(scale_xml.parent) / scaled_model
                        self._dbg("SCALE", "Expected scaled model output path", full_scaled_path)
                        self._dbg("SCALE", "Scaled model file exists?", full_scaled_path.exists())

                    except Exception as exc:
                        self._dbg("SCALE", "EXCEPTION during scaling", str(exc))
                        self.logger.error("Scaling exception for subject %s: %s", subject_num, exc)
                        return False
                else:
                    self._dbg("SCALE", "scale_xml not found — scaling skipped")
                    self.logger.warning(
                        "Scale XML not found for subject %s; skipping scaling.", subject_num
                    )

            # ================================================================
            # PER-TRIAL LOOP
            # ================================================================
            mapped_trials = adapted.get("mapped_trials", [])
            self._dbg("TRIALS", f"Total mapped trials to iterate", len(mapped_trials))

            for trial_idx, trial in enumerate(mapped_trials):
                trc = replace_subject_in_path(trial.get("trial_trc", ""), "01", subject_num)
                trial_name = Path(trc).stem

                self._dbg("TRIAL", f"--- Trial [{trial_idx + 1}/{len(mapped_trials)}]: {trial_name} ---")
                self._dbg("TRIAL", "trial_trc path", trc)
                self._dbg("TRIAL", "trial_trc exists?", Path(trc).exists())

                if selected_trials and trial_name not in selected_trials:
                    self._dbg("TRIAL", f"Skipping {trial_name} — not in selected_trials", selected_trials)
                    self.logger.debug("Skipping trial %s (not in selection)", trial_name)
                    continue

                self.logger.info("Processing trial %s for subject %s", trial_name, subject_num)

                model_for_trial = (
                    str(Path(scale_xml.parent) / scaled_model)
                    if scale_xml and scaled_model
                    else adapted.get("model", "")
                )
                self._dbg("TRIAL", "model_for_trial", model_for_trial)
                self._dbg("TRIAL", "model_for_trial exists?", Path(model_for_trial).exists() if model_for_trial else "no path")

                setup_ok = self.generate_setups_if_needed(
                    subject_num=subject_num,
                    subj_dir=subj_dir,
                    trial=trial,
                    trial_name=trial_name,
                    model_file=model_for_trial,
                )
                self._dbg("TRIAL", "generate_setups_if_needed returned", setup_ok)

                if not setup_ok:
                    self.logger.error(
                        "Setup generation failed for subject %s; skipping trial %s.",
                        subject_num, trial_name,
                    )
                    continue

                ik_tool = None

                # ============================================================
                # IK
                # ============================================================
                self._dbg("IK", f"Step enabled? {enabled_steps.get('ik', True)}")

                if enabled_steps.get("ik", True):
                    ik_xml = Path(
                        replace_subject_in_path(trial.get("ik_xml", ""), "01", subject_num)
                    )
                    self._dbg("IK", "ik_xml path", ik_xml)
                    self._dbg("IK", "ik_xml exists?", ik_xml.exists())

                    if ik_xml.exists():
                        self._dbg("IK", "Changing cwd to ik_xml parent", ik_xml.parent)
                        os.chdir(str(ik_xml.parent))
                        self._dbg("IK", "Current working directory", os.getcwd())
                        self.logger.info("Running IK for trial %s", trial_name)
                        try:
                            self._dbg("IK", "Loading InverseKinematicsTool from", ik_xml)
                            ik_tool = osim.InverseKinematicsTool(str(ik_xml))

                            self._dbg("IK", "Setting model file", model_for_trial)
                            ik_tool.set_model_file(model_for_trial)

                            marker_file = trial["trial_trc"]
                            self._dbg("IK", "Setting marker data file", marker_file)
                            self._dbg("IK", "Marker file exists?", Path(marker_file).exists())
                            ik_tool.setMarkerDataFileName(marker_file)
                            ik_tool.printToXML(str(ik_xml))

                            self._dbg("IK", "IK tool configured, running...")
                            success = ik_tool.run()
                            self._dbg("IK", "IK.run() returned", success)

                            if not success:
                                self.logger.error("IK failed for trial %s", trial_name)
                                continue

                            output_mot = ik_tool.getOutputMotionFileName()
                            self._dbg("IK", "IK output motion file", output_mot)
                            self._dbg("IK", "IK output exists?",
                                      Path(ik_xml.parent / output_mot).exists() if output_mot else "no filename")

                        except Exception as exc:
                            self._dbg("IK", "EXCEPTION during IK", str(exc))
                            self.logger.error("IK exception for trial %s: %s", trial_name, exc)
                            continue
                    else:
                        self._dbg("IK", "ik_xml not found — IK skipped for this trial")
                        self.logger.warning("IK XML not found for %s; skipping.", trial_name)
                        continue

                # ============================================================
                # ID
                # ============================================================
                self._dbg("ID", f"Step enabled? {enabled_steps.get('id', True)}")

                if enabled_steps.get("id", True):
                    id_xml = Path(
                        replace_subject_in_path(trial.get("id_xml", ""), "01", subject_num)
                    )
                    grf_xml = Path(
                        replace_subject_in_path(trial.get("grf_xml", ""), "01", subject_num)
                    )
                    self._dbg("ID", "id_xml path", id_xml)
                    self._dbg("ID", "id_xml exists?", id_xml.exists())
                    self._dbg("ID", "grf_xml path", grf_xml)
                    self._dbg("ID", "grf_xml exists?", grf_xml.exists())

                    if id_xml.exists():
                        self._dbg("ID", "Changing cwd to id_xml parent", id_xml.parent)
                        os.chdir(str(id_xml.parent))
                        self._dbg("ID", "Loading InverseDynamicsTool from", id_xml)
                        id_tool = osim.InverseDynamicsTool(str(id_xml))
                    else:
                        self._dbg("ID", "id_xml missing — creating empty InverseDynamicsTool")
                        id_tool = osim.InverseDynamicsTool()

                    if grf_xml.exists():
                        try:
                            self._dbg("ID", "Setting model", model_for_trial)
                            id_tool.setModelFileName(model_for_trial)

                            mot_file = ik_tool.getOutputMotionFileName() if ik_tool else ""
                            self._dbg("ID", "IK output motion file to use for ID", mot_file)
                            self._dbg("ID", "mot_file exists?",
                                      Path(mot_file).exists() if mot_file else "no filename")

                            table = osim.TimeSeriesTable(mot_file)
                            start = table.getIndependentColumn()[0]
                            end = table.getIndependentColumn()[-1]
                            self._dbg("ID", "Time range from motion file", f"start={start:.4f}  end={end:.4f}")

                            id_tool.setStartTime(start)
                            id_tool.setEndTime(end)

                            if ik_tool:
                                coord_path = str(Path(ik_xml.parent) / mot_file) if id_xml.exists() else mot_file
                                self._dbg("ID", "setCoordinatesFileName", coord_path)
                                self._dbg("ID", "coordinates file exists?", Path(coord_path).exists())
                                id_tool.setCoordinatesFileName(coord_path)

                            self._dbg("ID", "setExternalLoadsFileName", grf_xml)
                            id_tool.setExternalLoadsFileName(str(grf_xml))
                            id_tool.printToXML(str(id_xml))

                            self._dbg("ID", "ID tool configured, running...")
                            success = id_tool.run()
                            self._dbg("ID", "ID.run() returned", success)

                            if not success:
                                self.logger.error("ID failed for trial %s", trial_name)
                                continue
                        except Exception as exc:
                            self._dbg("ID", "EXCEPTION during ID", str(exc))
                            self.logger.error("ID exception for trial %s: %s", trial_name, exc)
                            continue
                    else:
                        self._dbg("ID", "grf_xml missing — ID skipped")
                        self.logger.info("GRF file missing for trial %s; skipping ID.", trial_name)
                        continue

                # ============================================================
                # SO
                # ============================================================
                self._dbg("SO", f"Step enabled? {enabled_steps.get('so', True)}")

                if enabled_steps.get("so", True):
                    so_xml = Path(
                        replace_subject_in_path(trial.get("so_xml", ""), "01", subject_num)
                    )
                    # Refresh grf_xml binding for SO (may not have been set if ID was skipped)
                    grf_xml = Path(
                        replace_subject_in_path(trial.get("grf_xml", ""), "01", subject_num)
                    )
                    self._dbg("SO", "so_xml path", so_xml)
                    self._dbg("SO", "so_xml exists?", so_xml.exists())
                    self._dbg("SO", "grf_xml path", grf_xml)
                    self._dbg("SO", "grf_xml exists?", grf_xml.exists())

                    if so_xml.exists():
                        self._dbg("SO", "Changing cwd to so_xml parent", so_xml.parent)
                        os.chdir(str(so_xml.parent))
                        so_tool = osim.AnalyzeTool(str(so_xml))
                        self._dbg("SO", "Model filename", so_tool.getModelFilename())
                        self._dbg("SO", "Current working directory", os.getcwd())
                        self.logger.info("Running SO for trial %s", trial_name)
                        try:
                            self._dbg("SO", "Loading AnalyzeTool from", so_xml)
                            so_tool = osim.AnalyzeTool(str(so_xml))

                            self._dbg("SO", "setExternalLoadsFileName", grf_xml)
                            so_tool.setExternalLoadsFileName(str(grf_xml))

                            self._dbg("SO", "setModel", model_for_trial)
                            so_tool.setModelFilename(model_for_trial)

                            if ik_tool:
                                ik_out = ik_tool.getOutputMotionFileName()
                                self._dbg("SO", "setCoordinatesFileName (from IK output)", ik_out)
                                so_tool.setCoordinatesFileName(ik_out)
                            else:
                                self._dbg("SO", "ik_tool is None — coordinates not set from IK")

                            so_tool.printToXML(str(so_xml))
                            self._dbg("SO", "SO tool configured, running...")

                            success = so_tool.run()
                            self._dbg("SO", "SO.run() returned", success)

                            if not success:
                                self.logger.error("SO failed for trial %s", trial_name)
                        except Exception as exc:
                            self._dbg("SO", "EXCEPTION during SO", str(exc))
                            self.logger.error("SO exception for trial %s: %s", trial_name, exc)
                    else:
                        self._dbg("SO", "so_xml not found — SO skipped for this trial")
                        self.logger.warning("SO XML not found for %s; skipping.", trial_name)
                        continue

                self._dbg("TRIAL", f"--- Trial {trial_name} complete ---")

            self._dbg("SUBJECT", f"===== END subject {subject_num} — all trials processed =====")

        finally:
            self._dbg("SUBJECT", "Restoring original working directory", original_cwd)
            os.chdir(original_cwd)

        return True


# ---------------------------------------------------------------------------
# Top-level worker — must be at module level for pickling by multiprocessing
# ---------------------------------------------------------------------------

def _subject_worker(args: tuple) -> tuple:
    """
    Executed in a spawned child process.
    Returns (subject_num, success: bool, error_msg: str).
    """
    subject_num, template_path_str, root_dir_str, steps, selected_trials, log_level = args

    # Each worker configures its own logger (no shared state with parent)
    logger = logging.getLogger(f"S{subject_num}")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                f"%(asctime)s [%(levelname)-8s] S{subject_num}: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    sep = "=" * 60
    print(f"\n{sep}", flush=True)
    print(f"[WORKER] Process started for subject {subject_num}", flush=True)
    print(f"[WORKER]   PID           : {os.getpid()}", flush=True)
    print(f"[WORKER]   template_path : {template_path_str}", flush=True)
    print(f"[WORKER]   root_dir      : {root_dir_str}", flush=True)
    print(f"[WORKER]   steps         : {steps}", flush=True)
    print(f"[WORKER]   selected_trials: {selected_trials or 'all'}", flush=True)
    print(f"[WORKER]   log_level     : {log_level}", flush=True)
    print(f"{sep}\n", flush=True)

    try:
        print(f"[WORKER] Loading template from: {template_path_str}", flush=True)
        with open(template_path_str, "r") as fh:
            template = json.load(fh)
        print(f"[WORKER] Template loaded OK — keys: {list(template.keys())}", flush=True)

        engine = PipelineEngine(logger)
        print(f"[WORKER] PipelineEngine created, starting run_pipeline_for_subject...", flush=True)

        success = engine.run_pipeline_for_subject(
            subject_num=subject_num,
            template=template,
            root_dir=Path(root_dir_str),
            enabled_steps=steps,
            selected_trials=selected_trials,
        )
        print(f"\n[WORKER] run_pipeline_for_subject returned: {success}", flush=True)
        return (subject_num, success, "")

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        print(f"\n[WORKER] UNHANDLED EXCEPTION for subject {subject_num}:\n{tb}", flush=True)
        return (subject_num, False, str(exc))


# ---------------------------------------------------------------------------
# Subject discovery
# ---------------------------------------------------------------------------

def discover_subjects(root_dir: Path) -> List[str]:
    subjects = [
        p.name.replace("S", "")
        for p in sorted(root_dir.glob("S*"))
        if p.is_dir() and p.name.replace("S", "").isdigit()
    ]
    return sorted(subjects, key=lambda x: int(x))


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

def run_parallel(jobs: List[tuple], cores: int, logger: logging.Logger) -> List[str]:
    """
    Use 'spawn' multiprocessing context to avoid crashes from fork + OpenSim/Qt state.
    Physical cores are used directly — no thread pool overhead.
    """
    import multiprocessing as mp

    ctx = mp.get_context("spawn")
    total = len(jobs)
    done = 0
    failed: List[str] = []

    logger.info(
        "Starting parallel run: %d subject(s) across %d physical core(s)", total, cores
    )

    with ctx.Pool(processes=cores) as pool:
        for subject_num, success, err in pool.imap_unordered(_subject_worker, jobs):
            done += 1
            if success:
                logger.info("[%d/%d] Subject %s  DONE", done, total, subject_num)
            else:
                logger.error("[%d/%d] Subject %s  FAILED: %s", done, total, subject_num, err)
                failed.append(subject_num)

    return failed


def run_sequential(jobs: List[tuple], logger: logging.Logger) -> List[str]:
    total = len(jobs)
    failed: List[str] = []

    for idx, job in enumerate(jobs, 1):
        subject_num, success, err = _subject_worker(job)
        if success:
            logger.info("[%d/%d] Subject %s  DONE", idx, total, subject_num)
        else:
            logger.error("[%d/%d] Subject %s  FAILED: %s", idx, total, subject_num, err)
            failed.append(subject_num)

    return failed


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenSim batch pipeline (CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--template", required=True, help="Path to template JSON file")
    parser.add_argument(
        "--subjects",
        default="",
        help="Comma-separated subject numbers e.g. 01,02,05 (default: all discovered)",
    )
    parser.add_argument(
        "--trials",
        default="",
        help="Comma-separated trial names (applied to every subject; default: all)",
    )
    parser.add_argument(
        "--steps",
        default="scale,ik,id,so",
        help="Comma-separated steps: scale,ik,id,so (default: all)",
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Run subjects in parallel using physical cores"
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=0,
        help="Number of parallel cores (default: physical_cores - 1, min 1)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--log-file", default="", help="Optional file path for log output")
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.template.strip():
        print("Error: --template argument is required", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    log_file = args.log_file or None
    logger = setup_logging(args.log_level, log_file)

    sep = "=" * 60
    print(f"\n{sep}", flush=True)
    print("[MAIN] Pipeline CLI starting", flush=True)
    print(f"[MAIN]   Python        : {sys.version}", flush=True)
    print(f"[MAIN]   PID           : {os.getpid()}", flush=True)
    print(f"[MAIN]   CWD           : {os.getcwd()}", flush=True)
    print(f"[MAIN]   --template    : {args.template}", flush=True)
    print(f"[MAIN]   --subjects    : {args.subjects or '(auto-discover)'}", flush=True)
    print(f"[MAIN]   --trials      : {args.trials or '(all)'}", flush=True)
    print(f"[MAIN]   --steps       : {args.steps}", flush=True)
    print(f"[MAIN]   --parallel    : {args.parallel}", flush=True)
    print(f"[MAIN]   --cores       : {args.cores or '(auto)'}", flush=True)
    print(f"[MAIN]   --log-level   : {args.log_level}", flush=True)
    print(f"[MAIN]   --log-file    : {log_file or '(none)'}", flush=True)
    print(f"{sep}\n", flush=True)

    # Load template
    template_path = Path(args.template)
    print(f"[MAIN] Checking template path: {template_path}", flush=True)
    print(f"[MAIN] Template file exists? {template_path.is_file()}", flush=True)

    if not template_path.is_file():
        logger.error("Template file not found: %s", template_path)
        sys.exit(1)

    with open(template_path, "r") as fh:
        template = json.load(fh)
    print(f"[MAIN] Template loaded OK — keys: {list(template.keys())}", flush=True)

    root_dir_str = template.get("root_dir", "")
    print(f"[MAIN] root_dir from template: {root_dir_str!r}", flush=True)

    if not root_dir_str:
        logger.error("Template JSON missing 'root_dir' key")
        sys.exit(1)

    root_dir = Path(root_dir_str)
    print(f"[MAIN] root_dir Path: {root_dir}", flush=True)
    print(f"[MAIN] root_dir exists? {root_dir.is_dir()}", flush=True)

    if not root_dir.is_dir():
        logger.error("root_dir does not exist: %s", root_dir)
        sys.exit(1)

    # Resolve subjects
    if args.subjects.strip():
        subjects = [s.strip().zfill(2) for s in args.subjects.split(",") if s.strip()]
        print(f"[MAIN] Subjects from --subjects arg: {subjects}", flush=True)
    else:
        subjects = discover_subjects(root_dir)
        print(f"[MAIN] Auto-discovered subjects: {subjects}", flush=True)
        logger.info("Auto-discovered subjects: %s", subjects)

    if not subjects:
        logger.error("No subjects found. Exiting.")
        sys.exit(1)

    # Resolve trials
    selected_trials: Optional[List[str]] = None
    if args.trials.strip():
        selected_trials = [t.strip() for t in args.trials.split(",") if t.strip()]
    print(f"[MAIN] selected_trials: {selected_trials or 'all'}", flush=True)

    # Resolve steps
    requested = {s.strip().lower() for s in args.steps.split(",") if s.strip()}
    all_steps = {"scale", "ik", "id", "so"}
    unknown = requested - all_steps
    if unknown:
        logger.warning("Unknown step(s) ignored: %s", unknown)
    steps = {s: (s in requested) for s in all_steps}

    active_steps = [s for s, v in steps.items() if v]
    print(f"[MAIN] Steps map: {steps}", flush=True)
    print(f"[MAIN] Active steps: {active_steps}", flush=True)

    logger.info("Template  : %s", template_path)
    logger.info("Root dir  : %s", root_dir)
    logger.info("Subjects  : %s", subjects)
    logger.info("Trials    : %s", selected_trials or "all")
    logger.info("Steps     : %s", active_steps)
    logger.info("Parallel  : %s", args.parallel)

    # Build job list
    jobs = [
        (s, str(template_path), str(root_dir), steps, selected_trials, args.log_level)
        for s in subjects
    ]
    print(f"[MAIN] Total jobs to run: {len(jobs)}", flush=True)
    for j in jobs:
        print(f"[MAIN]   job -> subject={j[0]}  template={j[1]}", flush=True)

    # Run
    t0 = time.monotonic()

    if args.parallel and len(jobs) > 1:
        cores = args.cores if args.cores > 0 else max(1, physical_core_count() - 1)
        cores = min(cores, len(jobs))
        print(f"\n[MAIN] Parallel mode — physical cores available: {physical_core_count()}", flush=True)
        print(f"[MAIN] Using {cores} core(s) for {len(jobs)} subject(s)", flush=True)
        failed = run_parallel(jobs, cores, logger)
    else:
        if args.parallel:
            logger.info("Only one subject; running sequentially.")
        print(f"\n[MAIN] Sequential mode", flush=True)
        failed = run_sequential(jobs, logger)

    elapsed = time.monotonic() - t0
    logger.info("Finished in %.1f s", elapsed)
    print(f"\n[MAIN] Total elapsed time: {elapsed:.1f} s", flush=True)

    if failed:
        logger.error("Failed subjects: %s", failed)
        print(f"[MAIN] FAILED subjects: {failed}", flush=True)
        sys.exit(1)
    else:
        logger.info("All subjects completed successfully.")
        print(f"[MAIN] All subjects completed successfully.", flush=True)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Required on Windows with frozen/spawn executables
    main()
