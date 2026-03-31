# ================ RADIAL_RESOLUTION_FACTOR ===================
# 表面三角形メッシュ及び内部テトラメッシュを生成する際のメッシュサイズ
# 中心線に対する垂直断面において、最小直径の方向にテトラが ( 2 / RADIAL_RESOLUTION_FACTOR ) 個並ぶ程度の大きさになる
RADIAL_RESOLUTION_FACTOR    = 0.175

# ================    FIRST_LAYER_RATIO     ===================
# プリズム1層目(一番外側)の厚さ(直径比)
FIRST_LAYER_RATIO           = 0.006

# ================    GROWTH_RATE           ===================
# 外側から内側へ向かって見た時の、プリズム層の厚さの成長率。n層目の厚さ = GROWTH_RATE * (n-1)層目の厚さ
GROWTH_RATE                 = 1.2

# ================    NUM_OF_LAYERS         ===================
# プリズム層の層数
NUM_OF_LAYERS               = 8

# ================    surface mesh を作った後、vtkWindowedSincPolyDataFilter で平滑化 ON/OFF ======
SMOOTHER_VTK      = True
# ================    surface mesh を作った後、EdgeSWapを行う ON/OFF ======
EDGESWAP          = True

# 内側テトラメッシュを、プリズム表面三角形パッチのスケールよりもさらに小さくしたい場合
# RESCALE_BGFIELD_FOR_TETRA = Trueにする。(1 / TETRA_SCALING) 倍だけ細かくなる
# テトラメッシュの大きさは (プリズム層を含めた)断面の最小直径に対して 
# ( 2 / (RADIAL_RESOLUTION_FACTOR * TETRA_SCALING) ) 個並ぶ程度の大きさになる。
# 表面メッシュに対して、プリズム層作成のために内側に押し出した後の表面メッシュは
# 0.7~0.8倍の大きさになっているはずなので、(プリズム層は管径の20%程度の厚さのため)
# TETRA_SCALING の値も 0.8 程度に設定することでプリズム - テトラ の接続がよくなるはず
# ================    BGFIELD_SCALING       ===================
RESCALE_BGFIELD_FOR_TETRA = True
if RESCALE_BGFIELD_FOR_TETRA : 
    TETRA_SCALING = 0.8


# 管径が変化する形状に対して、最小直管径の部分のスケールで全体のプリズム層を作るかどうかのON / OFF
# 基本的にOFFでいい。比較のためにプリズム層を一定の幅で作りたかったらTrueにする.
MAKE_BOUNDARY_CONSTANT = False
if MAKE_BOUNDARY_CONSTANT :
    RADIUS_MINIMUM = 2.75 #形状全体での最小直径