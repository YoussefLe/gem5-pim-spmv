# PIM Offloading for SpMV Acceleration on HBM2

This repository contains the co-simulation environment (gem5 + DRAMSys) designed to validate a Processing-In-Memory (PIM) architecture applied to Sparse Matrix-Vector Multiplication (SpMV).

## System Architecture & Hybrid Topology

To bypass the Transactional Level Modeling (TLM) limitations of bare-metal booting directly on HBM2, this system implements a hybrid memory topology:

* **Standard DDR3:** Hosts the boot segment and the host CPU bare-metal firmware.
* **HBM2 (via DRAMSys):** Serves as an exclusive PIM offloading space containing the CSR matrix structure and the hardware PIM kernel. The memory controller is strictly configured to **FR-FCFS** (First-Ready, First-Come, First-Serve) with an **Open-Page** policy to maximize row hits and internal inter-bank bandwidth.

## Firmware Submodule (PIMSys)

The bare-metal executable (Rust `no_std`) and the VLIW hardware microcode are managed in the `ext/PIMSys` submodule. Ensure the submodule is initialized when cloning this repository.

## Test Scenarios & Execution

Two distinct execution scenarios are provided to demonstrate the "Memory Wall" bottleneck and the resolution brought by our PIM architecture.

### A. CPU Baseline Execution (No PIM)

The ARM processor sequentially fetches the sparse matrix through the system bus to perform the computation locally.

```bash
./build/ARM/gem5.opt configs/pim_simulation.py --kernel=ext/PIMSys/pim-os/target/aarch64-unknown-none/release/baseline
```

### B. PIM Accelerated Execution (HPC Offloading)

The ARM processor acts strictly as an orchestrator. It distributes the computational load across the 32 HBM2 banks, dispatches the execution signal, and enters deep sleep (wfi).

```bash
./build/ARM/gem5.opt configs/pim_simulation.py --kernel=ext/PIMSys/pim-os/target/aarch64-unknown-none/release/vadd
```

## Experimental Results (gem5 Metrics)

Tests conducted on a synthetic CSR matrix (2048x2048, NNZ=8192) demonstrate the overwhelming superiority of the PIM approach:

| Metric | CPU Sequential (Baseline) | PIM Acceleration (HPC) | Analysis / Impact |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 239.61 s | 41.42 s | 5.8x Speedup |
| **External Bus Bandwidth** | 1,089 B/s (Saturated/Fragmented) | ~6,297 B/s (Broadcast only) | Elimination of the Memory Wall |
| **CPU Footprint (Instructions)**| 151,670 (Massive pipeline stalls) | 151,670 (Strict firmware budget) | WFI sleep state validated |
| **Load Distribution** | Channel 0 bottlenecked | Evenly distributed | 32-bank parallelism confirmed |

### Current Limitations: Power Analysis

Currently, the DRAMSys native power analysis module lacks mathematical models for 3D topologies and ultra-wide channels inherent to HBM2 standards. Enabling it causes fatal segmentation faults during TLM binding. Therefore, `PowerAnalysis` is set to `false` in `pim-hbm2.json`. 
