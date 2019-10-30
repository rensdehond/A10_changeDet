pdal pipeline pipeline.json;
echo 'ahn filtered';
entwine build -i /var/data/arnot/AHN/c_10cn2_filtered.laz -o /var/data/arnot/AHN/build_/ -r EPSG:28992 EPSG:4978;
echo 'filtered_laz build';
entwine convert -i /var/data/arnot/AHN/build/ -o /var/data/arnot/AHN/cesium/;
echo 'converted to cesium';

