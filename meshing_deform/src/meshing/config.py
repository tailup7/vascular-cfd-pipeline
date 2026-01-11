# ================ RADIAL_RESOLUTION_FACTOR ===================
# 表面三角形メッシュ及び内部テトラメッシュを生成する際のメッシュサイズ
# 中心線に対する垂直断面において、最小直径の方向にテトラが ( 2 / RADIAL_RESOLUTION_FACTOR ) 個並ぶ程度の大きさになる
RADIAL_RESOLUTION_FACTOR    = 0.1

# ================    FIRST_LAYER_RATIO     ===================
# プリズム1層目(一番外側)の厚さ(直径比)
FIRST_LAYER_RATIO           = 0.01

# ================    GROWTH_RATE           ===================
# 外側から内側へ向かって見た時の、プリズム層の厚さの成長率。n層目の厚さ = GROWTH_RATE * (n-1)層目の厚さ
GROWTH_RATE                 = 1.3

# ================    NUM_OF_LAYERS         ===================
# プリズム層の層数
NUM_OF_LAYERS               = 6