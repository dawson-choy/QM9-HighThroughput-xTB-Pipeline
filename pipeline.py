"""
QM9 High-Throughput Quantum Chemistry Calculation Pipeline
Author: Dawson Choy (CUHK)
Description: An end-to-end, fault-tolerant workflow designed to extract, curate, 
             and calculate semi-empirical quantum chemical properties (via xTB) 
             for 133,885 molecules from the benchmark QM9 dataset.
"""

import os
import re
import glob
import tarfile
import shutil
import subprocess

def find_and_extract_qm9(base_dir):
    """
    Step 1: Automatically search and extract the raw QM9 tarball within the directory.
    """
    print(f"🔍 [STEP 1] Searching for QM9 tarball in: {base_dir}")
    search_pattern = os.path.join(base_dir, "*dsgdb9nsd*")
    found_files = glob.glob(search_pattern)
    
    if not found_files:
        print("❌ Error: Cannot find any file containing 'dsgdb9nsd' in the specified directory!")
        return None

    tar_path = None
    for file in found_files:
        if os.path.isfile(file) and file.endswith(('.tar', '.tgz', '.tar.bz2', '.tar.gz')):
            tar_path = file
            break
            
    if not tar_path:
        tar_path = found_files[0]
        
    target_dir = os.path.join(base_dir, "qm9_all_extracted")
    print(f"🎯 Tarball localized at: {tar_path}")
    print("⏳ Extracting 133,885 molecular files. Please wait (approx. 1-3 mins)...")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    try:
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(path=target_dir)
        extracted_files = os.listdir(target_dir)
        print(f"✨ Extraction Successful! Total files extracted: {len(extracted_files)}")
        return target_dir
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None


def curate_and_standardize_qm9(input_folder, base_dir):
    """
    Step 2: Parse raw non-standard QM9 XYZ files, extract formulas via Regex, 
            and reformat them into strict standard XYZ coordinates for quantum chemistry engines.
    """
    output_folder = os.path.join(base_dir, "qm9_standard_xyz_final")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    print(f"\n🔍 [STEP 2] Commencing Data Curation in: {input_folder}")
    search_pattern = os.path.join(input_folder, "dsgdb9nsd_*.xyz")
    file_list = glob.glob(search_pattern)
    
    total_files = len(file_list)
    if total_files == 0:
        print("❌ Error: No raw XYZ files detected!")
        return None
        
    # Enforce strict natural numerical sorting for data lineage integrity
    file_list.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
    print(f"📊 Total raw files sorted: {total_files}")
    print("⏭️ Skipping the first 4 manually validated structures. Starting batch curation...")
    
    success_count = 0
    for file_path in file_list:
        try:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            file_id_num = int(base_name.split('_')[-1])
            
            # Skip first 4 sample baseline files
            if file_id_num < 5:
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                
            if not lines:
                continue

            atom_count = int(lines[0].strip())
            last_line = lines[-1].strip()
            
            # Regex mapping to isolate InChI molecular formula for file indexing
            match = re.search(r'InChI=1S/([^/]+)', last_line)
            formula = match.group(1) if match else "Unknown"
            
            # Construct standard XYZ format (Line 1: Atom Count, Line 2: Blank Comment, Line 3+: Coordinates)
            cleaned_lines = [f"{atom_count}\n", "\n"]
            for i in range(2, 2 + atom_count):
                if i < len(lines):
                    cleaned_lines.append(f"{lines[i]}\n")
            
            file_id_str = f"{file_id_num:06d}"
            output_filename = f"{formula}_{file_id_str}.xyz"
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
                
            success_count += 1
            if success_count % 10000 == 0:
                print(f"⏳ Curation Progress: [{success_count}/{total_files - 4}] files processed...")
                
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(file_path)}: {e}")
            
    print(f"✨ Curation Complete! Standardized datasets saved at: {output_folder}")
    return output_folder


def run_high_throughput_xtb(xyz_folder, base_dir):
    """
    Step 3: Fault-tolerant execution console for xTB. Features sandboxed environments 
            and checkpoint-resume capability to flag non-convergent geometries.
    """
    project_output_dir = os.path.join(base_dir, "qm9_xtb_project_results")
    if not os.path.exists(project_output_dir):
        os.makedirs(project_output_dir)
        
    crash_list_path = os.path.join(project_output_dir, "crash_list.txt")
    
    search_pattern = os.path.join(xyz_folder, "*.xyz")
    xyz_files = glob.glob(search_pattern)
    total_files = len(xyz_files)
    
    if total_files == 0:
        print("❌ Error: No standardized XYZ inputs found!")
        return
        
    xyz_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
    print(f"\n🚀 [STEP 3] Launching High-Throughput xTB Compute Console...")
    print(f"📊 Target Inventory: {total_files} curated molecular graphs.")
    print(f"📝 Appending execution blacklists to: {crash_list_path}\n")
    
    success_count = 0
    skipped_count = 0
    crash_count = 0
    
    for xyz_path in xyz_files:
        abs_xyz_path = os.path.abspath(xyz_path)
        file_name_without_ext = os.path.splitext(os.path.basename(xyz_path))[0]
        
        custom_name = f"{file_name_without_ext}_sp_gas_phase"
        sub_folder_path = os.path.join(project_output_dir, custom_name)
        out_log_path = os.path.join(sub_folder_path, f"{custom_name}.out")
        
        # [CRITICAL CRITERIA] Checkpoint & Resume: Bypass completed operations seamlessly
        if os.path.exists(out_log_path):
            with open(out_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                if "normal termination of xtb" in f.read().lower():
                    skipped_count += 1
                    continue
        
        if not os.path.exists(sub_folder_path):
            os.makedirs(sub_folder_path)
            
        dest_xyz_path = os.path.join(sub_folder_path, f"{custom_name}.xyz")
        if not os.path.exists(dest_xyz_path):
            shutil.copy2(abs_xyz_path, dest_xyz_path)
        
        # Configure xTB CLI args (--scc for self-consistent charge single-point calculations)
        cmd = ["xtb", os.path.basename(dest_xyz_path), "--scc"]
        
        try:
            with open(out_log_path, "w", encoding="utf-8") as out_f:
                subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True, check=True, cwd=sub_folder_path)
            
            success_count += 1
            if (success_count + skipped_count) % 1000 == 0:
                print(f"⏳ Progress: [{success_count + skipped_count}/{total_files}] | New: {success_count} | Skipped: {skipped_count} | Crashed: {crash_count}")
                    
        except subprocess.CalledProcessError:
            crash_count += 1
            print(f"❌ Geometry Evaluation Crash tracked for molecule: {file_name_without_ext}. Skipping...")
            with open(crash_list_path, "a", encoding="utf-8") as crash_f:
                crash_f.write(f"{file_name_without_ext}.xyz\n")
            continue
            
        except FileNotFoundError:
            print("\n❌ Environment Error: 'xtb' command binary not detected in system PATH variable!")
            return

    print(f"\n✨ Workflow Pipeline Fully Concluded!")
    print(f"📊 Summary Statistics -> Computed: {success_count} | Checkpoint Skipped: {skipped_count} | Logged Crashes: {crash_count}")


if __name__ == "__main__":
    # Dynamically targets the user's cross-platform Downloads directory to avoid hardcoded user paths.
    USER_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # Executing the full orchestrated workflow
    raw_dir = find_and_extract_qm9(USER_DOWNLOAD_DIR)
    if raw_dir:
        standardized_dir = curate_and_standardize_qm9(raw_dir, USER_DOWNLOAD_DIR)
        if standardized_dir:
            run_high_throughput_xtb(standardized_dir, USER_DOWNLOAD_DIR)
