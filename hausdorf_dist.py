import numpy as np
from scipy.spatial import cKDTree
import pdal
from numpy.lib import recfunctions as rfn


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


def get_points(ept_path, bounds, wkt):
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
    pipeline = pdal.Pipeline(
        WRITE_PIPELINE.format(path=path),
        arrays=[point_cloud]
    )
    pipeline.validate()
    pipeline.execute()


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
    
def main():
    path_a10_2018 = '/var/data/rws/data/2018/entwined/ept.json'
    path_a10_2019 = '/var/data/rws/data/2019/amsterdam_entwined/ept.json'

    schema = 'nwb'
    table = 'wegvakken_20180201'

    xmin, ymin, xmax, ymax = (117944.7,483449.4,118073.4,483526.2)
    bounds = f'([{xmin}, {xmax}], [{ymin}, {ymax}])'
    wkt = 'POLYGON((117944.7 483449.4,117944.7 483526.2,118073.4 483526.2,118073.4 483449.4,117944.7 483449.4))'  # larger square

    point_cloud_1 = get_points(path_a10_2018, bounds, wkt)
    point_cloud_2 = get_points(path_a10_2019, bounds, wkt)
    out_points = filter_distance(point_cloud_1, point_cloud_2, 0.05)

    write_to_laz(out_points, '/var/data/rws/data/output/test.laz')

if __name__ == "__main__":
    main()
