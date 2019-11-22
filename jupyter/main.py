from functions import get_points, filter_distance, recursive_planes, get_relevant_cids, find_distances_centroid
import shapely.wkt
import numpy as np
import pandas as pd
from numpy.lib import recfunctions as rfn


def main(wkt):

    paths = {   
        '2018':'/var/data/rws/data/2018/entwined/ept.json', 
        '2019':'/var/data/rws/data/2019/amsterdam_entwined/ept.json'
        }

    n_planes = 5
    min_pts = 10000
    max_dist = 0.1
    max_iterations = 1000

    xmin,ymin,xmax,ymax = shapely.wkt.loads(wkt).bounds
    bounds = f'([{xmin}, {xmax}], [{ymin}, {ymax}])'

    pc18 = get_points(paths['2018'], bounds, wkt)
    print(f'loaded pc 2018')
    pc19 = get_points(paths['2019'], bounds, wkt)
    print(f'loaded pc 2019')

    filtered_2018 = filter_distance(pc18, pc19)
    filtered_2019 = filter_distance(pc19, pc18)
    print('filtered pcs')

    pcs = {
        '2018': filtered_2018,
        '2019':filtered_2019
        }

    results = {}

    for year in ('2018', '2019'):
        points = pd.DataFrame(
        np.array(
            pcs[year][['X','Y','Z','Red','Green','Blue']].tolist()), 
            columns=['x', 'y', 'z','red','green','blue'])

        planes, models = recursive_planes(
                points.copy(), 
                n_planes = n_planes, 
                min_pts = min_pts, 
                max_dist = max_dist,
                max_iterations = max_iterations
            )

        rel_cids = get_relevant_cids(planes)

        z = find_distances_centroid(
                models[rel_cids[0]], 
                models[rel_cids[1]], 
                shapely.wkt.loads(wkt))

        results[f'z_{year}'] = z
        results[f'model_{year}_{rel_cids[0]}'] = models[rel_cids[0]]
        results[f'model_{year}_{rel_cids[1]}'] = models[rel_cids[1]]
            

    z_diff = results['z_2018'] - results['z_2019']

    return results['z_2018'], results['z_2019'], z_diff

if __name__ == '__main__':
    wkt = 'POLYGON((117875.3 487304,117875.3 487329,117906.1 487329,117906.1 487304,117875.3 487304))' # brug
    z18, z19, dz= main(wkt)

    print(z18, '\t' , z19, '\t' , dz)