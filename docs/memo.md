# Tested Environment

+ Ubuntu24.04
  + Python3.12
  + OpenFOAM-v2506

+ Fugaku (RedHat)
  + Python3.11.11
  + OpenFOAM-v2412 

In this project, recommended python version is **Python 3.11 or 3.12**.

# Getting Started
## setup
### on Linux (Ubuntu/Debian)
1. Install Python (skip if already installed)
``` bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
python3.12 --version
# (Alternatively, you may install Python 3.11)
```
2. Clone the repository
``` bash
git clone https://github.com/ut-olab/vascular-cfd-pipeline.git
```
``` bash
cd vascular-cfd-pipeline
```
3. Create and activate python venv
``` bash
python3 -m venv venv
source venv/bin/activate
python --version
```
4. Install dependencies
``` bash
pip install -e meshing_deform
```

### on Fugaku
Please see `docs/fugaku/README.md`

## プログラム実行
### メッシュ生成 / 変形
+ メッシュ生成
``` bash
python -m meshing.main
```
+ メッシュ変形
``` bash
python -m deform.main
```

### バッチ処理 (大量のメッシュを生成、変形、流体解析)
``` bash
cd batch
python -m batch.py batch_cases.csv
```


## Project Structure
``` bash
  vascular-cfd-pipeline/
  ├─ venv/ 
  ├─ meshing_deform/
  │     ├─ src/ 
  │     │    ├─ meshing/
  │     │    │       ├─ __init__.py                    
  │     │    │       ├─ main.py                   
  │     │    │       ├─ config.py
  │     │    │       └─ README.md
  │     │    │
  │     │    ├─ deform/
  │     │    │       ├─ centerline/  
  │     │    │       │      ├─ __init__.py
  │     │    │       │      ├─ adjust_num_of_cl.py
  │     │    │       │      ├─ alignment.py
  │     │    │       │      └─ README.md
  │     │    │       ├─ smooth/
  │     │    │       │      ├─ __init__.py
  │     │    │       │      ├─ edgeswap.py
  │     │    │       │      ├─ smoother_vtk.py
  │     │    │       │      └─ README.md
  │     │    │       ├─ __init__.py
  │     │    │       ├─ main.py
  │     │    │       ├─ config.py
  │     │    │       └─ README.md
  │     │    │
  │     │    ├─ postcheck/  # _with_ccnID.vtk を出力するコードを入れる
  │     │    │       ├─ __init__.py
  │     │    │       ├─ hausdorff.py
  │     │    │       ├─ openfoam_checkmesh.py
  │     │    │       ├─ _with_ccnID.vtk を出力するコード
  │     │    │       └─ README.md
  │     │    │     
  │     │    └─ commonlib/
  │     │            ├─ __init__.py
  │     │            ├─ node.py          
  │     │            ├─ cell.py      
  │     │            ├─ boundarylayer.py
  │     │            ├─ meshinfo.py   
  │     │            ├─ func.py            
  │     │            ├─ utility.py
  │     │            └─ README.md
  │     ├─ requirements.txt
  │     ├─ pyproject.toml
  │     ├─ .gitignore
  │     └─ README.md
  │     
  ├─ TubeFromCenterline/   # generate surface(*.stl) from centerline(*.csv)
  │     ├─ TubeFromCenterline.cpp
  │     ├─ CMakeLists.txt
  │     ├─ .gitignore
  │     └─ README.md
  │     
  ├─ openfoam_cases/    # template cases
  │     ├─ simpleFoam/
  │     ├─ pimpleFoam/
  │     └─ README.md
  ├─ batch/
  │     ├─ batch.py
  │     ├─ batch_cases.csv
  │     ├─ README.md
  │     └─ .gitignore
  ├─ inputs/           # input data (not generated automatically)
  │     ├─ original/   # 基準メッシュの生成に用いる中心線(*.csv)と表面(*.stl)
  │     └─ target/     # 変形目標となる中心線(*.csv). バッチ処理のため複数case
  ├─ runs/             # generated outputs (safe to delete)
  │     ├─ run_case1/ 
  │     ├─ run_case2/
  │     ...
  │
  ├─ jobs/
  │     └─ fugaku/
  ├─ docs/
  │     ├─ figures/
  │     └─ fugaku/
  │             ├─ build_gmsh.sh
  │             ├─ run_python_gmsh.sh
  │             ├─ pyproject.toml
  │             └─ README.md
  ├─ README.md
  └─ .gitignore  
```