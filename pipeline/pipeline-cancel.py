# !/usr/bin/env python3
"""
run_pipeline_from_template.py

Usage:
    python run_pipeline_from_template.py /path/to/subjects_root

Requirements:
 - Put this script next to your template_map.json (the JSON you already made).
 - Adjust OPEN_SIM_CLI or replace the placeholders with OpenSim Python API calls if you prefer.

Behavior:
 - For each subject folder under subjects_root, create mapping_for_pipeline.json
 - Adapt example template paths to each subject by using relative path substitution
 - Only include trials that have linked IK (and ID if present). Skips others.
 - Optionally runs OpenSim steps (lines provided; comment/uncomment to use).
"""
import json
import re
from pathlib import Path
from pprint import pprint
import subprocess
import sys

TEMPLATE = Path("template_map.json")   # your file (already present)
OUTPUT_NAME = "mapping_for_pipeline.json"

# ---- Utilities ----
def numeric_tokens(s):
    return re.findall(r"(\d+)", s)

def replace_number_in_name(example_name, target_name):
    """
    Replace numeric tokens in example_name with numeric tokens from target_name.
    If example has multiple numeric tokens, replace them in order.
    If no numeric tokens, return target_name's stem + example extension.
    """
    ex_nums = numeric_tokens(example_name)
    tgt_nums = numeric_tokens(target_name)
    if not ex_nums or not tgt_nums:
        # fallback: use target_name as-is (no number substitution possible)
        return target_name
    # replace numbers sequentially
    new = example_name
    for en, tn in zip(ex_nums, tgt_nums):
        new = re.sub(en, tn, new, count=1)
    return new

def adapt_path_for_subject(example_path, example_root, target_root, example_trial_name=None, candidate_trial_name=None):
    """
    Replace example_root prefix in example_path by target_root and, if needed,
    swap trial basename numeric tokens from example_trial_name -> candidate_trial_name.
    Returns Path object (not necessarily existing).
    """
    try:
        rel = Path(example_path).relative_to(example_root)
    except Exception:
        # If example_path is not under example_root, do string replacement of example_root string
        rel = Path(str(example_path).replace(str(example_root), "")).relative_to(Path("."))
    # if trial-based filename substitution requested:
    if example_trial_name and candidate_trial_name:
        # perform numeric token substitution on the final filename
        new_name = replace_number_in_name(rel.name, candidate_trial_name)
        rel = rel.with_name(new_name)
    return (Path(target_root) / rel).resolve()

def find_candidates_in_same_rel_folder(example_trial_path, example_root, target_subject_root):
    """
    Given example_trial_path and example_root, compute the same relative folder inside target_subject_root
    and list candidate .trc files there.
    """
    ex_trial = Path(example_trial_path)
    try:
        relfolder = ex_trial.parent.relative_to(example_root)
    except Exception:
        # fallback: try using the parent path portion after subject folder name
        relfolder = ex_trial.parent
    target_folder = Path(target_subject_root) / relfolder
    if not target_folder.exists():
        return []
    return sorted([p for p in target_folder.iterdir() if p.suffix.lower() == ".trc"])

# ---- Main ----
def main(root_dir_str):
    root_dir = Path(root_dir_str).expanduser().resolve()
    if not root_dir.is_dir():
        print("subjects_root must be a directory.")
        sys.exit(1)

    if not TEMPLATE.exists():
        print("template_map.json not found in current directory.")
        sys.exit(1)

    template = json.loads(TEMPLATE.read_text())
    example_subject = Path(template.get("example_subject") or template.get("subject"))
    if not example_subject:
        print("example subject path not found in template.")
        sys.exit(1)

    print("Loaded template for example:", example_subject)
    pprint(template.get("mapped_trials", [])[:2])

    # gather subject folders (immediate children)
    subjects = sorted([p for p in root_dir.iterdir() if p.is_dir()])
    print(f"Found {len(subjects)} subject folders under {root_dir}\n")

    summary = {"processed": 0, "skipped_trials_total": 0, "mapped_total": 0, "subjects": {}}

    for subj in subjects:
        subj_name = subj.name
        print("Processing subject:", subj_name)
        per_subj_map = {
            "subject": str(subj),
            "scale_xml": None,
            "static_trc": None,
            "mapped_trials": []
        }

        # ---- scale and static: adapt by replacing example_subject base -> subj
        ex_scale = template.get("scale_xml")
        if ex_scale:
            adapted_scale = adapt_path_for_subject(ex_scale, example_subject, subj)
            per_subj_map["scale_xml"] = str(adapted_scale) if adapted_scale.exists() else None
            if not adapted_scale.exists():
                print("  WARNING: scale xml not found for", subj_name, "->", adapted_scale)

        ex_static = template.get("static_trc")
        if ex_static:
            adapted_static = adapt_path_for_subject(ex_static, example_subject, subj)
            per_subj_map["static_trc"] = str(adapted_static) if adapted_static.exists() else None
            if not adapted_static.exists():
                print("  WARNING: static trc not found for", subj_name, "->", adapted_static)

        mapped_count = 0
        skipped_count = 0

        # ---- For each mapped trial in example, find a candidate trial in subject and adapt associated files
        for mapped in template.get("mapped_trials", []):
            ex_trial_trc = mapped["trial_trc"]
            ex_trial_name = Path(ex_trial_trc).name

            # list candidates present in same relative folder for this subject:
            candidates = find_candidates_in_same_rel_folder(ex_trial_trc, example_subject, subj)
            if not candidates:
                # nothing in that folder in target subject - skip
                skipped_count += 1
                continue

            # Heuristic candidate selection:
            # 1) try to find candidate with same numeric token as example (e.g. stw1 -> pick stw1 or nearest)
            ex_nums = numeric_tokens(ex_trial_name)
            chosen_candidate = None
            if ex_nums:
                for c in candidates:
                    if any(n == ex_nums[0] for n in numeric_tokens(c.name)):
                        chosen_candidate = c
                        break
            # 2) if none, try candidate with same prefix (e.g. 'stw')
            if not chosen_candidate:
                ex_prefix = re.split(r'[\d_\.]+', ex_trial_name)[0].lower()
                for c in candidates:
                    if c.name.lower().startswith(ex_prefix):
                        chosen_candidate = c
                        break
            # 3) otherwise pick first candidate (positional)
            if not chosen_candidate:
                chosen_candidate = candidates[0]

            # Now adapt IK/ID/SO/GRF by substitution of subject root and trial numbers
            adapted_ik = None
            adapted_id = None
            adapted_so = None
            adapted_grf = None

            # IK
            ex_ik = mapped.get("ik_xml")
            if ex_ik:
                adapted = adapt_path_for_subject(ex_ik, example_subject, subj, example_trial_name=ex_trial_name, candidate_trial_name=chosen_candidate.name)
                if adapted.exists():
                    adapted_ik = str(adapted)
                else:
                    # attempt plain subject-level replacement (no trial number swap)
                    adapted2 = Path(str(ex_ik).replace(str(example_subject), str(subj)))
                    if adapted2.exists():
                        adapted_ik = str(adapted2)

            # ID
            ex_id = mapped.get("id_xml")
            if ex_id:
                adapted = adapt_path_for_subject(ex_id, example_subject, subj, example_trial_name=ex_trial_name, candidate_trial_name=chosen_candidate.name)
                if adapted.exists():
                    adapted_id = str(adapted)
                else:
                    adapted2 = Path(str(ex_id).replace(str(example_subject), str(subj)))
                    if adapted2.exists():
                        adapted_id = str(adapted2)

            # SO
            ex_so = mapped.get("so_xml")
            if ex_so:
                adapted = adapt_path_for_subject(ex_so, example_subject, subj, example_trial_name=ex_trial_name, candidate_trial_name=chosen_candidate.name)
                if adapted.exists():
                    adapted_so = str(adapted)
                else:
                    adapted2 = Path(str(ex_so).replace(str(example_subject), str(subj)))
                    if adapted2.exists():
                        adapted_so = str(adapted2)

            # GRF
            ex_grf = mapped.get("grf_xml")
            if ex_grf:
                adapted = adapt_path_for_subject(ex_grf, example_subject, subj, example_trial_name=ex_trial_name, candidate_trial_name=chosen_candidate.name)
                if adapted.exists():
                    adapted_grf = str(adapted)
                else:
                    adapted2 = Path(str(ex_grf).replace(str(example_subject), str(subj)))
                    if adapted2.exists():
                        adapted_grf = str(adapted2)

            # REQUIRE that IK exists (and optionally ID) — if not, skip this trial
            if not adapted_ik or (mapped.get("id_xml") and not adapted_id):
                skipped_count += 1
                continue

            # Accept mapping for this trial
            per_subj_map["mapped_trials"].append({
                "trial_trc": str(chosen_candidate),
                "ik_xml": adapted_ik,
                "id_xml": adapted_id,
                "so_xml": adapted_so,
                "grf_xml": adapted_grf
            })
            mapped_count += 1

        # Save per-subject mapping JSON
        outpath = subj / OUTPUT_NAME
        outpath.write_text(json.dumps(per_subj_map, indent=2))
        print(f"  -> Saved mapping: {outpath}  (mapped: {mapped_count}, skipped: {skipped_count})")

        # Optionally run pipeline steps for this subject (UNCOMMENT and adapt to your OpenSim environment)
        # NOTE: Replace placeholders below with the actual OpenSim command or OpenSim Python API calls.
        #
        # Example: run scaling (if scale xml exists)
        # if per_subj_map['scale_xml']:
        #     subprocess.run(['opensim-cmd', 'run-tool', per_subj_map['scale_xml']], check=True)
        #
        # for t in per_subj_map['mapped_trials']:
        #     # run IK
        #     subprocess.run(['opensim-cmd', 'run-tool', t['ik_xml']], check=True)
        #     # run ID (if present)
        #     if t.get('id_xml'):
        #         subprocess.run(['opensim-cmd', 'run-tool', t['id_xml']], check=True)
        #     # run SO (if present)
        #     if t.get('so_xml'):
        #         subprocess.run(['opensim-cmd', 'run-tool', t['so_xml']], check=True)
        #
        # A safer approach is to build a shell command or use the OpenSim Python API (if installed).
        #
        summary["processed"] += 1
        summary["mapped_total"] += mapped_count
        summary["skipped_trials_total"] += skipped_count
        summary["subjects"][subj_name] = {"mapped": mapped_count, "skipped": skipped_count}

    print("\nDone. Summary:")
    pprint(summary)
    print("Per-subject mapping files are saved as", OUTPUT_NAME, "inside each subject folder.")
    print("Edit the script to enable OpenSim CLI calls or integrate with OpenSim Python API.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline_from_template.py /path/to/subjects_root")
        sys.exit(1)
    main(sys.argv[1])
