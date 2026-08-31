# PIM Offloading for SpMV Acceleration on HBM2

This repository contains the co-simulation environment (gem5 + DRAMSys) developed to validate a Processing-In-Memory (PIM) architecture applied to Sparse Matrix-Vector Multiplication (SpMV). This research targets the elimination of the von Neumann bottleneck (Memory Wall) for memory-bound High-Performance Computing (HPC) workloads.

## System Architecture & Hybrid Topology

To bypass the Transactional Level Modeling (TLM) limitations of bare-metal booting directly on HBM2, this system implements a hybrid memory topology:

* **Standard DDR3:** Hosts the boot segment and the host CPU bare-metal firmware. This ensures stable system initialization.
* **HBM2 (via DRAMSys):** Serves as an exclusive PIM offloading space containing the CSR matrix structure and the hardware PIM kernel. The memory controller is strictly configured to **FR-FCFS** (First-Ready, First-Come, First-Serve) with an **Open-Page** policy to maximize row hits and internal inter-bank bandwidth.

## Firmware Submodule (PIMSys)

The bare-metal executable (Rust `no_std`) and the VLIW hardware microcode are managed in the `ext/PIMSys` submodule. Ensure the submodule is initialized when cloning this repository.

## Source Tree & File Architecture

The repository follows the standard gem5 directory structure, heavily customized to support our hybrid memory topology and PIM co-simulation. Below is the detailed file hierarchy:

    gem5-pim-spmv/
    ├── configs/
    │   ├── pim_simulation.py       # Main gem5 Python orchestration script mapping the DDR3 and HBM2 memory spaces
    │   └── pim-hbm2.json           # DRAMSys configuration defining the FR-FCFS controller, Open-Page policy, and 32 banks
    ├── ext/
    │   └── PIMSys/                 # Git submodule containing the bare-metal Rust orchestrator and VLIW microcode
    ├── src/
    │   └── mem/                    # Modified gem5 memory system C++ source files to support custom PIM TLM packets
    ├── build/                      # Target directory for compiled gem5 binaries (e.g., ARM/gem5.opt)
    ├── m5out/                      # Auto-generated directory containing simulation results (stats.txt, config.ini)
    └── README.md                   # This architectural documentation file

## Test Scenarios & Execution

Two distinct execution scenarios are provided to demonstrate the "Memory Wall" bottleneck and the resolution brought by our PIM architecture.

### A. CPU Baseline Execution (No PIM)

The ARM processor sequentially fetches the sparse matrix through the system bus to perform the computation locally.

    ./build/ARM/gem5.opt configs/pim_simulation.py --kernel=ext/PIMSys/pim-os/target/aarch64-unknown-none/release/baseline

### B. PIM Accelerated Execution (HPC Offloading)

The ARM processor acts strictly as an orchestrator. It distributes the computational load across the 32 HBM2 banks, dispatches the execution signal, and enters deep sleep (wfi).

    ./build/ARM/gem5.opt configs/pim_simulation.py --kernel=ext/PIMSys/pim-os/target/aarch64-unknown-none/release/vadd

## Experimental Results (gem5 Metrics)

Tests conducted on a synthetic CSR matrix (2048x2048, NNZ=8192) demonstrate the overwhelming superiority of the PIM approach:

| Metric | CPU Sequential (Baseline) | PIM Acceleration (HPC) | Analysis / Impact |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 239.61 s | 41.42 s | **5.8x Speedup.** Bypasses the ~240 trillion simulated idle ticks caused by CPU memory starvation. |
| **External Bus Bandwidth** | 1,089 B/s (Saturated/Fragmented) | ~6,297 B/s (Broadcast only) | **Elimination of the Memory Wall.** Traffic is localized entirely within the HBM2 internal channels. |
| **CPU Footprint (Instructions)**| 151,670 (Massive pipeline stalls) | 151,670 (Strict firmware budget) | **WFI sleep state validated.** Low instruction count in PIM reflects an optimized, finite firmware budget. |
| **Load Distribution** | Channel 0 bottlenecked | Evenly distributed | **32-bank parallelism confirmed.** The NNZ partitioner successfully prevents internal memory contention. |

## Current Limitations: Power Analysis

Currently, the DRAMSys native power analysis module lacks mathematical models for 3D topologies and ultra-wide channels inherent to HBM2 standards. Enabling it causes fatal segmentation faults during TLM binding. Therefore, `PowerAnalysis` is set to `false` in `pim-hbm2.json`. Accurate energy metrics and thermal dissipation profiling will be addressed during future physical hardware implementation phases.
