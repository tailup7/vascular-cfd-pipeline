#!/bin/bash
#PJM -g hp120306
#PJM -L "node=1"
#PJM -L "rscgrp=small"
#PJM -L "elapse=02:00:00"
#PJM -x PJM_LLIO_GFSCACHE=/vol0002:/vol0004

set -euo pipefail

# ====== �����̃C���X�g�[���� ======
export PREFIX=/vol0002/mdt1/data/hp120306/u14406/local/gmsh/4.13.1
export SRCDIR=/vol0002/mdt1/data/hp120306/u14406/local/src
export BUILDDIR=$SRCDIR/gmsh/build

mkdir -p "$SRCDIR"
cd "$SRCDIR"

echo "[INFO] host=$(hostname)"
echo "[INFO] uname -m=$(uname -m)"
echo "[INFO] pwd=$(pwd)"

# ====== Spack�i�r���h�c�[�������p�j ======
. /home/u14406/spack/share/spack/setup-env.sh

# spack�ɓ����Ă���V����CMake ��load����(�x�x�Ƀf�t�H���g�œ����Ă�����̂͂��Â�)
spack load /ek66qoi
cmake --version

# Python �͂��Ȃ������i�g���Ă�����́i��FSpack python 3.11�j
# �������͊��Ɍv�Z�m�[�h�œ��� python ������Ȃ炻����g����OK
#   ��: spack load python@3.11.11 target=a64fx %fj
spack load /7heyycu
echo "[INFO] python=$(which python)"
python --version

# ====== gmsh �\�[�X�擾 ======
if [ ! -d gmsh ]; then
  git clone https://gitlab.onelab.info/gmsh/gmsh.git
fi
cd gmsh

# 4.13.1 �ɍ��킹��i�^�O���Ⴄ�ꍇ������̂Ō���\���j
git fetch --tags
echo "[INFO] available tags (filtered):"
git tag | grep -E '^gmsh_4_13|^v4\.13|4\.13' || true

# �悭����^�O���Fgmsh_4_13_1
# �������ꂪ�����Ȃ�A��� tag �o�͂���߂����̂�I��ł�������
git checkout gmsh_4_13_1 || true

# ====== �r���h ======
mkdir -p "$BUILDDIR"
cd "$BUILDDIR"

# �d�v�F
# - ENABLE_FLTK=OFF�FGUI�����i�v�Z�m�[�h�ł�GUI�g���Ȃ��̂ł��ꂪ����j
# - ENABLE_MPI=OFF�FMPI�������G���[�������i���Ȃ����܂��ɑ���������j
# - ENABLE_PYTHON=ON�FPython�o�C���f�B���O����
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DENABLE_FLTK=OFF \
  -DENABLE_MPI=OFF \
  -DENABLE_BUILD_DYNAMIC=ON \
  -DENABLE_BUILD_LIB=ON \
  -DENABLE_PYTHON=ON \
  -DPython3_EXECUTABLE="$(which python)"

make -j 8
make install

echo "[INFO] Installed to: $PREFIX"

# ====== �������m�F�igmsh.py �� libgmsh.so ��T���j ======
echo "[INFO] find gmsh.py / libgmsh.so"
find "$PREFIX" -maxdepth 5 -name "gmsh.py" -o -name "libgmsh.so*" || true

echo "[INFO] Done."
