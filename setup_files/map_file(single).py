#!/usr/bin/env python3
"""
create_opensim_template_linked.py

- Scans a single example subject directory for OpenSim files (.xml, .trc, .mot, .sto)
- Auto-detects static TRC (contains "static" in name)
- Auto-detects IK setup XMLs (contains "ik" in name). If none found, prompts user to choose.
- Auto-detects scale XML (contains "scale" in name). If none found, prompts user to choose.
- Treats remaining .trc files as trials.
- Links each IK xml to trial(s) using:
    1) basename substring match
    2) shared numeric token match
    3) if count(ik_xml) == count(trials) -> positional mapping
- **Only includes trials that have a matching IK setup** (skips others)
- Produces template_map.json (single JSON file) suitable as a pipeline template.
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

REQ_EXT = {".xml", ".trc", ".mot", ".sto"}
OUTPUT = "template_map.json"


def print_tree(root: Path, prefix=""):
    items = sorted(root.iterdir())
    for i, p in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + p.name)
        if p.is_dir():
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(p, prefix + extension)


def gather_files(example_dir: Path,REQ_EXT=REQ_EXT):
    files = []
    for p in example_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in REQ_EXT:
            files.append(p)
    return sorted(files)


def choose_from_list(prompt, items, allow_multiple=False):
    if not items:
        return []
    print(prompt)
    for i, p in enumerate(items, 1):
        print(f"  {i}. {p}")
    if allow_multiple:
        ans = input("Choose indices (comma-separated), 'a' for all, or 0 = none: ").strip().lower()
        if ans == 'a':
            return list(items)
        if ans in ('0', ''):
            return []
        try:
            idxs = [int(x) for x in ans.replace(' ', '').split(',')]
            return [items[i-1] for i in idxs]
        except Exception:
            print("Invalid choice. Returning none.")
            return []
    else:
        ans = input("Choose index (or 0 = none): ").strip()
        if ans in ('0', ''):
            return None
        try:
            i = int(ans)
            return items[i-1]
        except Exception:
            print("Invalid choice. Returning none.")
            return None


def numeric_tokens(name):
    return re.findall(r'(\d+)', name)


def map_ik_to_trials(ik_files,id_files,so_files,grf_files, trial_files):
    """
    Returns mapping: ik_path -> list of trial_paths
    Heuristics:
      1) substring match (basename)
      2) shared numeric token
      3) if len(ik)==len(trials) -> positional mapping
    """
    ik_to_trials = defaultdict(list)
    id_to_trials = defaultdict(list)
    so_to_trials = defaultdict(list)
    grf_to_trials = defaultdict(list)
    trials_left = set(trial_files)

    # 1) substring match (case-insensitive)
    for ik, id,so,grf in zip(ik_files, id_files,so_files,grf_files):
        ik_b = ik.stem.lower()
        for tr in list(trials_left):
            if ik_b in tr.stem.lower() or any(tok.lower() in tr.stem.lower() for tok in ik_b.split('_')):
                ik_to_trials[ik].append(tr)
                id_to_trials[id].append(tr)
                so_to_trials[so].append(tr)
                grf_to_trials[grf].append(tr)
                trials_left.discard(tr)

    # 2) numeric token match
    if trials_left:
        # build trial numeric map
        trial_num_map = defaultdict(list)
        for tr in trials_left:
            for n in numeric_tokens(tr.name):
                trial_num_map[n].append(tr)
        for ik, id ,so, grf in zip(ik_files, id_files, so_files, grf_files):
            for n in numeric_tokens(ik.name):
                if n in trial_num_map:
                    for tr in trial_num_map[n]:
                        if tr in trials_left:
                            ik_to_trials[ik].append(tr)
                            id_to_trials[id].append(tr)
                            so_to_trials[so].append(tr)
                            grf_to_trials[grf].append(tr)
                            trials_left.discard(tr)

    # 3) positional mapping if counts equal and still unmatched trials remain
    if trials_left:
        unmatched_trials = sorted(list(trials_left))
        # collect iks that have no mapped trials yet
        iks_unmapped = [ik for ik in ik_files if len(ik_to_trials[ik]) == 0]
        ids_unmapped = [id for id in id_files if len(id_to_trials[id]) == 0]
        sos_unmapped = [so for so in so_files if len(so_to_trials[so]) == 0]
        grfs_unmapped = [grf for grf in grf_files if len(grf_to_trials[grf]) == 0]
        if len(iks_unmapped) == len(unmatched_trials) and len(iks_unmapped) > 0:
            for ik,id, so, grf, tr in zip(sorted(iks_unmapped),sorted(ids_unmapped),sorted(sos_unmapped), sorted(grfs_unmapped), unmatched_trials):
                ik_to_trials[ik].append(tr)
                id_to_trials[id].append(tr)
                so_to_trials[so].append(tr)
                grf_to_trials[grf].append(tr)
                trials_left.discard(tr)

    return ik_to_trials,id_to_trials,so_to_trials,grf_to_trials, list(trials_left)


def find_associated_files_for_trial(trial_path, all_files):
    """Find .mot and .sto in same folder with same basename (or same prefix)."""
    folder = trial_path.parent
    name_noext = trial_path.stem
    mot = []
    sto = []
    # exact basename matches first
    for p in all_files:
        if p.parent == folder:
            if p.suffix.lower() == '.mot' and p.stem == name_noext:
                mot.append(p)
            if p.suffix.lower() == '.sto' and p.stem == name_noext:
                sto.append(p)
    # fallback: any .mot/.sto in same folder (less strict)
    if not mot:
        mot = [p for p in all_files if p.parent == folder and p.suffix.lower() == '.mot']
    if not sto:
        sto = [p for p in all_files if p.parent == folder and p.suffix.lower() == '.sto']
    return mot, sto


def main():
    if len(sys.argv) < 2:
        print("Usage: python map_file(single).py /path/to/example_subject")
        sys.exit(1)

    example = Path(sys.argv[1]).expanduser().resolve()
    root_dir = example
    if not example.is_dir():
        print("Example must be a directory.")
        sys.exit(1)

    print("\nScanning example subject:", example)
    print("\nFolder tree:")

    
    print("\n-----------------------------------\n")

    files = gather_files(example,".osim")
    
    osim_models = [p for p in files if p.suffix.lower() == '.osim']
    check=False
    for subject in example.iterdir():
        print(subject)
        if subject.is_dir() and "01" in str(subject):
            print("\nUsing example subject folder:",subject)
            example = subject
            check=True
            break
    if not check:
        print(" No '01' folder found.")
        exit(1)
            
    print_tree(example)

    files = gather_files(example)
    xml_files = [p for p in files if p.suffix.lower() == '.xml']
    trc_files = [p for p in files if p.suffix.lower() == '.trc']
    # mot_files = [p for p in files if p.suffix.lower() == '.mot']
    # sto_files = [p for p in files if p.suffix.lower() == '.sto']

    # static detection
    static_candidates = [p for p in trc_files if 'static' in p.name.lower()]
    static_trc = None
    if len(static_candidates) == 1:
        static_trc = static_candidates[0]
        print("Auto static:", static_trc)
    elif len(static_candidates) > 1:
        chosen = choose_from_list("Multiple static TRC candidates. Pick one:", static_candidates, allow_multiple=False)
        static_trc = chosen
    else:
        print("No static TRC auto-detected (expect 'static' in filename).")
    osim_model = None
    if len(osim_models) == 1:
        osim_model = osim_models[0]
        print("\nAuto-detected model:", osim_model)
    elif len(osim_models) > 1:
        chosen = choose_from_list("Multiple .osim files found. Pick one:", osim_models, allow_multiple=False)
        osim_model = chosen
    else:
        print("\nNo .osim files found in example directory.")

    # trials are other trc files
    trials = [p for p in trc_files if p != static_trc]
    print(f"\nDetected {len(trials)} trial TRC(s).")

    # IK xml auto-detection
    ik_xmls = [p for p in xml_files if 'ik' in p.name.lower()]
    id_xmls = [p for p in xml_files if 'id' in p.name.lower()]
    so_xmls = [p for p in xml_files if 'so' in p.name.lower()]
    grf_xmls = [p for p in xml_files if 'grf' in p.name.lower()]

    for role, xml_list in [("IK", ik_xmls), ("ID", id_xmls), ("SO", so_xmls), ("GRF", grf_xmls)]:
        if xml_list:
            print(f"\n{role} XML(s):")
            for p in xml_list:
                print(" ", p)
        else:
            # prompt user to select id xmls if none automatically detected
            print("\nNo {role} auto-detected. Please choose {role} file(s) from available XMLs:")
            id_xmls = choose_from_list("Pick {role}(s):", xml_files, allow_multiple=True)
            if xml_list is None:
                xml_list = []


    # scale xml detection
    scale_xmls = [p for p in xml_files if 'scale' in p.name.lower()]
    scale_xml = None
    if len(scale_xmls) == 1:
        scale_xml = scale_xmls[0]
        print("\nAuto-detected SCALE XML:", scale_xml)
    elif len(scale_xmls) > 1:
        scale_xml = choose_from_list("Multiple possible SCALE XMLs. Pick one:", scale_xmls, allow_multiple=False)
    else:
        # ask user to pick single scale xml or skip
        print("\nNo SCALE XML auto-detected. Pick one from XML list (or 0 to skip):")
        scale_xml = choose_from_list("Choose SCALE XML:", xml_files, allow_multiple=False)

    # map IK -> trials
    ik_to_trials_map,id_to_trials_map, so_to_trials_map, grf_to_trials_map, trials_unmatched = map_ik_to_trials(ik_xmls,id_xmls,so_xmls,grf_xmls, trials)
    # Build template structure: include only trials that have a matching IK setup
    mapped_trials = []
    for (ik, tr_list), (id, _),(so,_),(grf,_) in zip(ik_to_trials_map.items(),
                                                id_to_trials_map.items(),
                                                so_to_trials_map.items(),
                                                grf_to_trials_map.items()):
        for tr in tr_list:
            # mot, sto = find_associated_files_for_trial(tr, files)
            mapped_trials.append({
                "trial_trc": str(tr),
                "ik_xml": str(ik),
                "id_xml": str(id),
                "so_xml": str(so),
                "grf_xml": str(grf)
                # "trial_mot": [str(p) for p in mot],
                # "trial_sto": [str(p) for p in sto]
            })

    # summary outputs
    # print("\nSummary:")
    # if static_trc:
    #     print(" Static TRC:", static_trc)
    # print(f" Trials found: {len(trials)} (only {len(mapped_trials)} have linked IK setups and will be included).")
    # if trials_unmatched:
    #     print(" Skipped trials (no IK setup found):")
    #     for t in trials_unmatched:
    #         print("   ", t)
    # if ik_xmls:
    #     print(" IK XML(s):")
    #     for ik in ik_xmls:
    #         linked = ik_to_trials_map.get(ik, [])
    #         print(f"  {ik} -> {len(linked)} trial(s)")

    template = {
        "subject": str(example),
        "root_dir": str(root_dir),
        "model": str(osim_model) if osim_model else None,
        "static_trc": str(static_trc) if static_trc else None,
        "scale_xml": str(scale_xml) if scale_xml else None,
        "mapped_trials": mapped_trials,
        # "all_detected_files": {
        #     "xml": [str(p) for p in xml_files],
        #     "trc": [str(p) for p in trc_files],
        #     "mot": [str(p) for p in mot_files],
        #     "sto": [str(p) for p in sto_files],
        # },
        # "notes": "Only trials with matching IK setups are included. IK->trial mapping heuristics: substring, numeric token, positional."
    }

    Path(OUTPUT).write_text(json.dumps(template, indent=2))
    print(f"\nTemplate written to {OUTPUT}\n")


if __name__ == "__main__":
    main()
