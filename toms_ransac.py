
import numpy as np
import pandas as pd
import matplotlib
pd.options.mode.chained_assignment = None  # default='warn'
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from pyntcloud import PyntCloud
from sklearn.cluster import DBSCAN

points = np.array((x, y, z)).T
points=pd.DataFrame(points,columns=['x','y','z'])
roof = PyntCloud(points)

#find planes until none remains
global i,cid
global planes, rest
i = 0
cid = 0
planes=pd.DataFrame(columns=['x','y','z','cid'])
rest=pd.DataFrame(columns=['x','y','z'])

def find_dbscan(points):
    df = points[["x", "y","z"]]
    db = DBSCAN(eps=dbscan_distance, min_samples=dbscan_min_samples)
    dbsc = db.fit(df)
    return dbsc.labels_

def find_planes_recursively(pointcloud):
    global i,cid
    global planes
    global rest
    if len(pointcloud.points) < min_size or i > 100:
        pass
    else:
        cid = cid + 1
        
        #First throw isolated points
        pointcloud.points["cluster"] = find_dbscan(pointcloud.points)
        pointcloud.points = pointcloud.points[pointcloud.points.cluster >= 0]
        
        for name, group in pointcloud.points.groupby('cluster'): 
            i = i + 1
            pointcloud = PyntCloud(group)
            pointcloud.add_scalar_field("plane_fit",max_dist=ransac_distance, max_iterations=ransac_iterations, n_inliers_to_stop=None)
        
            ransacplane = pointcloud.points[pointcloud.points.is_plane == 1]
            ransacrest = pointcloud.points[pointcloud.points.is_plane == 0]
         
            ransacplane["dbc"] = find_dbscan(ransacplane)
        
            dbscanplane = ransacplane[ransacplane.dbc >= 0]
            dbscanrest = ransacplane[ransacplane.dbc < 0]
         
            dbscanplane["cid"]= i + dbscanplane["dbc"] #dbscan labels start at 0
            i = i + dbscanplane["dbc"].max()
            planes = pd.concat([planes,dbscanplane[['x','y','z','cid']]])
            
            cid = dbscanplane["cid"].max()

            rest = pd.concat([ransacrest[['x','y','z']],dbscanrest[['x','y','z']]])
            find_planes_recursively(PyntCloud(rest))
        
find_planes_recursively(roof)
return planes