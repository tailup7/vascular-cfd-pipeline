import commonlib.utility as utility
import commonlib.node as node
import commonlib.cell as cell
import numpy as np

def make_nthlayer_surface_node(n, surface_node_dict,surface_triangles, mesh, config):
    temp = set()
    nth_layer_surface_node_dict={}
    layernode_dict={}
    for surface_triangle in surface_triangles:
        nodes = [surface_triangle.node0, surface_triangle.node1, surface_triangle.node2]
        for onenode in nodes:
            scalingfactor = utility.calculate_nth_layer_thickratio(n, config)*onenode.scalar_forlayer
            if onenode.id in temp:
                nth_layer_surface_node_dict[onenode.id].x += scalingfactor*surface_triangle.unitnormal_in[0]
                nth_layer_surface_node_dict[onenode.id].y += scalingfactor*surface_triangle.unitnormal_in[1]
                nth_layer_surface_node_dict[onenode.id].z += scalingfactor*surface_triangle.unitnormal_in[2]
                nth_layer_surface_node_dict[onenode.id].sumcountor += 1
            else:
                x =  scalingfactor*surface_triangle.unitnormal_in[0]
                y =  scalingfactor*surface_triangle.unitnormal_in[1]
                z =  scalingfactor*surface_triangle.unitnormal_in[2]
                nth_layer_surface_node = node.NodeAny(onenode.id + mesh.num_of_surfacenodes*n, x, y, z)
                nth_layer_surface_node.closest_centerlinenode_id = onenode.closest_centerlinenode_id
                nth_layer_surface_node_dict[onenode.id] = nth_layer_surface_node
                temp.add(onenode.id)
    for i in range(1,mesh.num_of_surfacenodes+1):
        nth_layer_surface_node_dict[i].x = surface_node_dict[i].x + nth_layer_surface_node_dict[i].x/nth_layer_surface_node_dict[i].sumcountor
        nth_layer_surface_node_dict[i].y = surface_node_dict[i].y + nth_layer_surface_node_dict[i].y/nth_layer_surface_node_dict[i].sumcountor
        nth_layer_surface_node_dict[i].z = surface_node_dict[i].z + nth_layer_surface_node_dict[i].z/nth_layer_surface_node_dict[i].sumcountor
        layernode_dict[i+mesh.num_of_surfacenodes*n] = nth_layer_surface_node_dict[i]
        mesh.nodes.append(nth_layer_surface_node_dict[i])
        mesh.num_of_nodes += 1
    return mesh,layernode_dict

def make_nthlayer_quad(i,centerline_nodes, nodes_on_inletboundaryedge, nodes_on_outletboundaryedge,mesh,config):
    innerpoint_vec = np.array([centerline_nodes[5].x,centerline_nodes[5].y,centerline_nodes[5].z])
    utility.find_right_neighbors(nodes_on_inletboundaryedge, innerpoint_vec)
    for node_on_inletboundaryedge in nodes_on_inletboundaryedge:
        quad_id0=node_on_inletboundaryedge.id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id1=node_on_inletboundaryedge.right_node_id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id2=node_on_inletboundaryedge.right_node_id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad_id3=node_on_inletboundaryedge.id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_INLET.append(quad)
        mesh.num_of_elements+=1
    innerpoint_vec = np.array([centerline_nodes[-5].x,centerline_nodes[-5].y,centerline_nodes[-5].z])
    utility.find_right_neighbors(nodes_on_outletboundaryedge, innerpoint_vec)
    for node_on_outletboundaryedge in nodes_on_outletboundaryedge:
        quad_id0=node_on_outletboundaryedge.id- mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id1=node_on_outletboundaryedge.right_node_id- mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-(i-1))
        quad_id2=node_on_outletboundaryedge.right_node_id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad_id3=node_on_outletboundaryedge.id - mesh.num_of_surfacenodes*(config.NUM_OF_LAYERS-i)
        quad = cell.Quad(quad_id0,quad_id1,quad_id2,quad_id3)
        mesh.quadrangles_OUTLET.append(quad)
        mesh.num_of_elements+=1
    return mesh

# Gmshのプリズムは頂点を次の順で記述する
# 「反時計回り, かつ, 底面→上面」
#   
#         外側
#             
#      3 ー ー 5
#      | \   / |
#      |  \ /  | 
#      |   4   |
#      |   |   |
#      0---|---2
#       \  |  /
#        \ | /
#          1
#
#       形状の内部
#

def make_nthlayer_prism(n,surface_triangles,mesh):
    for surface_triangle in surface_triangles:
        prism_id0=surface_triangle.node0.id + mesh.num_of_surfacenodes*n
        prism_id1=surface_triangle.node1.id + mesh.num_of_surfacenodes*n
        prism_id2=surface_triangle.node2.id + mesh.num_of_surfacenodes*n
        prism_id3=surface_triangle.node0.id + mesh.num_of_surfacenodes*(n-1)
        prism_id4=surface_triangle.node1.id + mesh.num_of_surfacenodes*(n-1)
        prism_id5=surface_triangle.node2.id + mesh.num_of_surfacenodes*(n-1)
        nth_layer_prism = cell.Prism(prism_id0,prism_id1,prism_id2,prism_id3,prism_id4,prism_id5)
        mesh.prisms_INTERNAL.append(nth_layer_prism)
        mesh.num_of_elements+=1
    return mesh