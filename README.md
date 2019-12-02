# Detect drive through hights in high resolution point clouds
This repository contains the method for the detation of differences 'drive through height'. 

## Set up
`conda env create -f vu-pointclouds.yml`

## How to use?

1.  fill the config_template.yaml and rename to config.yaml
2.  run: `python3 main.py`

## What does it do?
this process wil loop through each of the polygons in `input table`. 
### For each polygon the process will:
1.  Find the points within the polygon for each of the years 2018 and 2019 (given the points related to the paths `path_2018` and `path_2019`) 
### For each year the process will:
    1.  Estimate two planes per polygon; one for the bottom (the road) and the top (the ceiling).
    2.  Calculate the difference in height between the years.
    3.  write results to the output table. The results are:
        1.   Four times the point and normal that represent each plane. 2 tops, 2 bottoms for 2 years makes four.
        2.   The height per year
        3.   the difference in height


## The initial plan
[see the very rough plan](plan.md)

## License
[MIT License](LICENSE)
