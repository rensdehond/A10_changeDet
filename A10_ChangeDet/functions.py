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
from sklearn.cluster import DBSCAN

from pyntcloud.ransac.fitters import single_fit
from pyntcloud.ransac.models import RansacPlane

from scipy.spatial import cKDTree


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


def recursive_planes(pyntcloud_pts, n_planes = 2, min_pts = 100, max_dist = 0.2, max_iterations = 200):
    '''
    :TODO
    '''
    pyntcloud_pts['uid'] = pyntcloud_pts.index
    ransac_points = pyntcloud_pts.copy()
    points_with_planes = pyntcloud_pts.copy()
    best_models = {}
    
    for i in range(n_planes):
        if len(pyntcloud_pts.index) < min_pts:
            print(f'found {i} planes')
            break
            
        else:
            cid = i+1

            xyz = PyntCloud(pd.DataFrame({
                'x':ransac_points.x,
                'y':ransac_points.y,
                'z':ransac_points.z
                   }))
            
            inliers, best_model = single_fit(xyz.points.values, 
                                             RansacPlane, 
                                             return_model=True, 
                                             max_iterations=max_iterations, 
                                             n_inliers_to_stop=100000)

            best_models[cid] = best_model
            best_inliers = best_model.get_projections(xyz.points.values)[0] < max_dist
            
            # create frame of uid and plane
            ransacplane = pd.DataFrame({
                    'uid':ransac_points.uid,  # :TODO check if the right UID's are selected
                    'plane': best_inliers.astype(np.int)
                })
            
            # find the non-planes
            outliers_bools = best_model.get_projections(xyz.points.values)[0] >= max_dist
            outliers = ransac_points[outliers_bools]
            
            # merge the existing planes with the new found plane
        
            points_with_planes = pd.merge(points_with_planes, 
                                          ransacplane, 
                                          on='uid',
                                          how='left')

            if i == 0:
                points_with_planes['cid'] = 20
            
            # Give the points in the plane a cluster id. 
            points_with_planes['cid'] = np.where(points_with_planes['plane'] == 1, 
                                                 cid, 
                                                 points_with_planes['cid']
                                                )
            
            points_with_planes = points_with_planes.drop(['plane'], axis=1)

            ransac_points = outliers.copy()
            n_pnts = len(ransacplane.uid)
            print(f'clustered cluster {cid}; found {n_pnts} points')
            
    return points_with_planes, best_models

def filter_distance(reference_cloud, compared_cloud, max_dist = 0.05):
    reference_array = np.array(reference_cloud[['X', 'Y', 'Z']].tolist())
    compared_array = np.array(compared_cloud[['X', 'Y', 'Z']].tolist())

    haus_distances = hausdorff_distance(reference_array, 
                                        compared_array)
    out_array = rfn.append_fields(compared_cloud[['X','Y','Z','Red','Green','Blue']], 
                                'Distance', 
                                haus_distances)
    filtered_out_array = out_array[out_array['Distance'] < max_dist]

    return filtered_out_array

def hausdorff_distance(reference_cloud, compared_cloud):
    """

    Parameters
    ----------
    reference_cloud : (Mx3) array
        The X, Y, Z coordinates of points in the reference cloud
    compared_cloud : (Mx3) array
        The X, Y, Z coordinates of points in the compared cloud
    """
    tree = cKDTree(reference_cloud)
    distances, _ = tree.query(compared_cloud, k=1)
    return distances



def get_relevant_cids(planes):
    cids, count = np.unique(planes['cid'], return_counts=True)
    
    # last one is the 'rest' cid
    cids = cids[:-1]
    counts = count[:-1]
    
    # get the order of largest to smallest  cluster
    order = sorted(range(len(counts)), key=lambda k: counts[k])
    order.reverse()

    return [ cids[order[0]], cids[order[1]] ]


def find_z(point, normal, x, y):
    '''
    https://math.stackexchange.com/questions/28043/finding-the-z-value-on-a-plane-with-x-y-values
    
    Follows function:
        z = (r * a + s * b + t * c − r * x − s * y) / t
        
    '''
    
    z = (np.dot(normal, point) - normal[0] * x - normal[1] * y) / normal[2]

    
    return z

def find_distances_centroid(model1, model2, polygon):
    centroid = polygon.centroid
    z1 = find_z(model1.point, model1.normal, centroid.x, centroid.y)
    z2 = find_z(model2.point, model2.normal, centroid.x, centroid.y)

    distance = z2 - z1

    return distance

def calc_iterations(n_points, prob_all_inliers = 0.99):
    
    enumerator = math.log(1 - prob_all_inliers)
    divider = math.log(1 - 0)


    return iterations

def find_hausdorf_dist():
    avg_dist = 0
    std_dist = 0
    return avg_dist, std_dist