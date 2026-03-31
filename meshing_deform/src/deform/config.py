# 中心線の各点における接線ベクトルに対して移動平均をかける
MOVING_AVERAGE    = True

# 変形後の表面メッシュに対してEdge Swapを行う
EDGESWAP          = True

# 変形後の表面メッシュに対して vtkWindowedSincPolyDataFilter をかける
SMOOTHER_VTK      = True

# 変形量計算に用いる目標中心線を、基準中心線に対して位置合わせする
ALIGNMENT         = False

# 変形後メッシュのプリズム層数や初層厚さ、成長率、テトラメッシュの粗さを基準メッシュのものから変えたいときは、
# USE_MESHING_CONFIG = False にして、以下のパラメータを自由に設定する
# テトラメッシュの大きさは (プリズム層を含めた)断面の最小直径に対して 
# ( 2 / (RADIAL_RESOLUTION_FACTOR * TETRA_SCALING) ) 個並ぶ程度の大きさになる。
USE_MESHING_CONFIG = True
if not USE_MESHING_CONFIG :
    # テトラメッシュの設定
    RADIAL_RESOLUTION_FACTOR  = 0.35
    RESCALE_BGFIELD_FOR_TETRA = True
    if RESCALE_BGFIELD_FOR_TETRA : 
        TETRA_SCALING = 0.7    
    # プリズムメッシュの設定
    FIRST_LAYER_RATIO         = 0.015
    GROWTH_RATE               = 1.2
    NUM_OF_LAYERS             = 6
