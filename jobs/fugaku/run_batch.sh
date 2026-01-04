#!/bin/bash
# ============================================================
# Fugaku PJM job script template
#   - runs batch/batch.py with venv + gmsh (source-built)
#   - project layout:
#     vascular-cfd-pipeline/
#       venv/
#       batch/batch.py
#       batch/batch_cases.csv
#       runs/
#       jobs/fugaku/run_batch.sh   (this file)
# ============================================================

#PJM -g hp120306
#PJM -L "node=1"
#PJM -L "rscgrp=small"
#PJM -L "elapse=02:00:00"
#PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004
# 必要なら（例）:
##PJM -L "node=2"
##PJM --mpi "max-proc-per-node=1"

set -euo pipefail

echo "[INFO] job start: $(date)"
echo "[INFO] host: $(hostname)"
echo "[INFO] pwd : $(pwd)"

# ====== 0) Spack 環境（必要なら） ======
# ※あなたの環境に合わせてパスを調整
. /home/u14406/spack/share/spack/setup-env.sh

# ====== 1) Python を用意（spack の python を使う例） ======
spack load /7heyycu

echo "[INFO] python=$(which python)"
python --version

# ====== 2) OpenFOAM を用意 ======
export FUGAKU=1
spack load  openfoam@2412 arch=linux-rhel8-a64fx

# ====== 3) プロジェクトルートへ移動 ======
# この run_batch.sh は jobs/fugaku/ にある前提
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "[INFO] SCRIPT_DIR   = ${SCRIPT_DIR}"
echo "[INFO] PROJECT_ROOT = ${PROJECT_ROOT}"

cd "${PROJECT_ROOT}"

# ====== 4) gmsh (source-built) の Python API / shared lib を見せる ======
export GMSH_PREFIX=/vol0002/mdt1/data/hp120306/u14406/local/gmsh/4.13.1
export PYTHONPATH="${GMSH_PREFIX}/lib64:${PYTHONPATH:-}"

# libgmsh.so の場所
export LD_LIBRARY_PATH="${GMSH_PREFIX}/lib64:${LD_LIBRARY_PATH:-}"

echo "[INFO] GMSH_PREFIX      = ${GMSH_PREFIX}"
echo "[INFO] PYTHONPATH       = ${PYTHONPATH}"
echo "[INFO] LD_LIBRARY_PATH  = ${LD_LIBRARY_PATH}"

# ====== 5) venv を有効化（numpy/scipy/trimesh/vtk など） ======
# venv の場所がプロジェクト直下 venv/ の想定
if [ ! -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
  echo "[ERROR] venv not found: ${PROJECT_ROOT}/venv/bin/activate" >&2
  exit 1
fi

source "${PROJECT_ROOT}/venv/bin/activate"

echo "[INFO] venv python=$(which python)"
python --version

# ====== 6) Sanity check（最小） ======
python - << 'EOF'
import sys, os
print("[PY] sys.executable =", sys.executable)
print("[PY] sys.path[0:5]  =", sys.path[0:5])
print("[PY] PYTHONPATH     =", os.environ.get("PYTHONPATH",""))
print("[PY] LD_LIBRARY_PATH=", os.environ.get("LD_LIBRARY_PATH",""))

import gmsh
print("[PY] gmsh version   =", getattr(gmsh, "__version__", "unknown"))
gmsh.initialize()
gmsh.finalize()
print("[PY] gmsh init/finalize OK")
EOF

# ====== 7) 実行する CSV を指定 ======
# デフォルトは batch/batch_cases.csv
CSV_PATH="${PROJECT_ROOT}/batch/batch_cases.csv"

# 別CSVを使いたい場合は、qsub 時に環境変数で上書きできるようにしておく
# 例: pjsub --export CSV_PATH=/path/to/other.csv jobs/fugaku/run_batch.sh
CSV_PATH="${CSV_PATH_OVERRIDE:-${CSV_PATH}}"

if [ ! -f "${CSV_PATH}" ]; then
  echo "[ERROR] CSV not found: ${CSV_PATH}" >&2
  exit 1
fi

echo "[INFO] CSV_PATH = ${CSV_PATH}"

# ====== 8) 実行ログの置き場所（任意） ======
# PJM の stdout/stderr とは別に、runs/run_batch_*.log にも残したい場合
RUNLOG_DIR="${PROJECT_ROOT}/runs"
mkdir -p "${RUNLOG_DIR}"
RUNLOG="${RUNLOG_DIR}/run_batch_$(date +%Y%m%d_%H%M%S).log"

echo "[INFO] RUNLOG = ${RUNLOG}"
echo "[INFO] ===== batch start =====" | tee -a "${RUNLOG}"

# ====== 9) batch 実行 ======
# batch/batch.py は修正版（SRC_DIR を sys.path に追加する版）を想定
python "${PROJECT_ROOT}/batch/batch.py" "${CSV_PATH}" 2>&1 | tee -a "${RUNLOG}"

echo "[INFO] ===== batch end =====" | tee -a "${RUNLOG}"
echo "[INFO] job end: $(date)"
