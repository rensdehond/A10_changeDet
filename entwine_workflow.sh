# entwine build -i /var/data/arnot/AHN/c_10cn2_filtered.laz -o /var/data/arnot/AHN/build_/ -r EPSG:28992 EPSG:4978;

entwine build -c /var/data/rws/data/config-2018-cesium.json
echo 'tiled 2018 to epsg 4978'
entwine build -c /var/data/rws/data/config-2019-cesium.json
echo 'tiled 2019 to epsg 4978'

entwine convert -i /var/data/rws/data/2018/entwined-4978/ -o /var/data/rws/data/2018/cesium/
echo 'converted 2018 to cesium';
entwine convert -i /var/data/rws/data/2019/entwined-4978/ -o /var/data/rws/data/2019/cesium/
echo 'converted 2019 to cesium';


