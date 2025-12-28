import vtk

def vtkWindowedSincPolyDataFilter(surfacenodes_moved, surfacetriangles_moved):
    print("start vtkWindowedSincPolyDataFilter")
    # 1) NodeMoved → vtkPoints
    points = vtk.vtkPoints()
    nodeid_to_vtkid = {}    # NodeMoved.id → vtk の point id
    nodes_in_order = []     # index -> NodeMoved のリスト（後で使いやすくする用）

    for node_obj in surfacenodes_moved:
        pid = points.InsertNextPoint(node_obj.x, node_obj.y, node_obj.z) # pidは 0スタート。.InsertNextPoint() をするたびに自動で左辺は+1される。
        nodeid_to_vtkid[node_obj.id] = pid
        nodes_in_order.append(node_obj)

    # 2) Triangle → vtkCellArray
    polys = vtk.vtkCellArray()
    for tri in surfacetriangles_moved:
        vtk_tri = vtk.vtkTriangle()
        vtk_tri.GetPointIds().SetId(0, nodeid_to_vtkid[tri.node0.id])    #頂点0は、vtk内でのnodeID -- の nodeである、と設定する
        vtk_tri.GetPointIds().SetId(1, nodeid_to_vtkid[tri.node1.id])
        vtk_tri.GetPointIds().SetId(2, nodeid_to_vtkid[tri.node2.id])
        polys.InsertNextCell(vtk_tri)  # セル配列に三角形を追加

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(polys)

    # 3) WindowedSincPolyDataFilter でスムージング
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputData(polydata)
    smoother.SetNumberOfIterations(20)      # 好きなパラメータに調整
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetPassBand(0.1)
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOn()
    smoother.Update()

    smoothed = smoother.GetOutput()
    smoothed_points = smoothed.GetPoints()

    # 4) スムージング後の座標を NodeMoved に書き戻す
    for node_obj in surfacenodes_moved:
        pid = nodeid_to_vtkid[node_obj.id] 
        x, y, z = smoothed_points.GetPoint(pid)   # この右辺。vtk内でのnodeIDはスムージング後も保持されており、移動前のnodeIDからnodeを参照して移動後のnodeの座標を得ることができる。
        node_obj.x = x
        node_obj.y = y
        node_obj.z = z

    # Triangle の unitnormal も更新したければここで再計算
    for tri in surfacetriangles_moved:
        tri.calc_unitnormal()

    print("end vtkWindowedSincPolyDataFilter")

    return surfacenodes_moved, surfacetriangles_moved
