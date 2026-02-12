"""
Pipeline GUI for OpenSim processing using PySide6.
Features:
- Select template JSON via dialog (no argv)
- Extract root_dir from JSON
- Discover subjects under root_dir (Sxx)
- Subject checklist with filter & sort
- Per-subject trial discovery (replacing '01' in template paths) and validation
- Trial tree with checkboxes under subjects
- Select pipeline steps (Scale, IK, ID, SO)
- Run pipeline (in background thread) and display logs

Save this file and run: python pipeline_gui.py
Requires: PySide6, OpenSim (if running actual tools)
"""

import sys
import os
import json
import logging
import subprocess
import threading
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFileDialog, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QCheckBox, QLineEdit, QTextEdit, QProgressBar, QGroupBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject


import opensim as osim


BOLD_RED = "\033[1;91m" # Bold and bright red for extra attention
END = "\033[0m" # Reset code

# ------------------ Data classes ------------------

@dataclass
class PipelineConfig:
    template_path: Path
    root_dir: Path
    subjects: List[str]
    trials: Dict[str, List[str]]
    run_scale: bool
    run_ik: bool
    run_id: bool
    run_so: bool
    parallel: bool


# ------------------ Utility functions ------------------

def replace_subject_in_path(path_str: str, old_subj: str, new_subj: str) -> str:
    return path_str.replace(old_subj, new_subj)


# ------------------ Pipeline Engine (refactored) ------------------
class PipelineEngine:
    def __init__(self, logger: logging.Logger = None):# type: ignore
        self.logger = logger or logging.getLogger(__name__)

    def generate_setups_if_needed(self, subject_num: str, subj_dir: Path, trial, model_file: Path,xml = "", trial_name = "") -> bool:
        script_dir = Path(__file__).parent
        # print(f"subject_num = {subject_num},\nsubj_dir = {subj_dir},\ntrial = {trial},\nmodel_file = {model_file},\nxml = {xml},\ntrial_name = {trial_name}\n")
        if trial_name == "scale":
            # scale
            scale_dir = subj_dir / "scale"
            # if not scale_dir.exists() or not Path(xml).exists():
            self.logger.info(f"Generating scale setup for subject {subject_num}")
            
            result = subprocess.run(['python', 'scale_setup.py', subject_num, str(subj_dir), str(model_file), str(xml)], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Scale setup failed for {subject_num}: {result.stderr}")
            return True
        # GRF
        try:
            grf_dir = subj_dir / "ID" / "grf"
            if trial_name == "stw1":
            # if not grf_dir.exists() or not Path(trial.get('grf_xml',"")).exists():
                self.logger.info(f"Generating GRF setups for subject {subject_num}")
                
                result = subprocess.run(['python', 'grf_setup.py', subject_num, str(subj_dir), str(trial_name), str(trial.get('trial_mot',"")),str(trial.get('trial_trc',"")),str(trial.get('grf_xml',""))], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
        except Exception as e:
            self.logger.error(f"GRF setup failed for {subject_num}: {e}")

        # ID
        try:
            id_dir = subj_dir / "ID"
            # if not id_dir.exists() or not Path(trial.get('id_xml',"")).exists():
            self.logger.info(f"Generating ID setups for subject {subject_num}")
            
            result = subprocess.run(['python', 'id_setup.py', str(subj_dir), str(trial_name), str(model_file), str(trial.get('id_xml',""))], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
        except Exception as e:
            self.logger.error(f"ID setup failed for {subject_num}: {e}")

        # SO
        try:
            so_dir = subj_dir / "SO"
            if not so_dir.exists() or not Path(trial.get('so_xml',"")).exists():
                self.logger.info(f"Generating SO setups for subject {subject_num}")
                
                result = subprocess.run(['python', 'SO_setup.py', str(subj_dir), str(trial_name), str(model_file), str(trial.get('so_xml',""))], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
            
            # Copy actuators file if it doesn't exist
            actuators_src = Path(r"d:\student\MTech\Sakshi\STW\S01\SO\cmc_actuators.xml")
            actuators_dst = so_dir / "cmc_actuators.xml"
            if actuators_src.exists() and not actuators_dst.exists():
                so_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(actuators_src), str(actuators_dst))
                self.logger.info(f"Copied cmc_actuators.xml to {actuators_dst}")
        except Exception as e:
            self.logger.error(f"SO setup failed for {subject_num}: {e}")

        # IK
        try:            
            ik_dir = subj_dir / "IK"
            if not ik_dir.exists() or not Path(trial.get('ik_xml',"")).exists():
                self.logger.info(f"Generating IK setups for subject {subject_num}")
                
                result = subprocess.run(['python', 'ik_setup.py', str(subj_dir), str(trial_name), str(model_file), str(trial.get('trial_trc',"")), str(trial.get('ik_xml',""))], cwd=str(Path.joinpath(script_dir.parent, 'setup_files')), capture_output=True, text=True)
        except Exception as e:
            self.logger.error(f"IK setup failed for {subject_num}: {e}")
        

        return True

    def run_pipeline_for_subject(self, subject_num: str, template: dict, root_dir: Path, enabled_steps: dict, selected_trials: List[str] = None): # type: ignore
        subj_dir = root_dir / f"S{subject_num}"
        osim.Logger_setLevelString("Error") # Suppress OpenSim logs except errors
        # osim.Logger_setLevelString("Critical") # Suppress all OpenSim logs
        if not subj_dir.exists():
            self.logger.warning(f"Subject {subject_num} directory not found; skipping.")
            return False
        # osim.Logger_setLevelString("Off")
        adapted = json.loads(json.dumps(template))
        # Replace subject 01 with subject_num in adapted paths
        for key, value in adapted.items():
            if isinstance(value, str):
                adapted[key] = replace_subject_in_path(value, "01", subject_num)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if isinstance(v, str):
                                item[k] = replace_subject_in_path(v, "01", subject_num)

        # print(f"Adapted template for subject {subject_num}: {adapted}")  # Debug print to check adapted paths
        original_cwd = os.getcwd()
        try:
            
            print('{BOLD_RED}',os.getcwd(),'{END}')
            self.logger.info(f"Processing subject {subject_num} in {subj_dir}")

            # Scaling
            scaled_model = None
            scale_xml = None
            if enabled_steps.get('scale', True):
                os.mkdir(subj_dir / "scale") if not (subj_dir / "scale").exists() else None
                # os.chdir(os.path.join(str(subj_dir)+'\\scale'))
                scale_xml = Path(adapted.get('scale_xml', ''))
                self.generate_setups_if_needed(subject_num = subject_num, subj_dir = subj_dir, trial = 0, model_file=adapted.get('model', ''),xml = scale_xml,trial_name = "scale") # generate scale setup if not exists
                if scale_xml.exists():
                    os.chdir(str(scale_xml.parent))
                    self.logger.info(f"Running scaling for subject {subject_num}")
                    
                    try:
                        
                        scale_tool = osim.ScaleTool(str(scale_xml))
                        scale_tool.setPathToSubject("")
                        scaled_model = scale_tool.getMarkerPlacer().getOutputModelFileName()
                        scale_tool.getGenericModelMaker().setModelFileName(adapted.get("model", ""))
                        scale_tool.getMarkerPlacer().setMarkerFileName(adapted.get("static_trc", ""))
                        scale_tool.getModelScaler().setMarkerFileName(adapted.get("static_trc", ""))
                        scale_tool.printToXML(str(scale_xml))  # Save the possibly updated XML

                        success = scale_tool.run()
                        if not success:
                            self.logger.error(f"Scaling failed for {subject_num}")
                            return False
                    except Exception as e:
                        self.logger.error(f"Scaling failed for {subject_num}: {str(e)}")
                        return False
                else:
                    self.logger.warning(f"Scale XML not found for {subject_num}; skipping scaling.")
            
            # Run for each trial
            mapped_trials = adapted.get('mapped_trials', [])
            # if not scaled_model:
            #     self.logger.error(f"[FATAL] No scaled model for subject {subject_num}")
            #     return False
            # scaled_model = os.path.join(scale_xml.parent, scaled_model) #type : ignore
            for trial in mapped_trials:
                # extract trial name robustly
                trc = trial.get('trial_trc', '')
                # attempt to replace subject in trc path
                trc = replace_subject_in_path(trc, '01', subject_num)
                # default trial name as filename without extension
                trial_name = Path(trc).stem

                # if user selected only specific trials, skip others
                if selected_trials and trial_name not in selected_trials:
                    self.logger.debug(f"Skipping trial {trial_name} as not selected")
                    continue

                self.logger.info(f"Processing trial {trial_name} for subject {subject_num}")
                
                if not self.generate_setups_if_needed(subject_num = subject_num, subj_dir = subj_dir, trial = trial, trial_name = trial_name, model_file=(os.path.join(scale_xml.parent,(scaled_model))) ):
                    self.logger.error(f"Setup generation failed for {subject_num}; skipping.")
                    continue

                # IK
                ik_tool = None
                if enabled_steps.get('ik', True):
                    ik_xml = Path(replace_subject_in_path(trial.get('ik_xml', ''), '01', subject_num))
                    os.chdir(str(ik_xml.parent))
                    self.logger.info(f"ik xml =  {ik_xml}")           
                    if ik_xml.exists():
                        self.logger.info(f"Running IK for trial {trial_name}")
                        
                        try:
                            ik_tool = osim.InverseKinematicsTool(str(ik_xml))
                            ik_tool.set_model_file((os.path.join(scale_xml.parent,(scaled_model)))) 
                            ik_tool.setMarkerDataFileName(trial['trial_trc'])
                            success = ik_tool.run() 
                            if not success:
                                self.logger.error(f"IK failed for {trial_name}")
                                continue
                        except Exception as e:
                            self.logger.error(f"IK failed for {trial_name}: {str(e)}")
                            continue
                    else:
                        self.logger.warning(f"IK XML not found for {trial_name}; skipping IK.")
                        continue

                # ID
                if enabled_steps.get('id', True):
                    id_xml = Path(replace_subject_in_path(trial.get('id_xml', ''), '01', subject_num))
                    grf_xml = Path(replace_subject_in_path(trial.get('grf_xml', ''), '01', subject_num))
                    os.chdir(str(id_xml.parent))
                    if id_xml.exists() and grf_xml.exists():
                        self.logger.info(f"Running ID for trial {trial_name}")
                        
                        try:
                            
                                id_tool = osim.InverseDynamicsTool(str(id_xml))
                                id_tool.setModelFileName((os.path.join(scale_xml.parent,(scaled_model))))   
                                if ik_tool is not None:
                                    id_tool.setCoordinatesFileName(os.path.join(ik_xml.parent, ik_tool.getOutputMotionFileName()))
                                id_tool.setExternalLoadsFileName(str(grf_xml))
                                success = id_tool.run()
                                if not success:
                                    self.logger.error(f"ID failed for {trial_name}")
                                    continue
                        except Exception as e:
                            self.logger.error(f"ID failed for {trial_name}: {str(e)}")
                            continue
                    else:
                        self.logger.warning(f"ID or GRF XML not found for {trial_name}; skipping ID.")
                        continue

                # SO
                if enabled_steps.get('so', True):
                    so_xml = Path(replace_subject_in_path(trial.get('so_xml', ''), '01', subject_num))
                    os.chdir(str(so_xml.parent))
                    if so_xml.exists():
                        self.logger.info(f"Running SO for trial {trial_name}")
                        
                        try:
                            so_tool = osim.AnalyzeTool(str(so_xml))
                            so_tool.setExternalLoadsFileName(str(grf_xml)) 
                            so_tool.setModel((os.path.join(scale_xml.parent,scaled_model)))   
                            if ik_tool is not None:
                                so_tool.setCoordinatesFileName(ik_tool.getOutputMotionFileName())
                            success = so_tool.run()
                            if not success:
                                self.logger.error(f"SO failed for {trial_name}")
                        except Exception as e:
                            self.logger.error(f"SO failed for {trial_name}: {str(e)}")
                    else:
                        self.logger.warning(f"SO XML not found for {trial_name}; skipping SO.")
                        continue
        
        finally:
            os.chdir(original_cwd)

    def run_pipeline(self, config: PipelineConfig):
        # Load template
        with open(config.template_path, 'r') as f:
            template = json.load(f)

        root_dir = config.root_dir

        subjects = config.subjects
        self.logger.info(f"Starting pipeline for subjects: {subjects}")

        for s in subjects:
            self.run_pipeline_for_subject(s, template, root_dir,
                                         enabled_steps={
                                             'scale': config.run_scale,
                                             'ik': config.run_ik,
                                             'id': config.run_id,
                                             'so': config.run_so
                                         },
                                         selected_trials=config.trials.get(s, None)) # type: ignore

        self.logger.info("Pipeline completed.")


# ------------------ Logging integration with Qt ------------------
class QtLogEmitter(QObject):
    log_signal = Signal(str)
    progress_signal = Signal(int)

class QtLogHandler(logging.Handler):
    def __init__(self, emitter: QtLogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.log_signal.emit(msg)
        except Exception:
            pass


# ------------------ GUI ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenSim Pipeline GUI")
        self.resize(1000, 700)

        # Logger / Engine
        self.logger = logging.getLogger("PipelineGUI")
        self.logger.setLevel(logging.DEBUG)
        self.qt_emitter = QtLogEmitter()
        self.log_handler = QtLogHandler(self.qt_emitter)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)

        


        # UI elements
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()

        # Top controls
        btn_box = QHBoxLayout()
        self.btn_load = QPushButton("Load template JSON")
        self.btn_load.clicked.connect(self.load_template)
        btn_box.addWidget(self.btn_load)

        self.label_template = QLabel("No template loaded")
        btn_box.addWidget(self.label_template)

        left_panel.addLayout(btn_box)

        self.btn_select_all = QPushButton("Select all")
        self.btn_deselect_all = QPushButton("Deselect all")
        self.btn_select_all.clicked.connect(self.select_all_subjects)
        self.btn_deselect_all.clicked.connect(self.deselect_all_subjects)

        btn_box.addWidget(self.btn_select_all)
        btn_box.addWidget(self.btn_deselect_all)


        # Subject filter
        filter_box = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter subjects (seperated by commas)...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_box.addWidget(QLabel("Filter:"))
        filter_box.addWidget(self.filter_input)
        left_panel.addLayout(filter_box)

        # Subject list
        self.subject_list = QListWidget()
        self.subject_list.setSelectionMode(QListWidget.MultiSelection)             # type: ignore
        self.subject_list.itemChanged.connect(self.subject_toggled)
        left_panel.addWidget(QLabel("Subjects:"))
        left_panel.addWidget(self.subject_list, stretch=2)

        # Steps selection
        steps_group = QGroupBox("Pipeline steps")
        steps_layout = QGridLayout()
        self.chk_scale = QCheckBox("Scaling")
        self.chk_scale.setChecked(True)
        self.chk_ik = QCheckBox("Inverse Kinematics")
        self.chk_ik.setChecked(True)
        self.chk_id = QCheckBox("Inverse Dynamics")
        self.chk_id.setChecked(True)
        self.chk_so = QCheckBox("Static Optimization / Analyze")
        self.chk_so.setChecked(True)
        steps_layout.addWidget(self.chk_scale, 0, 0)
        steps_layout.addWidget(self.chk_ik, 0, 1)
        steps_layout.addWidget(self.chk_id, 1, 0)
        steps_layout.addWidget(self.chk_so, 1, 1)
        steps_group.setLayout(steps_layout)
        left_panel.addWidget(steps_group)

        # Run controls
        run_box = QHBoxLayout()
        self.chk_parallel = QCheckBox("Parallel (use multiple cores)")
        self.btn_run = QPushButton("Run pipeline")
        self.btn_run.clicked.connect(self.run_pipeline)
        run_box.addWidget(self.chk_parallel)
        run_box.addWidget(self.btn_run)
        left_panel.addLayout(run_box)

        # Right: Trial tree + logs
        self.trial_tree = QTreeWidget()
        self.trial_tree.setHeaderLabels(["Subject/Trial", "Exists"])
        right_panel.addWidget(QLabel("Trials (per subject):"))
        right_panel.addWidget(self.trial_tree, stretch=3)

        # Logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_panel.addWidget(QLabel("Logs:"))
        right_panel.addWidget(self.log_text, stretch=2)

        # Progress
        self.progress = QProgressBar()
        right_panel.addWidget(self.progress)
        self.engine = PipelineEngine(logger=self.logger)
        self.qt_emitter.progress_signal.connect(self.progress.setValue)

        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=2)

        # Internal state
        self.template = None
        self.template_path = None
        self.root_dir = None
        self.detected_subjects = []  # list of '01','02' etc
        self.subject_items = {}  # subj -> QListWidgetItem
        self.subject_trials = {}  # subj -> list of trial dicts

        # Connect logger signal to UI
        self.qt_emitter.log_signal.connect(self.append_log)

    # ------------------ UI methods ------------------
    def append_log(self, text: str):
        self.log_text.append(text)

    def select_all_subjects(self):
        for s, item in self.subject_items.items():
            item.setCheckState(Qt.Checked)
        for i in range(self.trial_tree.topLevelItemCount()):
            top = self.trial_tree.topLevelItem(i)
            top.setCheckState(0, Qt.Checked)
            for j in range(top.childCount()):
                top.child(j).setCheckState(0, Qt.Checked)

    def deselect_all_subjects(self):
        for s, item in self.subject_items.items():
            item.setCheckState(Qt.Unchecked)
        for i in range(self.trial_tree.topLevelItemCount()):
            top = self.trial_tree.topLevelItem(i)
            top.setCheckState(0, Qt.Unchecked)
            for j in range(top.childCount()):
                top.child(j).setCheckState(0, Qt.Unchecked)


    def load_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select template JSON", os.getcwd(), "JSON files (*.json)")
        if not path:
            return
        try:
            with open(path, 'r') as f:
                template = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")
            return

        self.template = template
        self.template_path = Path(path)
        self.label_template.setText(str(self.template_path))

        # extract root_dir
        root = template.get('root_dir')
        if not root:
            QMessageBox.warning(self, "Warning", "Template JSON has no 'root_dir' key")
            return
        self.root_dir = Path(root)

        # discover subjects in root_dir
        self.detect_subjects()

    def detect_subjects(self):
        self.subject_list.clear()
        self.subject_items.clear()
        self.subject_trials.clear()

        if not self.root_dir or not self.root_dir.exists():
            QMessageBox.warning(self, "Warning", f"Root dir {self.root_dir} does not exist")
            return

        subjects = [p.name.replace('S', '') for p in sorted(self.root_dir.glob('S*')) if p.is_dir()]
        # ensure two-digit format
        subjects = [s for s in subjects if s.isdigit()]
        subjects = sorted(subjects, key=lambda x: int(x))
        self.detected_subjects = subjects

        for s in subjects:
            item = QListWidgetItem(f"S{s}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)   # type: ignore
            item.setCheckState(Qt.Unchecked)                       # type: ignore
            self.subject_list.addItem(item)
            self.subject_items[s] = item

        # auto-populate trials for each detected subject
        for s in subjects:
            self.resolve_trials_for_subject(s)

        self.populate_trial_tree()

    def apply_filter(self, text: str):
        text = text.lower().strip()
    
        # Check if input looks like comma-separated numbers: (6,23,18) or 6,23,18
        selected_subjects = set()
        if text:
            # Remove parentheses if present
            cleaned = text.replace('(', '').replace(')', '')
            # Check if it's a comma-separated list
            if ',' in cleaned:
                try:
                    selected_subjects = {s.strip().zfill(2) for s in cleaned.split(',') if s.strip().isdigit()}
                except:
                    pass
    
        for s, item in self.subject_items.items():
            # Show if: selected_subjects is empty (no filter), or subject matches
            if selected_subjects:
                visible = s in selected_subjects
            else:
                # Regular substring matching
                visible = text in s or text in item.text().lower()
            item.setHidden(not visible)

    def subject_toggled(self, item: QListWidgetItem):
        # When subject toggled, update trial selection states in the tree
        subj_label = item.text()  # e.g., 'S01'
        subj = subj_label.replace('S', '')
        checked = item.checkState() == Qt.Checked                 # type: ignore
        # find corresponding tree item
        for i in range(self.trial_tree.topLevelItemCount()):
            top = self.trial_tree.topLevelItem(i)
            if top.text(0) == f"S{subj}":                          # type: ignore
                top.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)          # type: ignore
                # toggle children
                for j in range(top.childCount()):                   # type: ignore
                    ch = top.child(j)                               # type: ignore
                    ch.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)        # type: ignore
                break

    def resolve_trials_for_subject(self, subj: str):
        # Use template mapped_trials to resolve trial paths for the given subject
        trials = []
        mapped = self.template.get('mapped_trials', []) if self.template else []
        for t in mapped:
            trc = t.get('trial_trc', '')
            trc_sub = replace_subject_in_path(trc, '01', subj)
            exists = Path(trc_sub).exists()
            trial_name = Path(trc_sub).stem
            trials.append({'name': trial_name, 'path': trc_sub, 'exists': exists, 'raw': t})
        self.subject_trials[subj] = trials

    def populate_trial_tree(self):
        self.trial_tree.clear()
        for s in self.detected_subjects:
            top = QTreeWidgetItem([f"S{s}", ""] )
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable)          # type: ignore
            top.setCheckState(0, Qt.Unchecked)                          # type: ignore
            self.trial_tree.addTopLevelItem(top)
            for t in self.subject_trials.get(s, []):
                child = QTreeWidgetItem([t['name'], "Yes" if t['exists'] else "No"]) 
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)  # type: ignore
                child.setCheckState(0, Qt.Checked if t['exists'] else Qt.Unchecked) # type: ignore
                top.addChild(child)
            top.setExpanded(True)

    # ------------------ Run pipeline ------------------
    def collect_config(self) -> PipelineConfig:
        selected_subjects = []
        for s, item in self.subject_items.items():
            if item.checkState() == Qt.Checked:                        # type: ignore
                selected_subjects.append(s)

        # collect selected trials per subject from tree
        selected_trials = {}
        for i in range(self.trial_tree.topLevelItemCount()):
            top = self.trial_tree.topLevelItem(i)
            subj_label = top.text(0).replace('S', '')                  
            picks = []
            for j in range(top.childCount()):
                ch = top.child(j)
                if ch.checkState(0) == Qt.Checked:
                    picks.append(ch.text(0))
            if picks:
                selected_trials[subj_label] = picks

        config = PipelineConfig(
            template_path=self.template_path,
            root_dir=self.root_dir,
            subjects=selected_subjects if selected_subjects else self.detected_subjects,
            trials=selected_trials,
            run_scale=self.chk_scale.isChecked(),
            run_ik=self.chk_ik.isChecked(),
            run_id=self.chk_id.isChecked(),
            run_so=self.chk_so.isChecked(),
            parallel=self.chk_parallel.isChecked()
        )
        return config

    def run_pipeline(self):
        if not self.template:
            QMessageBox.warning(self, "Warning", "Load a template JSON first")
            return

        config = self.collect_config()

        # confirm
        msg = f"Run pipeline for subjects: {config.subjects}\nSteps: "
        steps = [k for k, v in {
            'scale': config.run_scale,
            'ik': config.run_ik,
            'id': config.run_id,
            'so': config.run_so
        }.items() if v]
        msg += ','.join(steps)

        if QMessageBox.question(self, "Confirm run", msg) != QMessageBox.StandardButton.Yes:
            return

        # run in background thread to keep UI responsive
        thread = threading.Thread(target=self._background_run, args=(config,), daemon=True)
        thread.start()

    def _background_run(self, config: PipelineConfig):
        try:
            self.qt_emitter.progress_signal.emit(0)
            total_subjects = len(config.subjects)
            for idx, s in enumerate(config.subjects):
                # update progress (emit via logger so UI updates in main thread)
                self.logger.info(f"Starting subject {s} ({idx+1}/{total_subjects})")
                # ensure trials resolved for subject (in case user changed selection)
                if s not in self.subject_trials:
                    self.resolve_trials_for_subject(s)
                self.engine.run_pipeline_for_subject(s, json.load(open(config.template_path)), config.root_dir,
                                                    enabled_steps={'scale': config.run_scale, 'ik': config.run_ik, 'id': config.run_id, 'so': config.run_so},
                                                    selected_trials=config.trials.get(s, None))
                value = int(((idx+1)/total_subjects)*100)
                self.qt_emitter.progress_signal.emit(value)

            self.logger.info("All done")
            self.qt_emitter.progress_signal.emit(100)
        except Exception as e:
            self.logger.exception(f"Pipeline failed: {e}")


# ------------------ Main ------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
