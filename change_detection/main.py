import numpy as np
import pandas as pd
import shapely.wkt
from numpy.lib import recfunctions as rfn
import os 
from pathlib import Path
import yaml

from db_class import Database
from functions import (filter_distance, find_distances_centroid,
                       find_distances_pcs, get_points, get_relevant_cids,
                       recursive_planes, write_to_laz, prepare_sql_string,
                       write_to_laz)


def main_distances(wkt, method = 'ransac', laz_dir = None):
    '''
    Function that calculates the difference in height between the top and bottom
    of a bridge over a road between two years. 

    in:
        wkt [string]: 
            Text representation of a polygon. The polygon lies on the A10 and 
            there are points in this polygon in the paths.
        
        method [string]:
            Must be ransac or pointcloud. Specifies the method which is used to 
            calculate the difference in height.
        
        laz_dir [string or None]: 
            If it's a string it has to be a Path to a output directory for the laz files.
            If it's None, no output laz file is generated.
    '''

    assert method in ('ransac', 'pointcloud'), f'method is not ransac or pointcloud but "{method}".'
    assert isinstance(laz_dir, str), f'write_laz should be a string of the output directory but is {laz_dir}'

    paths = {
        '2018': config['path_2019'],
        '2019': config['path_2018']
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

        if laz_dir != None:
            laz_path = Path(laz_dir)
            if not laz_path.parent.exists:
                print('The output path specified for output laz files is incorrect.')

            laz_path.mkdir(parents=False, exist_ok=True)
            laz_fn = f'{year}'

            laz_array = rfn.append_fields(pcs[year][['X','Y','Z','Red','Green','Blue']],
                                          'Classification',
                                          planes[year]['cid'].astype(np.uint16),
                                          usemask=False,
                                         )
        
            write_to_laz(laz_array, laz_path.joinpath(f'{year}.laz'))
            print(f'wrote to {laz_dir}/{year}.laz"')

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
    schema = config['schema']
    table = config['table']
    out_table = config['out_table']

    # database connection and query
    leda = Database(
            'VU',  
            host=config['host'], 
            dbname=config['dbname'], 
            user=config['user'], 
            password=config['password'], 
            port=config['port']
        )

    query = f'SELECT id, ST_AsText(geom) wkt FROM {schema}.{table} where id in (1,2,3,4)'
    result = leda.execute_query(query)[0]

    for dictionary in result:
        wkt_id = dictionary['id']
        wkt = dictionary['wkt']

        print(f'clustering id: \t {wkt_id}')
        results = main_distances(wkt, 'pointcloud', laz_dir = config['output_path'] + f'{wkt_id}')

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

        insert_query = f'INSERT INTO {schema}.{out_table} \
            VALUES ({wkt_id}, {value_string}, ST_GeomFromText(\'{wkt}\'))'
        leda.execute_query(insert_query)


if __name__ == '__main__':
    with open('config.yaml', 'rt') as f:
        config = yaml.safe_load(f)

    # Ransac parameters
    N_PLANES = 2
    MIN_PTS = 100
    MAX_DIST = 0.1
    MAX_ITERATIONS = 5000

    # Pointcloud method parameters
    PERCENTAGE = 0.05

    main()
