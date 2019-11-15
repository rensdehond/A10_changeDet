import pandas as pd
from pyntcloud import PyntCloud
import numpy as np
import pdal
import shapely.wkt
from numpy.lib import recfunctions as rfn

import numpy as np
import pandas as pd
import matplotlib
pd.options.mode.chained_assignment = None  # default='warn'
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from pyntcloud import PyntCloud
from sklearn.cluster import DBSCAN, KMeans

from pyntcloud.ransac.fitters import single_fit
from pyntcloud.ransac.models import RansacPlane

def get_points(ept_path, bounds, wkt):
    
    READ_PIPELINE = """
                    {{
                        "pipeline": [
                            {{
                                "type": "readers.ept",
                                "filename": "{path}",
                                "bounds": "{bounds}"
                            }},
                            {{
                                "type":"filters.crop",
                                "polygon":"{wkt}"
                            }}
                        ]
                    }}
                    """
    
    pipeline = pdal.Pipeline(READ_PIPELINE.format(
        path=ept_path,
        bounds=bounds,
        wkt=wkt)
    )

    pipeline.validate()
    pipeline.execute()
    point_cloud = pipeline.arrays[0]

    return point_cloud



def write_to_laz(point_cloud, path):
    
    WRITE_PIPELINE = """
    {{
        "pipeline": [
            {{
                "type": "writers.las",
                "filename": "{path}",
                "extra_dims": "all"
            }}
        ]
    }}
    """
    pipeline = pdal.Pipeline(
        WRITE_PIPELINE.format(path=path),
        arrays=[point_cloud]
    )
    pipeline.validate()
    pipeline.execute()

def find_plane(points):
    pointcloud = PyntCloud(points)
    pointcloud.add_scalar_field("plane_fit",
                                max_dist=0.2, 
                                max_iterations=1000, 
                                n_inliers_to_stop=None)
    
    inliers = pointcloud.points[pointcloud.points.is_plane == 1]
    outliers = pointcloud.points[pointcloud.points.is_plane == 0]
    return pointcloud
    return inliers, outliers

def find_clusters(points, eps, min_samples):
    df = points[["x", "y","z"]]
    db = DBSCAN(eps=eps, min_samples=min_samples)
    dbsc = db.fit(df)
    labels = dbsc.labels_
    core_samples = np.zeros_like(labels, dtype = bool)
    core_samples[dbsc.core_sample_indices_] = True
    points["coresample"]= core_samples
    points["cluster"] = dbsc.labels_
    return points



def kmeans_clusters(points,n_clusters = 2):
    df = points[["x", "y","z"]]
    kmean = KMeans(n_clusters=n_clusters)
    kmean_clus = kmean.fit(df)
    labels = kmean_clus.labels_
    # core_samples = np.zeros_like(labels, dtype = bool)
    # core_samples[kmean_clus.core_sample_indices_] = True
    # points["coresample"]= core_samples
    points["cluster"] = kmean_clus.labels_
    return points


def recursive_planes(pyntcloud_pts, n_planes = 2, min_pts = 100, max_dist = 0.2):
    
    pyntcloud_pts['uid'] = pyntcloud_pts.index
    ransac_points = pyntcloud_pts.copy()
    points_with_planes = None
    
    for i in range(n_planes):
        if len(pyntcloud_pts.index) < min_pts:
            print(f'found {i + 1} planes')
            break
            
        else:
            # fit a plane
            # ransac_points.add_scalar_field("plane_fit",
            #                 max_dist=0.2, 
            #                max_iterations=1000, 
            #                n_inliers_to_stop=None)
            
            xyz = PyntCloud(pd.DataFrame({
                'x':ransac_points.x,
                'y':ransac_points.y,
                'z':ransac_points.z
                   }))
            
            inliers, best_model = single_fit(xyz.points.values, 
                                             RansacPlane, 
                                             return_model=True,
                                             max_iterations=10000, 
                                             n_inliers_to_stop=None)
            best_inliers = best_model.get_projections(xyz.points.values)[0] < max_dist
            
            print(best_model.point)
            print(best_model.normal)
            

                ## TO DOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
                ## the inliers are not correctly classified, 
                ## probably because max dist is not a argument for single_fit. 
                ## figure this out! 
                # distances to plane = best_model.get_projections(xyz.points.values)

            # create frame of uid and plane
            ransacplane = pd.DataFrame({
                'uid':ransac_points.uid,  
                'plane': best_inliers.astype(np.int)
            })
            
            # Copy the non-planes
            outliers = best_model.get_projections(xyz.points.values)[0] >= max_dist
            ransacrest = ransac_points[outliers]
            print(np.unique(outliers, return_counts=True))
            
            # if oints_with_planes exists, merge the existing planes with the new found plane
            if points_with_planes is not None:
                points_with_planes = pd.merge(  points_with_planes, 
                                                ransacplane, 
                                                on='uid',
                                                how='left')
            
            # If it does not exists, merge the initial pointcloud with found ransacplane
            else:
                points_with_planes = pd.merge(  pyntcloud_pts, 
                                                ransacplane, 
                                                on='uid',
                                                how='left')
            # if there is no column with cid, create a new one and give it all the value 10
            if i == 0:
                points_with_planes['cid'] = 10
            
            # at the 
            # points_with_planes['cid'] = points_with_planes.plane.where(points_with_planes['plane'] == 1, i+1)
            points_with_planes['cid'] = np.where(points_with_planes['plane'] == 1, i+1, points_with_planes['cid'])
            points_with_planes = points_with_planes.drop(['plane'], axis=1)

            ransac_points = ransacrest.copy()
            
    return points_with_planes


