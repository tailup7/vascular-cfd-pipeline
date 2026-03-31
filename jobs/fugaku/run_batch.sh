#!/bin/bash
# ============================================================
# Fugaku PJM job script template
#   - runs batch/batch_auto.py with venv + gmsh (source-built)
#   - project layout:
#     vascular-cfd-pipeline/
#       venv/
#       batch/batch_auto.py
#       runs/
#       jobs/fugaku/run_batch.sh   (this file)
# ============================================================

#PJM -g hp000000
#PJM -L "node=1"
#PJM -L "rscgrp=small"
#PJM -L "elapse=04:00:00"
#PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004
#PJM --mpi "proc=4,max-proc-per-node=4"

# ====== 並列数 : ここと上の行を書き換える
export NP=4

# 出力ファイル（任意）
#PJM -o run_batch_auto.%j.out
#PJM -e run_batch_auto.%j.err

set -euo pipefail

echo "[INFO] job start: $(date)"
echo "[INFO] host: $(hostname)"
echo "[INFO] pwd : $(pwd)"

# ====== 0) Spack 環境 ======
. /vol0004/apps/oss/spack/share/spack/setup-env.sh

# ====== 1) Python を用意（spack の python を使う例） ======
spack unload -a
spack load /7heyycu

echo "[INFO] base python=$(which python)"
python --version

# ====== 2) OpenFOAM を用意 ======
export FUGAKU=1
spack load openfoam@2412 arch=linux-rhel8-a64fx

# ====== 3) プロジェクトルートへ移動 ======
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "[INFO] SCRIPT_DIR   = ${SCRIPT_DIR}"
echo "[INFO] PROJECT_ROOT = ${PROJECT_ROOT}"

cd "${PROJECT_ROOT}"

# ====== 4) gmsh (source-built) の Python API / shared lib を見せる ======
export GMSH_PREFIX=/vol0002/mdt1/data/hp000000/u00000/local/gmsh/4.13.1
export PYTHONPATH="${GMSH_PREFIX}/lib64:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="${GMSH_PREFIX}/lib64:${LD_LIBRARY_PATH:-}"

echo "[INFO] GMSH_PREFIX      = ${GMSH_PREFIX}"
echo "[INFO] PYTHONPATH       = ${PYTHONPATH}"
echo "[INFO] LD_LIBRARY_PATH  = ${LD_LIBRARY_PATH}"

# ====== 5) venv を有効化 ======
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

# ====== 7) 実行ログの置き場所（任意） ======
RUNLOG_DIR="${PROJECT_ROOT}/runs"
mkdir -p "${RUNLOG_DIR}"
RUNLOG="${RUNLOG_DIR}/run_batch_auto_$(date +%Y%m%d_%H%M%S).log"

echo "[INFO] RUNLOG = ${RUNLOG}"
echo "[INFO] ===== batch_auto start =====" | tee -a "${RUNLOG}"

# ====== 8) batch_auto 実行 ======
AUTO_SCRIPT="${PROJECT_ROOT}/batch/batch_auto.py"
if [ ! -f "${AUTO_SCRIPT}" ]; then
  echo "[ERROR] script not found: ${AUTO_SCRIPT}" >&2
  exit 1
fi

# batch_auto.py は inputs/original と inputs/target を内部で参照する設計
python "${AUTO_SCRIPT}" 2>&1 | tee -a "${RUNLOG}"

echo "[INFO] ===== batch_auto end =====" | tee -a "${RUNLOG}"
echo "[INFO] job end: $(date)"