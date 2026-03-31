import sys
import numpy as np
import commonlib.utility as utility

class CenterlineNode:
    def __init__(self,id,x,y,z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

        self.center = None
        self.circleradius    = None
        self.unit_center_dir = None

    def __str__(self):
        return f"NodeAny(id={self.id}, x={self.x}, y={self.y}, z={self.z})"
    
    def calc_tangentvec(self,centerline_nodes):
        if self.id==0:
            self.tangentvec = np.array([centerline_nodes[1].x-self.x, 
                                        centerline_nodes[1].y-self.y, 
                                        centerline_nodes[1].z-self.z])/2
        elif self.id == len(centerline_nodes)-1:
            self.tangentvec = np.array([self.x-centerline_nodes[self.id-1].x, 
                                        self.y-centerline_nodes[self.id-1].y, 
                                        self.z-centerline_nodes[self.id-1].z])/2
        else:
            self.tangentvec = np.array([centerline_nodes[self.id+1].x-centerline_nodes[self.id-1].x, 
                                        centerline_nodes[self.id+1].y-centerline_nodes[self.id-1].y, 
                                        centerline_nodes[self.id+1].z-centerline_nodes[self.id-1].z])/2

    def calc_parallel_vec(self,centerline_nodes):
        self.parallel_vec  =  np.array([self.x-centerline_nodes[self.id].x,
                                        self.y-centerline_nodes[self.id].y,
                                        self.z-centerline_nodes[self.id].z])

    # a から b への回転行列 ( b = R a ) 
    def calc_rotation_matrix(self,centerline_nodes): # 引数はもう一方の中心線
        a=centerline_nodes[self.id].tangentvec
        b=self.tangentvec
        R = utility.rotation_matrix_from_A_to_B(a,b)
        self.rotation_matrix = R

    def calc_curvature(self, centerline_nodes):
        self.curvature_sin = None
        self.curvature     = None
        if self.id != 0 and self.id != len(centerline_nodes)-1:
            tangentvector1 = utility.vec(centerline_nodes[self.id+1]) - utility.vec(self)
            unit_tangentvector1 = tangentvector1/np.linalg.norm(tangentvector1) 
            tangentvector2 = utility.vec(self) - utility.vec(centerline_nodes[self.id-1])
            unit_tangentvector2 = tangentvector2/np.linalg.norm(tangentvector2)
            cross_norm = np.linalg.norm(np.cross(unit_tangentvector1,unit_tangentvector2))
            self.curvature_sin = cross_norm # = sin(theta)
            dot = float(np.dot(unit_tangentvector1, unit_tangentvector2))
            theta = np.arctan2(cross_norm, dot)
            L = np.linalg.norm(tangentvector1) # 点間距離
            self.curvature = theta / L

    def calc_circumcircle(self, prev_node, next_node, eps=1e-12):
        """
        prev_node, self, next_node の3点を通る円の中心と半径を計算し、
        self.center, self.radius に格納する。
        共線に近い場合:
        self.center = None
        self.circleradius = np.inf
        """
        p1 = utility.vec(prev_node)
        p2 = utility.vec(self)
        p3 = utility.vec(next_node)

        a = p2 - p1
        b = p3 - p1
        axb = np.cross(a, b)
        denom = 2.0 * np.dot(axb, axb)  # 2*|a×b|^2
        if denom < eps:
            # 3点が共線（またはほぼ共線）
            self.center = None
            self.radius = np.inf
            return
        a2 = np.dot(a, a)
        b2 = np.dot(b, b)
        term1 = np.cross(b, axb) * a2
        term2 = np.cross(axb, a) * b2
        u = (term1 + term2) / denom
        self.center = p1 + u
        self.circleradius    = float(np.linalg.norm(self.center - p1))
        d = self.center - p2
        nd = np.linalg.norm(d)
        if nd < eps:
            self.unit_center_dir = None
        else:
            self.unit_center_dir = d / nd 

class NodeAny:
    def __init__(self,id,x,y,z):
        self.id = id
        self.x  = x
        self.y  = y
        self.z  = z
        self.closest_centerlinenode_id           = None
        self.closest_centerlinenode_distance     = None
        self.projectable_centerlineedge_id       = None
        self.projectable_H_vec                   = None
        self.projectable_centerlineedge_distance = None
        self.edgeradius      = None
        self.scalar_forbgm   = None
        self.scalar_forlayer = None
        self.sumcountor      = 1 
        self.on_inlet_boundaryedge  = False
        self.on_outlet_boundaryedge = False
        self.right_node_id          = None
        self.correspond_centerlinenodes = []

    def __str__(self):
        return f"NodeAny(id={self.id}, x={self.x}, y={self.y}, z={self.z})"
    
    def find_closest_centerlinenode(self,centerline_nodes):
        min_distance_square = float("inf")
        for node_centerline in centerline_nodes:
            distance_square = (self.x-node_centerline.x)**2 + (self.y-node_centerline.y)**2 + (self.z-node_centerline.z)**2
            if distance_square < min_distance_square:
                min_distance_square = distance_square
                self.closest_centerlinenode_id = node_centerline.id
                self.closest_centerlinenode_distance = np.sqrt(min_distance_square)

    # projectable_centerlineedge の総数は 中心線 node - 1
    def find_projectable_centerlineedge(self,centerline_nodes):
        ccid = self.closest_centerlinenode_id
        if ccid==0:
            if utility.can_P_project_to_AB(self,centerline_nodes[0],centerline_nodes[1]) == True:
                self.projectable_centerlineedge_id = 0
                self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, centerline_nodes[0], centerline_nodes[1])
                self.projectable_H_vec = utility.calculate_H(self, centerline_nodes[0], centerline_nodes[1])
        elif ccid == len(centerline_nodes)-1:
            if utility.can_P_project_to_AB(self,centerline_nodes[-2],centerline_nodes[-1]) == True:
                self.projectable_centerlineedge_id = centerline_nodes[-2].id
                self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, centerline_nodes[-2], centerline_nodes[-1])
                self.projectable_H_vec = utility.calculate_H(self, centerline_nodes[-2], centerline_nodes[-1])
        else:
            distance_temp = float("inf")
            if utility.can_P_project_to_AB(self,centerline_nodes[ccid-1],centerline_nodes[ccid]) == True:
                distance_temp = utility.calculate_PH_length(self, centerline_nodes[ccid-1], centerline_nodes[ccid])
                self.projectable_H_vec = utility.calculate_H(self, centerline_nodes[ccid-1], centerline_nodes[ccid])
                self.projectable_centerlineedge_id = ccid-1
                self.projectable_centerlineedge_distance = distance_temp
            if utility.can_P_project_to_AB(self,centerline_nodes[ccid],centerline_nodes[ccid+1]) == True:
                if utility.calculate_PH_length(self, centerline_nodes[ccid], centerline_nodes[ccid+1]) < distance_temp:
                    self.projectable_H_vec = utility.calculate_H(self, centerline_nodes[ccid], centerline_nodes[ccid+1])
                    self.projectable_centerlineedge_id = ccid
                    self.projectable_centerlineedge_distance = utility.calculate_PH_length(self, centerline_nodes[ccid], centerline_nodes[ccid+1])

    # radius_list  の総数は、centerlinenodeの数 + 1
    def set_edgeradius(self,radius_list,config):
        if self.projectable_centerlineedge_id != None:
            self.edgeradius = radius_list[self.projectable_centerlineedge_id+1]
        else:
            if self.closest_centerlinenode_id   == 0:
                self.edgeradius=(radius_list[0]+radius_list[1])/2    
            elif self.closest_centerlinenode_id == len(radius_list)-2: # 一番最後の中心線node
                self.edgeradius=(radius_list[-1]+radius_list[-2])/2  
            else:
                self.edgeradius=(radius_list[self.closest_centerlinenode_id]+radius_list[self.closest_centerlinenode_id+1])/2   
        self.scalar_forbgm = self.edgeradius*config.RADIAL_RESOLUTION_FACTOR
        self.scalar_forlayer = self.edgeradius*2 # 断面の最小直径

class NodeMoved(NodeAny):
    def execute_deform_radius_true_circle(self,radius_list_target,centerline_nodes):
        if self.projectable_centerlineedge_id != None:
            radius_direction_vec = utility.vec(self)-self.projectable_H_vec
            radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
            coef = radius_list_target[self.projectable_centerlineedge_id+1] - self.projectable_centerlineedge_distance
            deform_vector = coef*radius_direction_unitvec
            self.x += deform_vector[0]
            self.y += deform_vector[1]
            self.z += deform_vector[2]
        else:
            if self.closest_centerlinenode_id==0:
                radius_direction_vec = utility.vec(self)-utility.calculate_H(self,centerline_nodes[0],centerline_nodes[1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[0] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            elif self.closest_centerlinenode_id==len(centerline_nodes)-1:
                radius_direction_vec = utility.vec(self)-utility.calculate_H(self,centerline_nodes[-2],centerline_nodes[-1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[-1] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            else:
                radius_direction_vec = utility.vec(self) - utility.vec(centerline_nodes[self.closest_centerlinenode_id])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = (radius_list_target[self.closest_centerlinenode_id] + radius_list_target[self.closest_centerlinenode_id+1])/2 - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]

    def execute_deform_radius_expansion(self, distance_from_original_centerline, expansion_list, centerline_nodes):
        if self.projectable_centerlineedge_id != None:
            initial_point = self.projectable_H_vec
            radius_direction_vec = utility.vec(self)-self.projectable_H_vec
            radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
            deformed_point = initial_point + distance_from_original_centerline * expansion_list[self.projectable_centerlineedge_id+1] * radius_direction_unitvec
        else:
            if self.closest_centerlinenode_id==0:
                initial_point = utility.calculate_H(self,centerline_nodes[0],centerline_nodes[1])
                radius_direction_vec = utility.vec(self)-utility.calculate_H(self,centerline_nodes[0],centerline_nodes[1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                deformed_point = initial_point + distance_from_original_centerline * expansion_list[0] * radius_direction_unitvec
            elif self.closest_centerlinenode_id==len(centerline_nodes)-1:
                initial_point = utility.calculate_H(self,centerline_nodes[-2],centerline_nodes[-1])
                radius_direction_vec = utility.vec(self)-utility.calculate_H(self,centerline_nodes[-2],centerline_nodes[-1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                deformed_point = initial_point + distance_from_original_centerline * expansion_list[-1] * radius_direction_unitvec
            else:
                initial_point = utility.vec(centerline_nodes[self.closest_centerlinenode_id])
                radius_direction_vec = utility.vec(self) - utility.vec(centerline_nodes[self.closest_centerlinenode_id])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                deformed_point = initial_point + distance_from_original_centerline * ((expansion_list[self.closest_centerlinenode_id]+expansion_list[self.closest_centerlinenode_id+1])/2) * radius_direction_unitvec
        self.x = deformed_point[0]
        self.y = deformed_point[1]
        self.z = deformed_point[2]



# gmsh.model.mesh.getNodes() の1つめの返り値は、得られた全Nodeのid のリスト。
# 2つめの返り値は、得られる全Nodeのx,y,z座標成分をまとめたリスト。これらをnodeごとの情報に整理する
def coords_to_nodes(nodeids, coords):
    if len(coords)%3!=0:
        print("mylib_info   : coords_to_nodes error.")
        sys.exit()
    else:
        nodes_any=[]
        for i in range(len(nodeids)):
            x = coords[3*i]
            y = coords[3*i+1]
            z = coords[3*i+2]
            id = nodeids[i]
            node_any = NodeAny(id,x,y,z)
            nodes_any.append(node_any)
    return nodes_any