#  vascular-cfd-pipeline
A repository for generating, deforming, and performing fluid flow simulations of patient-specific vascular models based on centerline information, with support for batch processing.<br>
The core functionality of this repository is implemented in `meshing_deform`, which provides centerline-driven CFD mesh generation, mesh deformation, and post-processing utilities for patient-specific vascular models.

## Features
- Automatic generation of tetra–prism hybrid meshes for CFD from tubular geometries
- Adaptive control of prism layer thickness and mesh resolution based on local radius, without explicit domain partitioning
- Centerline-based deformation of prism meshes while preserving element counts
- Batch processing of the entire pipeline, including CFD simulations, for multiple datasets
- Parallel execution for multiple cases on HPC systems such as [Fugaku](https://www.r-ccs.riken.jp/fugaku/)

## Pipeline
1. Generate a surface mesh from a centerline ([TubeFromCenterline](TubeFromCenterline/))
2. Generate a CFD mesh from a surface mesh ([meshing module](meshing_deform/src/meshing/))
3. Deform a reference CFD mesh using reference and target centerlines ([deform module](meshing_deform/src/deform/))
4. Run fluid flow simulations using OpenFOAM
   
&nbsp;&nbsp;&nbsp; **Batch execution:**  
&nbsp;&nbsp;&nbsp; The entire pipeline can be executed in batch for multiple datasets ([batch](batch/)).

## Requirements
+ Linux
+ Python3.11 or Python3.12
+ OpenFOAM

## Getting Started
### Getting Started on Local Machine (Linux)
1. Clone the repository
   ``` bash
   git clone <repository-url>
   cd vascular-cfd-pipeline
   ```
2. Rename inputs folder
   ``` bash
   mv inputs_share inputs
   ``` 
3. Install dependencies for `meshing_deform`
   ``` bash
   # make python virtual environment
   python3 -m venv venv
   
   # activate the virtual environment
   source venv/bin/activate

   # install dependencies
   pip install -e meshing_deform
   ```
4. Run modules
   ``` bash
   python -m meshing.main
   # or
   python -m deform.main
   ```

**(Optional) Run batch pipeline for multiple cases**
``` bash
cd batch
python batch_auto.py
```

### Getting Started on Fugaku
See the documentation [here](docs/fugaku) .

## Project Structure
``` bash
  vascular-cfd-pipeline/ 
  ├─ meshing_deform/       # Core library of this repository
  │     ├─ src/ 
  │     │    ├─ meshing/   # surface → tetra–prism hybrid meshing   
  │     │    ├─ deform/    # centerline-based mesh deformation
  │     │    ├─ postcheck/ 
  │     │    └─ commonlib/
  │     ├─ requirements.txt
  │     └─ pyproject.toml  
  ├─ TubeFromCenterline/   # generate surface(*.stl) from centerline(*.csv) 
  ├─ openfoam_cases/       # template cases
  │     ├─ simpleFoam/
  │     └─ pimpleFoam/
  ├─ batch/
  │     └─ batch_auto.py   # run batch process
  ├─ inputs/               # input data 
  │     ├─ original/   
  │     └─ target/     
  ├─ runs/                 # generated outputs (safe to delete)
  │     ├─ run_case1/ 
  │     ├─ run_case2/
  │     ...
  ├─ jobs/
  │     └─ fugaku/
  └─ docs/
        ├─ figures/
        └─ fugaku/
                ├─ build_gmsh.sh
                ├─ run_python_gmsh.sh
                ├─ pyproject.toml
                └─ README.md

```





