#  meshing-deformation-cfd-batch
A repository for generating, deforming, and performing fluid flow simulations of patient-specific vascular models based on centerline information, with support for batch processing.

## Features
- Automatic generation of tetra–prism hybrid meshes for CFD from tubular geometries
- Adaptive control of prism layer thickness and mesh resolution based on local radius, without explicit domain partitioning
- Centerline-based deformation of prism meshes while preserving element counts
- Batch processing of the entire pipeline, including CFD simulations, for multiple datasets
- Parallel execution for multiple cases on HPC systems such as [Fugaku](docs/fugaku/)

## Pipeline
1. Generate a surface mesh from a centerline ([TubeFromCenterline](TubeFromCenterline/))
2. Generate a CFD mesh from a surface mesh ([meshing module](meshing_deform/src/meshing/))
3. Deform a reference CFD mesh using reference and target centerlines ([deform module](meshing_deform/src/deform/))
4. Run fluid flow simulations using OpenFOAM
   
&nbsp;&nbsp;&nbsp; **Batch execution:**  
&nbsp;&nbsp;&nbsp; The entire pipeline can be executed in batch for multiple datasets ([batch](batch/)).

## Requirements
+ Python3.11 or Python3.12

## Getting Started
### Getting Started on Local Machine (Windows or Linux)
1. Clone the repository
   ``` bash
   git clone <repository-url>
   cd meshing-deformation-cfd-batch
   ```
2. Install dependencies for `meshing_deform`
   ``` bash
   # make python virtual environment
   python3 -m venv venv
   
   # activate the virtual environment
   # on Bash
   source venv/bin/activate
   # on PowerShell
   .\venv\Scripts\Activate

   # install dependencies
   pip install -e meshing_deform
   ```
3. Run modules
   ``` bash
   python -m meshing.main
   # or
   python -m deform.main
   ```
   
### Getting Started on Fugaku
See the documentation [here](docs/fugaku) .

## Project Structure
``` bash
  meshing-deformation-cfd-batch/
  ├─ meshing_deform/
  │     ├─ src/ 
  │     │    ├─ meshing/
  │     │    ├─ deform/
  │     │    ├─ postcheck/ 
  │     │    └─ commonlib/
  │     ├─ requirements.txt
  │     └─ pyproject.toml  
  ├─ TubeFromCenterline/   # generate surface(*.stl) from centerline(*.csv) 
  ├─ openfoam_cases/    # template cases
  │     ├─ simpleFoam/
  │     └─ pimpleFoam/
  ├─ batch/
  ├─ inputs/           # input data (not generated automatically)
  │     ├─ original/   # 基準メッシュの生成に用いる中心線(*.csv)と表面(*.stl)
  │     └─ target/     # 変形目標となる中心線(*.csv). バッチ処理のため複数case
  ├─ runs/             # generated outputs (safe to delete)
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

