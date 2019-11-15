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