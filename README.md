# QM9-HighThroughput-xTB-Pipeline
An end-to-end, fault-tolerant high-throughput pipeline designed for data curation and quantum chemical property calculations (via xTB) of 133,885 QM9 molecules. Features automated checkpoint-resume and sandboxed runtime isolation. Developed by Dawson Choy (CUHK).
# QM9-HighThroughput-xTB-Pipeline

[![Python Version](https://shields.io)](https://python.org)
[![Platform](https://shields.io)](https://github.com)

An end-to-end, fault-tolerant data curation and high-throughput computational chemistry pipeline designed to extract, standardize, and execute semi-empirical quantum chemical property calculations (via `xTB`) for **133,885 organic molecules** from the benchmark QM9 dataset.

Developed by **Dawson Choy** (Department of Chemistry, The Chinese University of Hong Kong).
---
## 🚀 Key Engineering & Architectural Features

* **Fault-Tolerant Checkpoint & Resume Mechanics**: Implemented an automated log-parsing evaluation engine that validates previous calculation files (by checking for `"normal termination of xtb"`). It seamlessly bypasses completed operations during a rerun, preventing compute redundancy and mitigating hardware failure risks.
* **Regex-Driven Data Curation**: Designed custom regular expression parsers to isolate `InChI` molecular formulas from complex, non-standard source text headers, dynamically remapping them to generate human-readable, indexed standard XYZ files.
* **Sandboxed Runtime Isolation**: To bypass OS file-system bottlenecks when handling 130,000+ data clusters, the pipeline dynamically isolates each molecular evaluation inside its own ephemeral subdirectory domain (`cwd` switching via Python's `subprocess`).
* **Automated Exception Blacklisting**: Features an asynchronous-style `try-except` crash-tracking pipeline that automatically appends non-convergent or structurally unstable geometries directly into an execution blacklist (`crash_list.txt`) without terminating the core scheduler.
---
## 🛠️ Pipeline Workflow Architecture

1. **Step 1: Automated Ingestion (`find_and_extract_qm9`)**
   * Dynamically tracks the system's native environment paths (cross-platform compatibility).
   * Locates and unpacks the raw QM9 tarball compressions securely within 1-3 minutes.
2. **Step 2: Standardization & Curating (`curate_and_standardize_qm9`)**
   * Re-engineers raw data into strict standard XYZ coordinates (Atom count -> Blank comment line -> Coordinates) required for modern quantum chemistry engines.
   * Enforces rigorous natural numerical sorting for absolute data lineage integrity.
3. **Step 3: High-Throughput Compute Console (`run_high_throughput_xtb`)**
   * Spawns sandboxed `xTB` command-line processes targeting multi-thousand molecular batch loops using `--scc` self-consistent charge single-point parameters.
---
## 📦 Prerequisites & Environment Setup
Ensure you have Python 3.8+ and the `xtb` binary configured in your system environment variables (`PATH`).
```bash
# Verify xTB environment availability
xtb --version
```
---
## 🏃‍♂️ How to Run
Simply download your raw QM9 data tarball (`dsgdb9nsd.xyz.tar.bz2`) into your system's default **Downloads** directory, and trigger the pipeline core orchestration:
```bash
python pipeline.py
```
---
## 📊 Summary Statistics & Impact
* **Target Scale**: 133,885 Molecular Graphs
* **Execution Paradigm**: Dry Lab Automation (High-Throughput Quantum Chemical Profiling)
* **Downstream Applications**: Generation of molecular representations (HOMO-LUMO Gaps, Total Energies, Orbital Matrixes) for AI Drug Discovery, Deep Learning Property Predictions, and Molecular ML architectures.
