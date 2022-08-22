import rosbag
import copy
import pandas as pd
import numpy as np
from math import cos, sin
from shapely.affinity import scale
from shapely.geometry import Point, Polygon
from math import exp

def ros2df(file): 
    '''
    @param file: filename of bag to open or a stream to read from
    @@type file: str or file
    '''  
    bag = rosbag.Bag(file)
    first_time_set = False
    cur_time = 0.0
    next_time = cur_time

    hmi_data_timestamp = []
    every_frame_data = {
      "TimeStamp": 1,
      "EgoPosStruct":{
        "TimeStamp":1,
        "Roll":0,
        "Pitch":0,
        "Yaw":0,
        "Position_x":0,
        "Position_y":0,
        "Position_z":0,
        "velocity_x":0,
        "velocity_y":0,
        "velocity_z":0,
        "gear_data":0
      },
      "ObjectsStruct":{
        "TimeStamp":1,
        "ObjectArray":[]
      },
        "LaneStruct":{
        "TimeStamp":1,
        "LaneArray":[]
      },
    }

    ObjectsStruct = {"TimeStamp":1, "ObjectArray":[]}
    LaneStruct = {"TimeStamp":1, "LaneArray":[]}
    EgoPosStruct = {"TimeStamp":0, "Position_x":0, "Position_y":0, "Position_z":0,
                    "velocity_x":0, "velocity_y":0, "velocity_z":0, "Roll":0, "Pitch":0, "Yaw":0, "gear_data":0}

    point3d = {
        "x_d" : 0.0,
        "y_d" : 0.0,
        "z_d" : 0.0
    }
    point3f = {
        "x_f" : 0.0,
        "y_f" : 0.0,
        "z_f" : 0.0
    }
    shape3f = {
        "height" : 0.0,
        "length" : 0.0,
        "width" : 0.0
    }

    data_record = {
        "LaneMarkingStruct":False,
        "LaneCenterStruct":False,
        "SpeedLimitInfoStruct":False,
        "TrafficSignStruct":False,
        "TrafficLightStruct":False,
        "IntelligentAvoidingInfoStruct":False,
        "ObstacleDistStruct":False,
        "FollowCarInfoStruct":False,
        "DecelerationStruct":False,
        "IntersectionStruct":False,
        "RoadObstacleStruct":False,
        "ego_pose":False,
        "ObjectsInfoStruct":False,
        "LaneInfoStruct":False, 
        "RoadMarkStruct":False,
        "MotionPlanningTrajStruct":False,
        "DecelerationInfoStruct": False,
        "ObsAvdanceTrckInfoStruct": False
    }

    num = 0
    cnt = 0

    flag_parking = flag_object = flag_lane = 0.0
    codeToID = {}
    id_list = []


    for topic, msg, t in bag.read_messages(["/mla/egopose","/msd/planning/plan",'/perception/fusion/object','/perception/vision/lane']):
      
        cur_time = int(str(t))

        if not first_time_set:
            before_time = cur_time-1
            next_time = before_time+100000000
            first_time_set = True
            data_element = copy.deepcopy(every_frame_data)
            data_element["TimeStamp"] = cur_time
            hmi_data_timestamp.append(data_element) 

        if cur_time > next_time :
            before_time = next_time
            next_time = before_time + 100000000
            data_element = copy.deepcopy(every_frame_data)
            data_element["TimeStamp"] = cur_time
            hmi_data_timestamp.append(data_element) 
            for j in data_record.keys():
                data_record[j] = False


        parking_slot_list = []

        if(topic == '/mla/egopose'):

            if(data_record["ego_pose"] == False):
                data_record["ego_pose"] = True
                EgoPosStruct["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
                if(msg.position.position_local.x != 0 or msg.position.position_local.y != 0 or msg.position.position_local.z != 0):
                    EgoPosStruct["Position_x"] = float(msg.position.position_local.x)
                    EgoPosStruct["Position_y"] = float(msg.position.position_local.y)
                    EgoPosStruct["Position_z"] = float(msg.position.position_local.z)                
                if(msg.orientation.euler_local.roll != 0 or msg.orientation.euler_local.yaw != 0 or msg.orientation.euler_local.pitch != 0):
                    EgoPosStruct["Roll"] = float(msg.orientation.euler_local.roll)
                    EgoPosStruct["Pitch"] = float(msg.orientation.euler_local.pitch)
                    EgoPosStruct["Yaw"] = float(msg.orientation.euler_local.yaw)
                EgoPosStruct["velocity_x"] = float(msg.velocity.velocity_local.vx)
                EgoPosStruct["velocity_y"] = float(msg.velocity.velocity_local.vy)
                EgoPosStruct["velocity_z"] = float(msg.velocity.velocity_local.vz)
	    	    
   
        if(EgoPosStruct["TimeStamp"] > 0 and cur_time - EgoPosStruct["TimeStamp"] < 300000000 ):
            hmi_data_timestamp[-1]["EgoPosStruct"]["TimeStamp"] =  EgoPosStruct["TimeStamp"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Position_x"] =  EgoPosStruct["Position_x"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Position_y"] = EgoPosStruct["Position_y"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Position_z"] =  EgoPosStruct["Position_z"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Roll"] = EgoPosStruct["Roll"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Pitch"] = EgoPosStruct["Pitch"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["Yaw"] = EgoPosStruct["Yaw"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["velocity_x"] = EgoPosStruct["velocity_x"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["velocity_y"] = EgoPosStruct["velocity_y"]
            hmi_data_timestamp[-1]["EgoPosStruct"]["velocity_z"] = EgoPosStruct["velocity_z"]


        if(topic == '/perception/fusion/object'):
            if(flag_object != hmi_data_timestamp[-1]["TimeStamp"]):
                if(data_record["ObjectsInfoStruct"] == False and (len(msg.perception_fusion_objects_data) > 0)):
                    data_record["ObjectsInfoStruct"] == True
                    ObjectsStruct["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
                    flag_object = hmi_data_timestamp[-1]["TimeStamp"]

                    ObjectsStruct["ObjectArray"] = []

                    for i in range(len(msg.perception_fusion_objects_data)):

                        object_x = msg.perception_fusion_objects_data[i].relative_position.x

                        object_y = msg.perception_fusion_objects_data[i].relative_position.y
                    

                        distance = object_x*object_x + object_y*object_y
                        

                        if True:
                            ObjectArray_info = {}
                            ObjectArray_info["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
                            ObjectArray_info["ID"] = msg.perception_fusion_objects_data[i].track_id
                            ObjectArray_info["Position_x"] = float(msg.perception_fusion_objects_data[i].relative_position.x)
                            ObjectArray_info["Position_y"] = float(msg.perception_fusion_objects_data[i].relative_position.y)
                            ObjectArray_info["Position_z"]= float(msg.perception_fusion_objects_data[i].relative_position.z)
                            ObjectArray_info["RelativeVelocity_x"] = float(msg.perception_fusion_objects_data[i].velocity_relative_to_ground.x)
                            ObjectArray_info["RelativeVelocity_y"] = float(msg.perception_fusion_objects_data[i].velocity_relative_to_ground.y)
                            ObjectArray_info["RelativeHeadingYaw"] = float(msg.perception_fusion_objects_data[i].relative_heading_yaw)
                            
                            
                            ObjectArray_info["ObjectType"] = msg.perception_fusion_objects_data[i].type_info.type.value
                            if(ObjectArray_info["ObjectType"] == 1):
                              ObjectArray_info["ObjectSubtype"] = msg.perception_fusion_objects_data[i].type_info.vehicle_sub_type.value
                            if(ObjectArray_info["ObjectType"] == 2):
                              ObjectArray_info["ObjectSubtype"] = msg.perception_fusion_objects_data[i].type_info.vru_sub_type.value
                            
                            ObjectArray_info["ObjectHeight"] = msg.perception_fusion_objects_data[i].shape.height  
                            ObjectArray_info["ObjectWidth"] = msg.perception_fusion_objects_data[i].shape.width 
                            ObjectArray_info["ObjectLenth"] = msg.perception_fusion_objects_data[i].shape.length

                            ObjectsStruct["ObjectArray"].append(ObjectArray_info)
                            


        if(ObjectsStruct["TimeStamp"] > 0 and cur_time - ObjectsStruct["TimeStamp"] <  300000000):
            hmi_data_timestamp[-1]["ObjectsStruct"]["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
            hmi_data_timestamp[-1]["ObjectsStruct"]["ObjectArray"] = ObjectsStruct["ObjectArray"]

        if(topic == "/perception/vision/lane"):

            if(flag_lane != hmi_data_timestamp[-1]["TimeStamp"]):

                if(data_record["LaneInfoStruct"] == False and (len(msg.lane_perception.lanes) > 0)):
                    data_record["LaneInfoStruct"] == True
            
                    LaneStruct["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
                    flag_lane = hmi_data_timestamp[-1]["TimeStamp"]

                    LaneStruct["LaneArray"] = []

                    for i in range(len(msg.lane_perception.lanes)):
                        lane = msg.lane_perception.lanes[i]
                        distance = -100
                        if lane.is_centerline == True or lane.is_failed_3d == True:
                            continue
                        
                        points = list(zip(lane.points_3d_y, lane.points_3d_x))
                        for x,y in points:
                            if y == 0:
                                distance = x
                                break
                  

                        if True:
                            LaneArray_info = {}
                            LaneArray_info["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
                            LaneArray_info["TrackID"] = msg.lane_perception.lanes[i].track_id
                            LaneArray_info["LaneType"] = msg.lane_perception.lanes[i].lane_type.value
                            LaneArray_info["LaneColor"] = msg.lane_perception.lanes[i].lane_color.value
                            LaneArray_info["DistanceToCar"] = float(distance)
                            
                            LaneStruct["LaneArray"].append(LaneArray_info)
                        


        if(LaneStruct["TimeStamp"] > 0 and cur_time - LaneStruct["TimeStamp"] <  300000000):
            hmi_data_timestamp[-1]["LaneStruct"]["TimeStamp"] = hmi_data_timestamp[-1]["TimeStamp"]
            hmi_data_timestamp[-1]["LaneStruct"]["LaneArray"] = LaneStruct["LaneArray"]
    
    result_object = []
    for i in range(len(hmi_data_timestamp)):
        if(len(hmi_data_timestamp[i]["ObjectsStruct"]["ObjectArray"]) > 0):
            for j in range(len(hmi_data_timestamp[i]["ObjectsStruct"]["ObjectArray"])):
                result_object.append(hmi_data_timestamp[i]["ObjectsStruct"]["ObjectArray"][j])

    result_egopose = []
    for i in range(len(hmi_data_timestamp)):
        if(len(hmi_data_timestamp[i]["EgoPosStruct"]) > 0):
            result_egopose.append(hmi_data_timestamp[i]["EgoPosStruct"])

    result_lane = []
    for i in range(len(hmi_data_timestamp)):
        if(len(hmi_data_timestamp[i]["LaneStruct"]) > 0):
            for j in range(len(hmi_data_timestamp[i]["LaneStruct"]["LaneArray"])):
                result_lane.append(hmi_data_timestamp[i]["LaneStruct"]["LaneArray"][j])  
            
    pf_object = pd.DataFrame(result_object)
    pf_egopose = pd.DataFrame(result_egopose)
    pf_lane = pd.DataFrame(result_lane)

    order_object = ["TimeStamp","ID","Position_x", "Position_y", "Position_z", "ObjectHeight","ObjectWidth","ObjectLenth","RelativeVelocity_x", "RelativeVelocity_y","RelativeHeadingYaw","ObjectType", "ObjectSubtype"]
    order_egopose = ["TimeStamp", "Position_x", "Position_y", "Position_z", "velocity_x", "velocity_y", "velocity_z", "Roll", "Pitch", "Yaw", "gear_data"]
    order_lane = ["TimeStamp", "TrackID", "LaneType", "LaneColor", "DistanceToCar"]

    pf_object = pf_object[order_object]
    pf_egopose = pf_egopose[order_egopose]

    pf_object.fillna(' ', inplace=True)
    pf_egopose.fillna(' ', inplace=True)
    pf_lane.fillna(' ', inplace=True)
    pf_indicators = pf_object[["TimeStamp","RelativeVelocity_x","RelativeVelocity_y","RelativeHeadingYaw"]].copy()

    def point_line_col(p1, l1, l2, vel): 
        line_dir = (l1 - l2)/np.linalg.norm(l1-l2)
        vel_proj = np.dot(vel, line_dir) *line_dir
        vel_hori = vel - vel_proj
        h = np.cross(l1-p1,l2-p1)/np.linalg.norm(l1-l2)
        t = abs(h / np.linalg.norm(vel_hori))
        if abs(np.cross(l1-p1,l2-p1)) <= abs(np.cross(l1-p1-0.1*vel,l2-p1-0.1*vel)):
            t = float("inf")
            return t
        p1_ = p1 + t *vel
        if np.dot((p1_ - l1),(p1_ -l2)) > 0: 
            t = float("inf")
        return t

    def crash_risk_ttc(veh_points, obj_points, vel):
        veh_l = veh_points[0]
        veh_r = veh_points[1]
        obj_lr = obj_points[0] 
        obj_lf = obj_points[1] 
        obj_rf = obj_points[2] 
        obj_rr = obj_points[3] 
        t_candidates = []
        t_candidates.append(point_line_col(veh_l, obj_lr, obj_lf,-vel))
        t_candidates.append(point_line_col(veh_l, obj_lf, obj_rf,-vel))
        t_candidates.append(point_line_col(veh_l, obj_rf, obj_rr,-vel))
        t_candidates.append(point_line_col(veh_l, obj_rr, obj_lr,-vel))
        t_candidates.append(point_line_col(veh_r, obj_lr, obj_lf,-vel))
        t_candidates.append(point_line_col(veh_r, obj_lf, obj_rf,-vel))
        t_candidates.append(point_line_col(veh_r, obj_rf, obj_rr,-vel))
        t_candidates.append(point_line_col(veh_r, obj_rr, obj_lr,-vel))
        t_candidates.append(point_line_col(obj_lr, veh_l, veh_r, vel))
        t_candidates.append(point_line_col(obj_lf, veh_l, veh_r, vel))
        t_candidates.append(point_line_col(obj_rf, veh_l, veh_r, vel))
        t_candidates.append(point_line_col(obj_rr, veh_l, veh_r, vel))
        t = min(t_candidates)
        
        
        return t

    def collision_point(veh_points, obj_points, vel):
        veh_l = veh_points[0]
        veh_r = veh_points[1]
        t = crash_risk_ttc(veh_points, obj_points, vel)
        y = veh_l[1]
        
        if t == float("inf"):
            return 2*veh_l[0] 
        
        obj_lr = obj_points[0] 
        obj_lf = obj_points[1] 
        obj_rf = obj_points[2] 
        obj_rr = obj_points[3] 
        obj_lr_c = obj_points[0] + vel * t 
        obj_lf_c = obj_points[1] + vel * t 
        obj_rf_c = obj_points[2] + vel * t 
        obj_rr_c = obj_points[3] + vel * t 
        if obj_lr_c[1] == y and obj_lf_c[1] == y:
            return ((obj_lr_c + obj_lf_c)/2)[0]
        elif obj_lf_c[1] == y and obj_rf_c[1] == y:
            return ((obj_lf_c + obj_rf_c)/2)[0]
        elif obj_rf_c[1] == y and obj_rr_c[1] == y:
            return ((obj_rf_c + obj_rr_c)/2)[0]
        elif obj_rr_c[1] == y and obj_lr_c[1] == y:
            return ((obj_rr_c + obj_lr_c)/2)[0]
        elif obj_lr_c[1] == y:
            return obj_lr_c[0]
        elif obj_lf_c[1] == y:
            return obj_lf_c[0]
        elif obj_rf_c[1] == y:
            return obj_rf_c[0]
        elif obj_rr_c[1] == y:
            return obj_rr_c[0]
        elif np.linalg.norm(obj_lr_c - veh_l)**2 + np.linalg.norm(obj_rf_c - veh_l)**2 > \
            np.linalg.norm(obj_lr_c - veh_r)**2 + np.linalg.norm(obj_rf_c - veh_r)**2:
            return veh_r[0] 
        elif np.linalg.norm(obj_lr_c - veh_l)**2 + np.linalg.norm(obj_rf_c - veh_l)**2 < \
            np.linalg.norm(obj_lr_c - veh_r)**2 + np.linalg.norm(obj_rf_c - veh_r)**2:
            return veh_l[0] 
            

    def C2C_rate(veh_points, obj_points, vel): 
        veh_l = veh_points[0]
        veh_r = veh_points[1]
        t = crash_risk_ttc(veh_points, obj_points, vel)
        
        obj_lr_c = obj_points[0] + vel * t 
        obj_lf_c = obj_points[1] + vel * t 
        obj_rf_c = obj_points[2] + vel * t 
        obj_rr_c = obj_points[3] + vel * t 
        
        if t == float("inf"):
            return -1
        
        center_obj = np.mean(obj_points, axis=0)
        center_obj_= center_obj + t * vel
        center_veh = np.array([0, 1.6])
        col_y = veh_r[1]
        col_x = collision_point(veh_points, obj_points, vel)
        col_p = np.array([col_x,col_y])
        sqr_dis_1 = np.linalg.norm(col_p- center_veh, 2)
        sqr_dis_2 = np.linalg.norm(col_p - center_obj_, 2)
        sqr_std_1 = np.linalg.norm(veh_l - center_veh, 2)
        sqr_std_2 = np.linalg.norm(obj_points[0] - center_obj, 2)
        rate = (sqr_dis_1 + sqr_dis_2) / (sqr_std_1 + sqr_std_2)
        rate = 1 - rate
        if rate < 0:
            rate = 0 
        return rate 



    def rotation(theta):
        rotation_metrix = np.array([[cos(theta), sin(theta)],
                                    [-sin(theta),cos(theta)]])
        return rotation_metrix

    def four_points_object(center_x, center_y, width, lenth, theta):
        rel_theta = -theta
        obj_lr_ = np.array([-width/2, -lenth/2])
        obj_lf_ = np.array([-width/2,lenth/2]) 
        obj_rf_ = np.array([width/2, lenth/2]) 
        obj_rr_ = np.array([width/2, -lenth/2]) 
        
        center = np.array([center_x, center_y])
        obj_lr = rotation(rel_theta)@ obj_lr_ + center
        obj_lf = rotation(rel_theta)@ obj_lf_ + center
        obj_rf = rotation(rel_theta)@ obj_rf_ + center
        obj_rr = rotation(rel_theta)@ obj_rr_ + center
        
        return [obj_lr, obj_lf, obj_rf, obj_rr]


    global A_car

    A_lane = 2
    sigma =  0.3

    delta = 0.5
    A_car = 20
    alpha = 0.5

    def lane_potential(rel_x):
        U_lane_i = A_lane * math.exp(- (rel_x)**2 / (2*(sigma**2)))
        return U_lane_i

    def create_car(p1,p2,p3,p4):
        p5 = (p1+p2)/2 + np.array([0,0.5])
        P1, P2, P3, P4, P5 = map(Point, [p1, p2, p3, p4, p5])
        car = Polygon([P1, P5, P2, P3, P4])
        return car

    def create_obs(p1,p2,p3,p4):
        P1, P2, P3, P4 = map(Point, [p1, p2, p3, p4])
        obs = Polygon([P1, P2, P3, P4])
        return obs

    def K_dis(car, obs):
        dis = car.distance(obs)
        if dis == 0:
            dis = 1
        return dis

    def U_car(car_points,obs_points):
        p11, p12, p13, p14 = car_points
        p21, p22, p23, p24 = obs_points
        car = scale(create_car(p11,p12,p13,p14), 0.08, 1, origin=(0,0))
        obs = scale(create_obs(p21,p22,p23,p24), 0.08, 1, origin=(0,0))
        K = K_dis(car.centroid, obs.centroid)
        U_car = A_car * (exp(-alpha * K))/K
        return U_car
   
    veh_r = np.array([4, 1])
    veh_l = np.array([-4,1])
    veh_r_ = np.array([4, -1])
    veh_l_ = np.array([-4,-1])

    veh1 = np.array([0.982, 4.065])
    veh2 = np.array([-0.982, 4.065])
    veh3 = np.array([-0.982, -0.865])
    veh4 = np.array([0.982, -0.865]) 

    veh_points = [veh_l, veh_r]
    veh_points_ = [veh1, veh2, veh3, veh4]

    pf_indicators["TTC"] = 0
    pf_indicators["C2CRate"] = 0
    pf_indicators["U_car"] = 0
    for i in range(pf_object.shape[0]):
        center_x = pf_object.loc[i,"Position_x"]
        center_y = pf_object.loc[i,"Position_y"]
        width = pf_object.loc[i,"ObjectWidth"]
        lenth = pf_object.loc[i,"ObjectLenth"]
        theta = pf_object.loc[i,"RelativeHeadingYaw"]
        vel = np.array([pf_object.loc[i,"RelativeVelocity_x"],
                        pf_object.loc[i,"RelativeVelocity_y"]])

        obj_points = four_points_object(center_x, center_y, width, lenth, theta)
        pf_indicators.loc[i,"TTC"] = crash_risk_ttc(veh_points, obj_points, vel)
        pf_indicators.loc[i,"C2CRate"] = C2C_rate(veh_points, obj_points, vel)
        pf_indicators.loc[i,"U_car"]= U_car(veh_points_, obj_points) 

    return pf_indicators