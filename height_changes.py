from hausdorf_dist import get_points, write_to_laz
import pdal

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

def main():
    test_area = [117813.6,487266.1,117942.1,487370.7]
    xmin,ymin,xmax,ymax = test_area

    path_a10_2018 = '/var/data/rws/data/2018/entwined/ept.json'
    path_a10_2019 = '/var/data/rws/data/2019/amsterdam_entwined/ept.json'

    wkt = 'POLYGON((117813.6 487266.1,117813.6 487370.7,117942.1 487370.7,117942.1 487266.1,117813.6 487266.1))'
        
        bounds = f'([{xmin}, {xmax}], [{ymin}, {ymax}])'
        point_cloud_1 = get_points(path_a10_2018, bounds, wkt)
        print(f'loaded pc 1')
        point_cloud_2 = get_points(path_a10_2019, bounds, wkt)
        print(f'loaded pc 2')

        


if __name__ == '__main__':
    main()