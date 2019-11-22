from functions import get_points, filter_distance, recursive_planes, get_relevant_cids, find_distances_centroid
import shapely.wkt
import numpy as np
import pandas as pd
from numpy.lib import recfunctions as rfn
from db_class import Database


def main_distances(wkt):

    paths = {   
        '2018':'/var/data/rws/data/2018/entwined/ept.json', 
        '2019':'/var/data/rws/data/2019/amsterdam_entwined/ept.json'
        }



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
                n_planes = N_PLANES, 
                min_pts = MIN_PTS, 
                max_dist = MAX_DIST,
                max_iterations = MAX_ITERATIONS
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

def main():

    leda = Database('VU')
    query = 'SELECT id, ST_AsText(geom) wkt FROM pc_poc.bruggen'
    result = leda.execute_query(query)[0]

    for dictionary in result:
        
        wkt_id = dictionary['id']
        wkt = dictionary['wkt']

        print(f'clustering id: \t {wkt_id}')
        z18, z19, dz = main_distances(wkt)

        insert_query = f'INSERT INTO VU.bruggen_results VALUES ({wkt_id}, {z18}, {z19}, {dz}, ST_GeomFromText(\'{wkt}\'))'
        


if __name__ == '__main__':

    N_PLANES = 5
    MIN_PTS = 10000
    MAX_DIST = 0.1
    MAX_ITERATIONS = 5000

    main()