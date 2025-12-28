import commonlib.utility as utility
import commonlib.cell as cell

class PairDict:
    def __init__(self):
        self.pair_dict = {}
    def _normalize_pair(self, a, b):
        return tuple(sorted((a, b)))  
    def add_pair(self, a, b, value):
        self.pair_dict[self._normalize_pair(a, b)] = value
    def remove_pair(self, a, b):
        key = self._normalize_pair(a, b)
        if key in self.pair_dict:
            del self.pair_dict[key]
    def get_value(self, a, b):
        return self.pair_dict.get(self._normalize_pair(a, b))
    
def edgeswap(surface_triangles,surface_triangle_dict, moved_nodes_dict,edgeswap_count,edgeswap_count_pre):
    edgeswap_count_pre = edgeswap_count

    for surface_triangle in surface_triangles:
        surface_triangle.already_swaped = False

    surface_triangles_swaped = []
    pair_dict = PairDict()              
    for surface_triangle in surface_triangles:
        node0 = moved_nodes_dict[surface_triangle.node0.id]
        node1 = moved_nodes_dict[surface_triangle.node1.id]
        node2 = moved_nodes_dict[surface_triangle.node2.id]
        # node0 とnode1 に対して
        if pair_dict.get_value(node0.id, node1.id) == None:
            pair_dict.add_pair(node0.id, node1.id, surface_triangle.id)
        else:
            pair_triangle = surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)]  
            if pair_triangle.already_swaped == False and surface_triangle.already_swaped == False:
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids - {node0.id, node1.id}))
                if utility.can_P_project_to_AB(node2, node0, node1) and utility.can_P_project_to_AB(moved_nodes_dict[pair_triangle_vertexid], node0, node1):
                    this_triangle_quality  = cell.calc_cell_quality(node0, node1, node2)
                    pair_triangle_quality  = cell.calc_cell_quality(node0, node1,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node1, node2,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node0, node2,moved_nodes_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surface_triangle.node0 = node1
                        surface_triangle.node1 = node2
                        surface_triangle.node2 = moved_nodes_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)].node0 = node0
                        surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)].node1 = moved_nodes_dict[pair_triangle_vertexid]
                        surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)].node2 = node2
                        # swap後、法線ベクトルの再計算
                        surface_triangle.calc_unitnormal() 
                        surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surface_triangle.already_swaped = True
                        surface_triangle_dict[pair_dict.get_value(node0.id,node1.id)].already_swaped = True
                        edgeswap_count+=1
                        print(f"do edgeswap at triangle {surface_triangle.id}")

        # node1 とnode2 に対して 
        if pair_dict.get_value(node1.id, node2.id) == None:
            pair_dict.add_pair(node1.id, node2.id, surface_triangle.id)
        else:
            pair_triangle = surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)]  
            if pair_triangle.already_swaped == False and surface_triangle.already_swaped == False:
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids-{node1.id, node2.id}))
                if utility.can_P_project_to_AB(node0,node1,node2) and utility.can_P_project_to_AB(moved_nodes_dict[pair_triangle_vertexid],node1,node2):
                    this_triangle_quality  = cell.calc_cell_quality(node0,node1,node2) ###
                    pair_triangle_quality  = cell.calc_cell_quality(node1,node2,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node0,node1,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node0,node2,moved_nodes_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surface_triangle.node1 = moved_nodes_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)].node0 = node0
                        surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)].node1 = node1
                        surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)].node2 = moved_nodes_dict[pair_triangle_vertexid]
                        # swap後、法線ベクトルの再計算
                        surface_triangle.calc_unitnormal()
                        surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surface_triangle.already_swaped = True
                        surface_triangle_dict[pair_dict.get_value(node1.id,node2.id)].already_swaped = True
                        edgeswap_count+=1
                        print(f"do edgeswap at triangle {surface_triangle.id}")

        # node2 とnode0 に対して 
        if pair_dict.get_value(node2.id, node0.id) == None:
            pair_dict.add_pair(node2.id, node0.id, surface_triangle.id)
        else:
            pair_triangle = surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)]
            if pair_triangle.already_swaped == False and surface_triangle.already_swaped == False:  
                pair_triangle_nodeids =  {pair_triangle.node0.id, pair_triangle.node1.id, pair_triangle.node2.id}
                pair_triangle_vertexid = next(iter(pair_triangle_nodeids-{node2.id, node0.id}))
                if utility.can_P_project_to_AB(node1,node2,node0) and utility.can_P_project_to_AB(moved_nodes_dict[pair_triangle_vertexid],node2,node0):
                    this_triangle_quality  = cell.calc_cell_quality(node0,node1,node2)
                    pair_triangle_quality  = cell.calc_cell_quality(node0,node2,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle1_quality = cell.calc_cell_quality(node0,node1,moved_nodes_dict[pair_triangle_vertexid])
                    temp_triangle2_quality = cell.calc_cell_quality(node1,node2,moved_nodes_dict[pair_triangle_vertexid])
                    if ( min(this_triangle_quality, pair_triangle_quality) >= min(temp_triangle1_quality, temp_triangle2_quality) and 
                            max(this_triangle_quality, pair_triangle_quality) >= max(temp_triangle1_quality, temp_triangle2_quality) ):
                        # this_triangleの各nodeを再定義
                        surface_triangle.node2 = moved_nodes_dict[pair_triangle_vertexid]
                        # pair_triangleの各nodeを再定義
                        surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)].node0 = moved_nodes_dict[pair_triangle_vertexid]
                        surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)].node1 = node1
                        surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)].node2 = node2
                        # swap後、法線ベクトルの再計算
                        surface_triangle.calc_unitnormal()
                        surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)].calc_unitnormal()
                        # swap後、this triangleとpair triangle を swap済みにする
                        surface_triangle.already_swaped = True
                        surface_triangle_dict[pair_dict.get_value(node2.id,node0.id)].already_swaped = True
                        edgeswap_count+=1
                        print(f"do edgeswap at triangle {surface_triangle.id}")
        surface_triangles_swaped.append(surface_triangle)
    return surface_triangles_swaped, edgeswap_count, edgeswap_count_pre