#!/bin/bash

# simpleFoam を並列実行するスクリプト

set -e

# ==== 並列数の設定 ====
: "${NP:=8}"   
echo "NP = $NP"

RHO=1060
PATCHES="(WALL)"

# 必要ならモジュールロード（環境に応じてコメント解除）
# module load openfoam
# module load openmpi
# module load python

# === .msh の確認 ===
mshfile=$(ls *.msh | head -n 1)
[ -z "$mshfile" ] && { echo "cannot find .msh file"; exit 1; }
echo "=== Using mesh file: $mshfile ==="

# === convert file format ===
gmshToFoam "$mshfile"

# === スケール変換 ===
transformPoints -scale "(1e-3 1e-3 1e-3)"

# === boundary の WALL を wall 型に変更 ===
sed -i '/^[[:space:]]*WALL[[:space:]]*$/,/^[[:space:]]*}[[:space:]]*$/ s/\(type[[:space:]]*\)patch;/\1wall;/' constant/polyMesh/boundary

# === decomposeParDict を NP に合わせる ===
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
mpirun -np "$NP" simpleFoam -parallel 2>&1 | tee log.parallel
ls -d [0-9]* 2>/dev/null || echo "No time directories created"

# === WSS 出力（並列）===
mpirun -np "$NP" simpleFoam -postProcess \
  -parallel \
  -func "wallShearStress(patches $PATCHES; writeFields yes;)" \
  -latestTime

# === 最新時刻だけ再構築 ===
reconstructPar -latestTime

# === Pa 変換 ===
python3 pa_convert.py --rho "$RHO" --time latest
