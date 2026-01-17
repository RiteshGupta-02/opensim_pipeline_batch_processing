#!/usr/bin/env python3
"""
create_subjects_json_pattern.py

Scans ONLY the first subject (01) interactively to learn the pattern,
then applies that pattern to all other subjects by replacing subject numbers.

Usage: python create_subjects_json_pattern.py /path/to/root_directory
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

REQ_EXT = {".xml", ".trc", ".mot", ".sto"}
OUTPUT = "subjects_trials.json"


def print_tree(root: Path, prefix="", max_depth=3, current_depth=0):
    """Print directory tree with limited depth"""
    if current_depth >= max_depth:
        return
    try:
        items = sorted(root.iterdir())
        for i, p in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            print(prefix + connector + p.name)
            if p.is_dir() and current_depth < max_depth - 1:
                extension = "    " if i == len(items) - 1 else "│   "
                print_tree(p, prefix + extension, max_depth, current_depth + 1)
    except PermissionError:
        pass


def gather_files(directory: Path, extensions=REQ_EXT):
    """Gather all files with specified extensions"""
    files = []
    for p in directory.rglob("*"):
        if p.is_file() and p.suffix.lower() in extensions:
            files.append(p)
    return sorted(files)


def choose_from_list(prompt, items, allow_multiple=False):
    """Interactive selection from list"""
    if not items:
        return [] if allow_multiple else None
    print(f"\n{prompt}")
    for i, p in enumerate(items, 1):
        print(f"  {i}. {p.name if hasattr(p, 'name') else p}")
    if allow_multiple:
        ans = input("Choose indices (comma-separated), 'a' for all, or 0 = none: ").strip().lower()
        if ans == 'a':
            return list(items)
        if ans in ('0', ''):
            return []
        try:
            idxs = [int(x.strip()) for x in ans.split(',')]
            return [items[i-1] for i in idxs if 1 <= i <= len(items)]
        except Exception:
            print("Invalid choice. Returning none.")
            return []
    else:
        ans = input("Choose index (or 0 = none): ").strip()
        if ans in ('0', ''):
            return None
        try:
            i = int(ans)
            if 1 <= i <= len(items):
                return items[i-1]
            else:
                print("Invalid index.")
                return None
        except Exception:
            print("Invalid choice. Returning none.")
            return None


def numeric_tokens(name):
    """Extract numeric tokens from filename"""
    return re.findall(r'(\d+)', name)


def detect_subject_number(path_str):
    """Extract subject number from path using various patterns"""
    patterns = [
        r'[Ss]ubject[_-]?(\d+)',
        r'[Ss](\d+)',
        r'(?:^|/)(\d+)(?:/|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, path_str)
        if match:
            return match.group(1)
    return None


def map_ik_to_trials(ik_files, id_files, so_files, grf_files, trial_files):
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
    for ik, id_xml, so, grf in zip(ik_files, id_files, so_files, grf_files):
        ik_b = ik.stem.lower()
        for tr in list(trials_left):
            if ik_b in tr.stem.lower() or any(tok.lower() in tr.stem.lower() for tok in ik_b.split('_')):
                ik_to_trials[ik].append(tr)
                id_to_trials[id_xml].append(tr)
                so_to_trials[so].append(tr)
                grf_to_trials[grf].append(tr)
                trials_left.discard(tr)

    # 2) numeric token match
    if trials_left:
        trial_num_map = defaultdict(list)
        for tr in trials_left:
            for n in numeric_tokens(tr.name):
                trial_num_map[n].append(tr)
        for ik, id_xml, so, grf in zip(ik_files, id_files, so_files, grf_files):
            for n in numeric_tokens(ik.name):
                if n in trial_num_map:
                    for tr in trial_num_map[n]:
                        if tr in trials_left:
                            ik_to_trials[ik].append(tr)
                            id_to_trials[id_xml].append(tr)
                            so_to_trials[so].append(tr)
                            grf_to_trials[grf].append(tr)
                            trials_left.discard(tr)

    # 3) positional mapping if counts equal and still unmatched trials remain
    if trials_left:
        unmatched_trials = sorted(list(trials_left))
        iks_unmapped = [ik for ik in ik_files if len(ik_to_trials[ik]) == 0]
        ids_unmapped = [id_xml for id_xml in id_files if len(id_to_trials[id_xml]) == 0]
        sos_unmapped = [so for so in so_files if len(so_to_trials[so]) == 0]
        grfs_unmapped = [grf for grf in grf_files if len(grf_to_trials[grf]) == 0]
        if len(iks_unmapped) == len(unmatched_trials) and len(iks_unmapped) > 0:
            for ik, id_xml, so, grf, tr in zip(sorted(iks_unmapped), sorted(ids_unmapped), 
                                                 sorted(sos_unmapped), sorted(grfs_unmapped), 
                                                 unmatched_trials):
                ik_to_trials[ik].append(tr)
                id_to_trials[id_xml].append(tr)
                so_to_trials[so].append(tr)
                grf_to_trials[grf].append(tr)
                trials_left.discard(tr)

    return ik_to_trials, id_to_trials, so_to_trials, grf_to_trials, list(trials_left)


def find_first_subject(root_dir: Path):
    """Find the first subject folder (containing '01')"""
    candidates = []
    for item in sorted(root_dir.iterdir()):
        if item.is_dir():
            item_str = str(item.name)
            # Check for '01' pattern
            if re.search(r'01', item_str):
                candidates.append(item)
    
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        print("\nMultiple folders found with '01' pattern:")
        return choose_from_list("Select the first subject folder:", candidates, allow_multiple=False)
    else:
        # No '01' found, let user choose
        all_dirs = [d for d in root_dir.iterdir() if d.is_dir()]
        if not all_dirs:
            return None
        print("\nNo folder with '01' pattern found.")
        return choose_from_list("Select the first subject folder:", all_dirs, allow_multiple=False)


def find_all_subjects(root_dir: Path, first_subject: Path):
    """Find all subject folders based on the pattern of first subject"""
    subject_num = detect_subject_number(first_subject.name)
    if not subject_num:
        print("Warning: Could not detect subject number pattern.")
        return [first_subject]
    
    subjects = []
    pattern_template = first_subject.name
    
    # Find all directories that match the pattern
    for item in sorted(root_dir.iterdir()):
        if item.is_dir():
            detected_num = detect_subject_number(item.name)
            if detected_num:
                subjects.append(item)
    
    return sorted(subjects)


def process_first_subject(subject_dir: Path, root_dir: Path):
    """Process first subject interactively and learn the pattern"""
    print(f"\n{'='*60}")
    print(f"PROCESSING FIRST SUBJECT: {subject_dir.name}")
    print(f"{'='*60}")
    
    print("\nFolder structure:")
    print_tree(subject_dir)
    
    # Gather files
    files = gather_files(subject_dir)
    xml_files = [p for p in files if p.suffix.lower() == '.xml']
    trc_files = [p for p in files if p.suffix.lower() == '.trc']
    
    # Find OSIM model in parent directory
    osim_files = gather_files(root_dir, {".osim"})
    osim_model = None
    if len(osim_files) == 1:
        osim_model = osim_files[0]
        print(f"\n Auto-detected OSIM model: {osim_model.name}")
    elif len(osim_files) > 1:
        osim_model = choose_from_list("Multiple .osim files found. Pick one:", osim_files, allow_multiple=False)
    else:
        print("\n No .osim model found in root directory.")
    
    # Detect static TRC
    static_candidates = [p for p in trc_files if 'static' in p.name.lower()]
    static_trc = None
    if len(static_candidates) == 1:
        static_trc = static_candidates[0]
        print(f" Auto-detected static TRC: {static_trc.name}")
    elif len(static_candidates) > 1:
        static_trc = choose_from_list(f"Multiple static TRC candidates in {subject_dir.name}. Pick one:", 
                                       static_candidates, allow_multiple=False)
    else:
        print(" No static TRC auto-detected (expect 'static' in filename).")
    
    # Detect trials (non-static TRC files)
    trials = [p for p in trc_files if p != static_trc]
    print(f"\n Detected {len(trials)} trial TRC(s)")
    
    # Detect IK XMLs
    ik_xmls = [p for p in xml_files if 'ik' in p.name.lower()]
    if ik_xmls:
        print(f" Auto-detected {len(ik_xmls)} IK XML(s)")
    else:
        print(" No IK XMLs auto-detected. Please choose:")
        ik_xmls = choose_from_list("Pick IK XML(s):", xml_files, allow_multiple=True)
        if not ik_xmls:
            ik_xmls = []
    
    # Detect ID XMLs
    id_xmls = [p for p in xml_files if 'id' in p.name.lower()]
    if id_xmls:
        print(f" Auto-detected {len(id_xmls)} ID XML(s)")
    else:
        print(" No ID XMLs auto-detected. Please choose:")
        id_xmls = choose_from_list("Pick ID XML(s):", xml_files, allow_multiple=True)
        if not id_xmls:
            id_xmls = []
    
    # Detect SO XMLs
    so_xmls = [p for p in xml_files if 'so' in p.name.lower()]
    if so_xmls:
        print(f" Auto-detected {len(so_xmls)} SO XML(s)")
    else:
        print(" No SO XMLs auto-detected. Please choose:")
        so_xmls = choose_from_list("Pick SO XML(s):", xml_files, allow_multiple=True)
        if not so_xmls:
            so_xmls = []
    
    # Detect GRF XMLs
    grf_xmls = [p for p in xml_files if 'grf' in p.name.lower()]
    if grf_xmls:
        print(f" Auto-detected {len(grf_xmls)} GRF XML(s)")
    else:
        print(" No GRF XMLs auto-detected. Please choose:")
        grf_xmls = choose_from_list("Pick GRF XML(s):", xml_files, allow_multiple=True)
        if not grf_xmls:
            grf_xmls = []
    
    # Detect Scale XML
    scale_xmls = [p for p in xml_files if 'scale' in p.name.lower()]
    scale_xml = None
    if len(scale_xmls) == 1:
        scale_xml = scale_xmls[0]
        print(f" Auto-detected Scale XML: {scale_xml.name}")
    elif len(scale_xmls) > 1:
        scale_xml = choose_from_list("Multiple Scale XMLs found. Pick one:", scale_xmls, allow_multiple=False)
    else:
        print(" No Scale XML auto-detected. Please choose (or skip):")
        scale_xml = choose_from_list("Choose Scale XML:", xml_files, allow_multiple=False)
    
    # Map XMLs to trials
    ik_to_trials, id_to_trials, so_to_trials, grf_to_trials, trials_unmatched = map_ik_to_trials(
        ik_xmls, id_xmls, so_xmls, grf_xmls, trials
    )
    
    # Build mapped trials
    mapped_trials = []
    for trial in trials:
        ik_xml = next((ik for ik, trs in ik_to_trials.items() if trial in trs), None)
        id_xml = next((id_x for id_x, trs in id_to_trials.items() if trial in trs), None)
        so_xml = next((so for so, trs in so_to_trials.items() if trial in trs), None)
        grf_xml = next((grf for grf, trs in grf_to_trials.items() if trial in trs), None)
        
        if ik_xml:  # Only include trials with IK setup
            mapped_trials.append({
                "trial_trc": trial,
                "ik_xml": ik_xml,
                "id_xml": id_xml,
                "so_xml": so_xml,
                "grf_xml": grf_xml
            })
    
    print(f"\n✓ Successfully mapped {len(mapped_trials)}/{len(trials)} trials")
    
    # Return pattern template
    return {
        "subject_dir": subject_dir,
        "osim_model": osim_model,
        "static_trc": static_trc,
        "scale_xml": scale_xml,
        "mapped_trials": mapped_trials
    }


def replace_subject_number(path: Path, old_num: str, new_num: str):
    """Replace subject number in path"""
    path_str = str(path)
    # Try multiple replacement patterns
    patterns = [
        (rf'[Ss]ubject[_-]?{old_num}', lambda m: m.group(0).replace(old_num, new_num)),
        (rf'[Ss]{old_num}', lambda m: m.group(0).replace(old_num, new_num)),
        (rf'(?<=[/\\]){old_num}(?=[/\\]|$)', new_num),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, path_str):
            print("\033[96mThis text will be green.\033[0m")
            new_path_str = re.sub(pattern, replacement, path_str)
            print(Path(new_path_str))
            return Path(new_path_str)
    
    return None


def apply_pattern_to_subject(template, subject_dir: Path, first_subject_dir: Path):
    """Apply learned pattern to a new subject"""
    first_num = detect_subject_number(first_subject_dir.name)
    new_num = detect_subject_number(subject_dir.name)
    
    if not first_num or not new_num:
        return None, f"Could not detect subject numbers"
    
    def apply_to_path(path):
        if path is None:
            return None
        new_path = replace_subject_number(path, first_num, new_num)
        if new_path and new_path.exists():
            return new_path
        return None
    
    # Apply pattern
    print("\033[092m static \033[0m")
    static_trc = apply_to_path(template["static_trc"])
    print("\033[092m scale\033[0m")
    scale_xml = apply_to_path(template["scale_xml"])

    # print("\033[31mThis text will be red.\033[0m")
    # print(scale_xml)
    # print("\033[31mThis text will be red.\033[0m")

    mapped_trials = []
    for trial_template in template["mapped_trials"]:
        print(f"\033[093m {trial_template} \033[0m")
        trial_trc = apply_to_path(trial_template["trial_trc"])
        ik_xml = apply_to_path(trial_template["ik_xml"])
        id_xml = apply_to_path(trial_template["id_xml"])
        so_xml = apply_to_path(trial_template["so_xml"])
        grf_xml = apply_to_path(trial_template["grf_xml"])
        
        mapped_trials.append({
            "trial_trc": trial_trc,
            "ik_xml": ik_xml,
            "id_xml": id_xml,
            "so_xml": so_xml,
            "grf_xml": grf_xml
        })
    
    return {
        "subject_dir": subject_dir,
        "osim_model": template["osim_model"],  # Same OSIM for all
        "static_trc": static_trc,
        "scale_xml": scale_xml,
        "mapped_trials": mapped_trials
    }, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_subjects_json_pattern.py /path/to/root_directory")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).expanduser().resolve()
    if not root_dir.is_dir():
        print("Root directory must be a valid directory.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"ROOT DIRECTORY: {root_dir}")
    print(f"{'='*60}")
    
    # Find first subject
    first_subject = find_first_subject(root_dir)
    if not first_subject:
        print("Error: No valid subject folder found.")
        sys.exit(1)
    
    # Process first subject interactively
    template = process_first_subject(first_subject, root_dir)
    
    # Find all subjects
    all_subjects = find_all_subjects(root_dir, first_subject)
    print(f"\n{'='*60}")
    print(f"Found {len(all_subjects)} total subjects")
    print(f"{'='*60}")
    
    # Apply pattern to all subjects
    processed_subjects = []
    skipped_subjects = []
    
    for i, subject_dir in enumerate(all_subjects, 1):
        print(f"\n[{i}/{len(all_subjects)}] Processing: {subject_dir.name}")
        
        if subject_dir == first_subject:
            # First subject already processed
            subject_data = {
                "subject": str(template["subject_dir"]),
                "subject_name": template["subject_dir"].name,
                "model": str(template["osim_model"]) if template["osim_model"] else None,
                "static_trc": str(template["static_trc"]) if template["static_trc"] else None,
                "scale_xml": str(template["scale_xml"]) if template["scale_xml"] else None,
                "mapped_trials": [
                    {
                        "trial_trc": str(t["trial_trc"]) if t["trial_trc"] else None,
                        "ik_xml": str(t["ik_xml"]) if t["ik_xml"] else None,
                        "id_xml": str(t["id_xml"]) if t["id_xml"] else None,
                        "so_xml": str(t["so_xml"]) if t["so_xml"] else None,
                        "grf_xml": str(t["grf_xml"]) if t["grf_xml"] else None
                    }
                    for t in template["mapped_trials"]
                ]
            }
            processed_subjects.append(subject_data)
            print("  (First subject - template)")
        else:
            # Apply pattern
            result, error = apply_pattern_to_subject(template, subject_dir, first_subject)
            if result:
                subject_data = {
                    "subject": str(result["subject_dir"]),
                    "subject_name": result["subject_dir"].name,
                    "model": str(result["osim_model"]) if result["osim_model"] else None,
                    "static_trc": str(result["static_trc"]) if result["static_trc"] else None,
                    "scale_xml": str(result["scale_xml"]) if result["scale_xml"] else None,
                    "mapped_trials": [
                        {
                            "trial_trc": str(t["trial_trc"]) if t["trial_trc"] else None,
                            "ik_xml": str(t["ik_xml"]) if t["ik_xml"] else None,
                            "id_xml": str(t["id_xml"]) if t["id_xml"] else None,
                            "so_xml": str(t["so_xml"]) if t["so_xml"] else None,
                            "grf_xml": str(t["grf_xml"]) if t["grf_xml"] else None
                        }
                        for t in result["mapped_trials"]
                    ]
                }
                processed_subjects.append(subject_data)
                print("  Pattern applied")
            else:
                skipped_subjects.append({
                    "subject": str(subject_dir),
                    "subject_name": subject_dir.name,
                    "reason": error
                })
                print(f"  Skipped: {error}")
    
    # Create final JSON
    output_data = {
        "root_directory": str(root_dir),
        "total_subjects": len(all_subjects),
        "processed_subjects": len(processed_subjects),
        "skipped_subjects_count": len(skipped_subjects),
        "subjects": processed_subjects,
        "skipped_subjects": skipped_subjects
    }
    
    # Write to file
    output_path = OUTPUT
    Path(output_path).write_text(json.dumps(output_data, indent=2))
    
    print(f"\n{'='*60}")
    print(f" Successfully processed {len(processed_subjects)}/{len(all_subjects)} subjects")
    if skipped_subjects:
        print(f" Skipped {len(skipped_subjects)} subjects")
    print(f" JSON file written to: {output_path}")
    print(f"{'='*60}\n")
    


if __name__ == "__main__":
    main()