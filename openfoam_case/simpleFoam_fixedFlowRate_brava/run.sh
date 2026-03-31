#!/bin/bash
#PJM -g hp000000
#PJM -L "node=1"
#PJM -L "rscgrp=small"
#PJM -L "elapse=02:00:00"
#PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004
#PJM --mpi "proc=4,max-proc-per-node=4"

# ===== 並列数の設定: ここと上の行を変える =====
NP=4
# ============================


set -euo pipefail

echo "[INFO] job start: $(date)"
echo "[INFO] host: $(hostname)"
echo "[INFO] pwd : $(pwd)"
echo "[INFO] NP       : ${NP}"

# ======  Spack 環境 ======
. /vol0004/apps/oss/spack/share/spack/setup-env.sh

spack load openfoam@2412 arch=linux-rhel8-a64fx

RHO=1060
PATCHES="(WALL)"

# === .msh の確認 ===
mshfile=$(ls *.msh | head -n 1)
[ -z "$mshfile" ] && { echo "cannot find .msh file"; exit 1; }
echo "=== Using mesh file: $mshfile ==="

# === convert file format ===
gmshToFoam "$mshfile"


# ==== checkMesh ======
checkMesh -case . 2>&1 | tee log.checkMesh

# === スケール変換 ===
transformPoints -scale "(1e-3 1e-3 1e-3)"

# === boundary の WALL を wall 型に変更 ===
sed -i '/^[[:space:]]*WALL[[:space:]]*$/,/^[[:space:]]*}[[:space:]]*$/ s/\(type[[:space:]]*\)patch;/\1wall;/' constant/polyMesh/boundary

# === decomposeParDict のnumberOfSubdomainsの値を NP に書き換える ===
if [ -f system/decomposeParDict ]; then
    sed -i -E "s/^( *numberOfSubdomains[[:space:]]+)[0-9]+;/\1${NP};/" system/decomposeParDict
else
    cat > system/decomposeParDict <<EOF
numberOfSubdomains ${NP};
method          scotch;
distributed     no;
roots           ();
EOF
fi

# === メッシュの番号振り直し & 分割 ===
renumberMesh -overwrite || true
decomposePar -force

# === simpleFoam 並列計算 ===
mpiexec simpleFoam -parallel 

# === WSS 出力（並列）===
mpiexec simpleFoam -parallel -postProcess \
  -func "wallShearStress(patches $PATCHES; writeFields yes;)" -latestTime

# === 最新時刻だけ再構築 ===
reconstructPar -latestTime

# === Pa 変換 ===
python3 pa_convert.py --rho "$RHO" --time latest