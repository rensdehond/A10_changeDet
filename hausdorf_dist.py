import numpy as np
from scipy.spatial import cKDTree
import pdal
from numpy.lib import recfunctions as rfn
from shapely.wkt import loads

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

    vakken = [
        #(0,'POLYGON((121185 481896,121185 484586,125726 484586,125726 481896,121185 481896))'),
        #(1,'POLYGON((125726 483630,125726 488614,127224 488614,127224 483630,125726 483630))'),
        (2,'POLYGON((122658 488614,122658 492179,127141 492179,127141 488614,122658 488614))'),
        (3,'POLYGON((118353 492179,118353 493635,123583 493635,123583 492179,118353 492179))'),
        (4,'POLYGON((117252 488685,117252 492179,119956 492179,119956 488685,117252 488685))'),
        (5,'POLYGON((117346 483929,117346 488685,118379 488685,118379 483929,117346 483929))'),
        (6,'POLYGON((117428 481921,117428 483929,121185 483929,121185 481921,117428 481921))')
    ]

    test_vakken = [
        'POLYGON((117711.232824925 484275.626208148,117711.232824925 484346.789941131,117770.396399013 484346.789941131,117770.396399013 484275.626208148,117711.232824925 484275.626208148))',
        'POLYGON((117770.675472475 484275.068061223,117770.675472475 484345.952720743,117821.18776922 484345.952720743,117821.18776922 484275.068061223,117770.675472475 484275.068061223))',
        'POLYGON((117724.628351134 484211.16023827,117724.628351134 484273.393620447,117770.675472475 484273.393620447,117770.675472475 484211.16023827,117724.628351134 484211.16023827))',
        'POLYGON((117769.838252087 484211.997458658,117769.838252087 484272.556400059,117822.30406307 484272.556400059,117822.30406307 484211.997458658,117769.838252087 484211.997458658))'
    ]

    schema = 'nwb'
    table = 'wegvakken_20180201'

    for i, vak in vakken:
        print(f'started vak {i}')
        geom = loads(vak)
        xmin, ymin, xmax, ymax = geom.bounds

        # xmin, ymin, xmax, ymax = (117944.7,483449.4,118073.4,483526.2)
        # wkt = 'POLYGON((117944.7 483449.4,117944.7 483526.2,118073.4 483526.2,118073.4 483449.4,117944.7 483449.4))'  # larger square

        bounds = f'([{xmin}, {xmax}], [{ymin}, {ymax}])'
        point_cloud_1 = get_points(path_a10_2018, bounds, vak)
        print(f'loaded pc 1 from  vak {i}')
        point_cloud_2 = get_points(path_a10_2019, bounds, vak)
        print(f'loaded pc 2 from  vak {i}')
        out_points = filter_distance(point_cloud_1, point_cloud_2, 0.05)
        print(f'filtered pcs from  vak {i}, start writing')

        write_to_laz(out_points, f'/var/data/rws/data/output/A10_vak_{i}.laz')
        print(f'vak {i}, done writing')

if __name__ == "__main__":
    main()
