#!/bin/bash
# 使用している計算機クラスタが古すぎて、OpenFOAMのバージョンも古い(OpenFOAM-v1612+)
# そのため計算後に P及びWSSに rhoを掛ける処理がまわりくどくなっている
set -e  # エラーが出たら中断

# === .mshファイル名を取得 ===
mshfile=$(ls *.msh | head -n 1)

if [ -z "$mshfile" ]; then
    echo "cannot find .msh file"
    exit 1
fi

echo "=== Using mesh file: $mshfile ==="

RHO=1060          # kg/m^3（血液密度）
PATCHES="(WALL)"

# Gmsh形式メッシュをOpenFOAM形式に変換
gmshToFoam "$mshfile"

# gmshは単位が無く、mmスケールでメッシュ生成していたため、mスケールに直す。(不要ならコメントアウトしてください)
transformPoints -scale "(1e-3 1e-3 1e-3)"

# checkMesh が OK でなければ 中断。
checkMesh | tee checkMesh.log
if ! grep -q "Mesh OK" checkMesh.log; then
    echo "Mesh check failed. See checkMesh.log"
    exit 1
fi

# constant/polyMesh/boundary ファイル内の "WALL" の "type" を "patch"から "wall" に変更
# これしないとWSSが計算されない。
sed -i '/^[[:space:]]*WALL[[:space:]]*$/,/^[[:space:]]*}[[:space:]]*$/ s/\(type[[:space:]]*\)patch;/\1wall;/' constant/polyMesh/boundary

# # simpleソルバ実行。ログをコンソールに流しながらファイルとしても出力する
simpleFoam | tee log

# OpenFOAM は p を p/ρ で計算している (両辺をρで割ったNS式) ので、計算終了後に ρ をかけて正しい圧力値にする
# (wallShearStressの部分は計算していなければコメントアウトしてください)
simpleFoam -postProcess -func "wallShearStress(patches $PATCHES; writeFields yes;)" -latestTime

# pythonスクリプトでPa単位へ変換
python pa_convert.py --rho "$RHO" --time latest