import commonlib.utility as utility
import numpy as np
import sys

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
        identity_matrix=np.array([[1,0,0],[0,1,0],[0,0,1]])
        a=centerline_nodes[self.id].tangentvec
        b=self.tangentvec
        R = utility.rotation_matrix_from_A_to_B(a,b)
        #cross_product = np.cross(a,b)
        #norm = np.linalg.norm(cross_product)
        #if norm!=0:
        #    unit_crossvec = cross_product/norm
        #else:
        #    unit_crossvec = cross_product
#
        #crx = float(unit_crossvec[0])
        #cry = float(unit_crossvec[1])
        #crz = float(unit_crossvec[2])
#
        #matrix1=np.array([[0, -crz, cry], [crz, 0, -crx], [-cry, crx, 0]])
        #matrix2=np.array([[crx**2, crx*cry, crx*crz],[crx*cry, cry**2, cry*crz], [crx*crz, cry*crz, crz**2]])
#
        #cos_theta = np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))
        #cos_theta = np.clip(cos_theta, -1.0, 1.0) # 丸め誤差で-1~1に収まらない場合を防ぐ
        #theta = np.arccos(cos_theta)

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
                self.edgeradius=(radius_list[0]+radius_list[1])/2    # なんで足して2でわる？
            elif self.closest_centerlinenode_id == len(radius_list)-2: # 一番最後の中心線node
                self.edgeradius=(radius_list[-1]+radius_list[-2])/2  # なんで足して2でわる？
            else:
                self.edgeradius=(radius_list[self.closest_centerlinenode_id]+radius_list[self.closest_centerlinenode_id+1])/2   # なんで足して2で割る?
        self.scalar_forbgm = self.edgeradius*config.SCALING_FACTOR
        self.scalar_forlayer = self.edgeradius*2

class NodeMoved(NodeAny):
    def execute_deform_radius(self,radius_list_target,centerline_nodes):
        if self.projectable_centerlineedge_id != None:
            radius_direction_vec = utility.vector(self)-self.projectable_H_vec
            radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
            coef = radius_list_target[self.projectable_centerlineedge_id+1] - self.projectable_centerlineedge_distance
            deform_vector = coef*radius_direction_unitvec
            self.x += deform_vector[0]
            self.y += deform_vector[1]
            self.z += deform_vector[2]
        else:
            if self.closest_centerlinenode_id==0:
                radius_direction_vec = utility.vector(self)-utility.calculate_H(self,centerline_nodes[0],centerline_nodes[1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[0] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            elif self.closest_centerlinenode_id==len(centerline_nodes)-1:
                radius_direction_vec = utility.vector(self)-utility.calculate_H(self,centerline_nodes[-2],centerline_nodes[-1])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = radius_list_target[-1] - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]
            else:
                radius_direction_vec = utility.vector(self) - utility.vector(centerline_nodes[self.closest_centerlinenode_id])
                radius_direction_unitvec = radius_direction_vec/np.linalg.norm(radius_direction_vec)
                coef = (radius_list_target[self.closest_centerlinenode_id] + radius_list_target[self.closest_centerlinenode_id+1])/2 - np.linalg.norm(radius_direction_vec)
                deform_vector = coef*radius_direction_unitvec
                self.x += deform_vector[0]
                self.y += deform_vector[1]
                self.z += deform_vector[2]

class NodeForHausdorff(NodeAny):
    def __init__(self,id,x,y,z):
        super().__init__(id,x,y,z)
        self.closest_surface_node_id=None
        self.related_triangle_ids=[]

    def append(self,id):
        self.related_triangle_ids.append(id)

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