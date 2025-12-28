#!/bin/bash
#PJM -g hp120306
#PJM -L "node=1"
#PJM -L "rscgrp=small"
#PJM -L "elapse=00:30:00"
#PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004

set -euo pipefail

. /home/u14406/spack/share/spack/setup-env.sh

# Python�i��F3.11�j
spack load /7heyycu
echo "[INFO] python=$(which python)"
python --version

# ====== ���Ȃ����r���h���� gmsh �̏ꏊ ======
export GMSH_PREFIX=/vol0002/mdt1/data/hp120306/u14406/local/gmsh/4.13.1

# gmsh.py ��������
# ���r���h���ʂ� gmsh.py ���ʂ̏ꏊ�ɂ���΁A�����ɍ��킹�ďC��
export PYTHONPATH="$GMSH_PREFIX/lib64:${PYTHONPATH:-}"

# libgmsh.so ��������
export LD_LIBRARY_PATH="$GMSH_PREFIX/lib64:${LD_LIBRARY_PATH:-}"

# �m�F
python - << 'EOF'
import sys
print("sys.path[0:5]=", sys.path[0:5])
import gmsh
print("gmsh imported:", gmsh.__version__)
gmsh.initialize()
gmsh.finalize()
print("gmsh initialize/finalize OK")
EOF

