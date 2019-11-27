import numpy as np
import pandas as pd
import shapely.wkt
from numpy.lib import recfunctions as rfn

from db_class import Database
from functions import (filter_distance, find_distances_centroid,
                       find_distances_pcs, get_points, get_relevant_cids,
                       recursive_planes, write_to_laz, prepare_sql_string)


def main_distances(wkt, method = 'ransac'):

    assert method in ('ransac', 'pointcloud'), f'method is not ransac or pointcloud but "{method}".'

    paths = {
        '2018': '/var/data/rws/data/2018/entwined/ept.json',
        '2019': '/var/data/rws/data/2019/amsterdam_entwined/ept.json'
    }

    xmin, ymin, xmax, ymax = shapely.wkt.loads(wkt).bounds
    bounds = f'([{xmin}, {xmax}], [{ymin}, {ymax}])'

    pc18 = get_points(paths['2018'], bounds, wkt)
    print(f'loaded pc 2018')
    pc19 = get_points(paths['2019'], bounds, wkt)
    print(f'loaded pc 2019')

    # pre processing (filtering of everything that moved more than  5 cm)
    filtered_2018 = filter_distance(pc18, pc19, 0.05)
    filtered_2019 = filter_distance(pc19, pc18, 0.05)
    print('filtered pcs')

    pcs = {
        '2018': filtered_2018,
        '2019': filtered_2019
    }

    results = {}
    planes = {}

    for year in ('2018', '2019'):
        points = pd.DataFrame(np.array(
            pcs[year][['X', 'Y', 'Z', 'Red', 'Green', 'Blue']].tolist()),
            columns=['x', 'y', 'z', 'red', 'green', 'blue'])

        planes_year, models_year = recursive_planes(
            points.copy(),
            n_planes=N_PLANES,
            min_pts=MIN_PTS,
            max_dist=MAX_DIST,
            max_iterations=MAX_ITERATIONS
        )

        planes[year] = planes_year
        rel_cids = get_relevant_cids(planes[year])

        results[f'model_{year}_{rel_cids[0]}'] = models_year[rel_cids[0]]
        results[f'model_{year}_{rel_cids[1]}'] = models_year[rel_cids[1]]

        if method == 'ransac':

            z = find_distances_centroid(
                models_year[rel_cids[0]],
                models_year[rel_cids[1]],
                shapely.wkt.loads(wkt))

            # z results
            results[f'z_{year}'] = z

        if method == 'pointcloud':
            z = find_distances_pcs(planes[year], rel_cids, PERCENTAGE)
            results[f'z_{year}'] = z

    
    results['z_diff'] = results['z_2018'] - results['z_2019']
    



    return results


def main():

    # database connection and query
    leda = Database('VU')
    query = 'SELECT id, ST_AsText(geom) wkt FROM pc_poc.bruggen where id = 17'
    result = leda.execute_query(query)[0]

    for dictionary in result:

        wkt_id = dictionary['id']
        wkt = dictionary['wkt']

        print(f'clustering id: \t {wkt_id}')
        # :TODO main_distances(wkt, write_laz = True)
        results = main_distances(wkt, 'pointcloud')

        values_list =  [
            results['model_2018_1'].point,
            results['model_2018_1'].normal,
            results['model_2018_2'].point,
            results['model_2018_2'].normal,
            results['z_2018'],
            results['model_2019_1'].point,
            results['model_2019_1'].normal,
            results['model_2019_2'].point,
            results['model_2019_2'].normal,
            results['z_2019'],
            results['z_diff']
        ]

        value_string = prepare_sql_string(values_list)
        print('vs:', value_string)

        insert_query = f'INSERT INTO pc_poc.results_pointcloud \
            VALUES ({wkt_id}, {value_string}, ST_GeomFromText(\'{wkt}\'))'
        # insert_query = f'INSERT INTO pc_poc.bruggen_results_point_normal VALUES ({values}, ST_GeomFromText(\'{wkt}\'))'
        leda.execute_query(insert_query)


if __name__ == '__main__':

    # Ransac parameters
    N_PLANES = 3
    MIN_PTS = 100
    MAX_DIST = 0.1
    MAX_ITERATIONS = 5000

    # Pointcloud method parameters
    PERCENTAGE = 0.05

    main()
