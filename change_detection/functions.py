from scipy.spatial import cKDTree
from pyntcloud.ransac.models import RansacPlane
from pyntcloud.ransac.fitters import single_fit
from sklearn.cluster import DBSCAN
import warnings
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
warnings.simplefilter(action='ignore', category=FutureWarning)


def get_points(ept_path, bounds, wkt):
    '''
    Returns points within an polygon (wkt) from an ept file.

    in:
        ept-path [string]: 
            the ept.json file

        wkt [string]: 
            representing the polygon

        bounds [xmin, xmax, ymin, ymax]:  
            boundarys containing the polygon

    out:
        point_cloud [structured array]: 
            column names are the attributes of the pointcloud

    '''

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

    pipeline = pdal.Pipeline(READ_PIPELINE.format(path=ept_path,
                                                  bounds=bounds,
                                                  wkt=wkt)
                             )

    pipeline.validate()
    pipeline.execute()
    point_cloud = pipeline.arrays[0]

    return point_cloud


def write_to_laz(point_cloud, path):
    '''
    writes a structured array to a .laz file
    in:
        point_cloud [structured np array]:
            The output pointcloud; needs attributes x, y and z. 
            When createing a pointcloud from scratch, pay attention to 
            the data types of the specific attributes, this is a pain in the ass.
            Easier to add one new collumn to an existing (filtered) pointcloud.

        path [string]:
            Path to a laz file.

    out:
        None

    '''
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


def recursive_planes(pyntcloud_pts, n_planes=2, min_pts=100, max_dist=0.2, max_iterations=200):
    '''
    in: 
        pyntcloud_pts [pd.DataFrame]:, 
            A pandas DataFrame with an arbitrary amount
            of attributes. X, Y and Z are manditory 

        n_planes [int]:
            The number of planes that have to be identified.

        min_pts [int]:
            The minimum ammount of points that should be in a plane.
            If less points remain, function stops.

        max_dist [float]:
            After each iteration points that lie within this distance to the plane
            are excluded from the pointcloud in the next iteration.

        max_iterations [int]: 
            Maximum number of ransac iterations. 

    out: 
        points_with_planes [pd.DataFrame]:
            DataFrame of the pointcloud containing all the input attributes,
            with added 'cid'. Cid stands for cluster ID and contains a unique id
            for each plane.

        best_models [dictionary]:
            A dictionary with Pyntcloud.model instances for each plane.
            Most importantly this model has a point and an normal that describes
            the plane.
                best_models[cid].point
                best_models[cid].plane

    '''
    pyntcloud_pts['uid'] = pyntcloud_pts.index
    ransac_points = pyntcloud_pts.copy()
    points_with_planes = pyntcloud_pts.copy()
    best_models = {}

    for i in range(n_planes):
        if len(ransac_points.index) < min_pts:
            print(f'found {i} planes, resulting {pyntcloud_pts.index} points')
            break

        else:
            cid = i+1

            xyz = PyntCloud(pd.DataFrame({
                'x': ransac_points.x,
                'y': ransac_points.y,
                'z': ransac_points.z
            }))

            inliers, best_model = single_fit(xyz.points.values,
                                             RansacPlane,
                                             return_model=True,
                                             max_iterations=max_iterations,
                                             n_inliers_to_stop=100000)

            best_models[cid] = best_model
            best_inliers = best_model.get_projections(
                xyz.points.values)[0] < max_dist

            # create frame of uid and plane
            ransacplane = pd.DataFrame({
                'uid': ransac_points.uid,  # :TODO check if the right UID's are selected
                'plane': best_inliers.astype(np.int)
            })

            # find the non-planes
            outliers_bools = best_model.get_projections(xyz.points.values)[
                0] >= max_dist
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


def filter_distance(reference_cloud, compared_cloud, max_dist=0.05):
    '''
    Calculates the closest hausdorff distance to each point of the reference cloud
    to the compared cloud. If this distance is larger than max_dist, the point is not returned
    in the output point cloud. 

    in: 
        reference_cloud [structured np.array]:
            Input pointcloud, must contain attributes X, Y and Z. Optionally more

        compared_cloud [structured np.array]:
            Input pointcloud, must contain attributes X, Y and Z. Optionally more

        max_dist [float]:
            If a point in the compared cloud has closest point in the reference cloud
            that is further away than <max_dist>; the point is not returned in the output.
            It is "filtered out"

    out:
        filtered_out_array [structured np.array]:
            A copy of compared_cloud excluding the points that have a closest point in referenced
            cloud further away than max_dist.

    '''
    reference_array = np.array(reference_cloud[['X', 'Y', 'Z']].tolist())
    compared_array = np.array(compared_cloud[['X', 'Y', 'Z']].tolist())

    haus_distances = hausdorff_distance(reference_array,
                                        compared_array)
    out_array = rfn.append_fields(compared_cloud[['X', 'Y', 'Z', 'Red', 'Green', 'Blue']],
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
    '''
    Returns 2 cluster ids in the order of the heighest (so top part) first.

    in:
        planes [pd.DataFrame]: 
            must contain cid and z columns.

    out: 
        [ cid1 [int], cid2 [int] ]:
            list with two cluster ids, the first if of the top plane and the
            second of the bottem plane
    '''

    cids, counts = np.unique(planes['cid'], return_counts=True)

    # last one is the 'rest' cid
    if len(cids) > 2:
        cids = cids[:-1]
        counts = counts[:-1]

    # get the order of largest to smallest  cluster
    order = sorted(range(len(counts)), key=lambda k: counts[k])

    cids = [cids[order[0]], cids[order[1]]]

    z1 = np.mean(planes[planes.cid == cids[order[0]]]['z'])
    z2 = np.mean(planes[planes.cid == cids[order[1]]]['z'])

    if z2 > z1:
        order.reverse()

    return [cids[order[0]], cids[order[1]]]


def find_z(point, normal, x, y):
    '''
    Calculates the Z on a plane given the X and Y coordinates

    Follows function:
        z = (r * a + s * b + t * c − r * x − s * y) / t
    https://math.stackexchange.com/questions/28043/finding-the-z-value-on-a-plane-with-x-y-values

    in: 
        point [x [float], y [float],z [float]]:
            an arbitrary point on a plane

        normal [a, b, c]:
            the directional vector of the plane
            Together with the point, a plane can be constructed.

        x [float]:
            the x coordinate of where the z value has to be calculated

        y [float]:
            the y coordinate of where the z value has to be calculated

    out:
        z [float]:
            The calculated Z value on the plane.
    '''

    z = (np.dot(normal, point) - normal[0] * x - normal[1] * y) / normal[2]

    return z


def find_distances_centroid(model1, model2, polygon):
    '''
    Calculates the distance between two planes on the centroid of a polygon.
    The models both describe a plane. 
     
    in:
        model1 [Pyntcloud.Model]:
            Model with a point and a normal describing a plane

        model2 [Pyntcloud.Model]:
            Model with a point and a normal describing a plane

        polygon [shapely.geometries.polygon]:
            A shapely geometry describing a polygon.
    
    out:
        distance [float]: 
            The distance between the two planes on the centroid of the
            given polygon
    
    '''

    centroid = polygon.centroid
    z1 = find_z(model1.point, model1.normal, centroid.x, centroid.y)
    z2 = find_z(model2.point, model2.normal, centroid.x, centroid.y)

    distance = z2 - z1

    return distance


def find_distances_pcs(planes, relevant_ids, fraction=0.05):
    '''
    Calculates the distance between two z values in pointclouds. 
    On the top plane, the z value is the z where .5 * fraction
     of the points lies above. 
    On the bottom plane, the z value is the z where .5 * fraction 
    of the points lies below.

    in:
        planes [pd.DataFrame]:
            A DataFrame that contains at least a cid column and a z column. 
            The relevant_ids have to correspond to the cid's in the cid column.
        
        relevant_ids [list]:
            A list of 2 integer values sorted descending on elevation. 
        
        fraction [float]:
            A float value between 0 and 1, that specifies the top and bottom
            fraction of points where the distance will be calculated.
    
    out:
        distance [float]:
            Distance between the two pointclouds
    '''


    percentage = .5 * (fraction * 100)
    top = relevant_ids[0]
    bottom = relevant_ids[1]

    top_z = np.percentile(planes[planes.cid == top]['z'], 100 - percentage)
    bottom_z = np.percentile(planes[planes.cid == bottom]['z'], percentage)

    distance = top_z - bottom_z

    return distance


def calc_iterations(n_points, prob_all_inliers=0.99):
    '''
    work in progress
    '''
    enumerator = math.log(1 - prob_all_inliers)
    divider = math.log(1 - 0)

    return iterations


def prepare_sql_string(values_list):
    '''
    prepares a string from a list containing np.ndarrays, that is ready to
    be inserted into a sql statement

    in:
        values_list [list]:
            list containg np.ndarrays.
    
    out:
        values [string]:
            A string that is ready to be insterted in sql statments. 
            has format "'single_value', 'single_value', '{elements, of, ndarray}'"
    '''
    new_values_list = []

    for i, value in enumerate(values_list):
        if type(value) == np.ndarray:

            string_value = "'{%s, %s, %s}'" % tuple(value)
            new_values_list += [string_value]
        else:
            new_values_list += [value]
    sql_string = ', '.join(str(value) for value in new_values_list)

    return sql_string
