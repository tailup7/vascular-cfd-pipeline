# 中心線の各点における接線ベクトルに対して移動平均をかける
MOVING_AVERAGE    = True

# 変形後の表面メッシュに対してEdge Swapを行う
EDGESWAP          = True

# 変形後の表面メッシュに対して vtkWindowedSincPolyDataFilter をかける
SMOOTHER_VTK      = True

# 変形量計算に用いる目標中心線を、基準中心線に対して位置合わせする
ALIGNMENT         = True

# 変形後メッシュのプリズム層数や初層厚さ、成長率、テトラメッシュの粗さを基準メッシュのものから変えたいときは、
# USE_MESHING_CONFIG = False にして、以下のパラメータを自由に設定する
USE_MESHING_CONFIG = True
if not USE_MESHING_CONFIG : 
    RADIAL_RESOLUTION_FACTOR = 0.35
    FIRST_LAYER_RATIO        = 0.015
    GROWTH_RATE              = 1.2
    NUM_OF_LAYERS            = 6
