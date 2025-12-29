# README

# Tested Environment
+ Windows11
  + Python3.12
+ Ubuntu22.04
  + Python3.12
+ RHEL 8.1 (富岳)
  + Python3.11.11

**Note** <br>
Windowsで使う場合は、`meshing_deform/src/meshing/main.py`及び、`meshing_deform/src/deform/main.py`内の`run_checkmesh()`関数をコメントアウトしてください。


## Setup

## Usage
0. venv仮想環境をactivateする
   ``` bash
   # bash の場合
   source venv/bin/activate
   # PowerShell の場合
   .\venv\Scripts\Activate
   ```
1. `meshing-deformation-cfd-batch`以下のどの階層にいてもいいので、以下を実行 <br>
   **メッシュ生成**
   ``` bash
   python -m meshing.main
   ```
   **メッシュ変形**
   ``` bash
   python -m deform.main
   ```
