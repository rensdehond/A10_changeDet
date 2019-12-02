DATA_PATH=/var/data/rws/data

mkdir $DATA_PATH/2018/filtered_las/

for i in $DATA_PATH/2018/las_processor_bundled_out/* ; do
	if [ ! -f $(echo $i | sed s/las_processor_bundled_out/filtered_las/) ]; then
		pdal pipeline normalize_pipeline.json normalize_pipeline.json \
		       	--readers.las.filename=$i \
	        	--writers.las.filename=$(echo $i | sed s/las_processor_bundled_out/filtered_las/)
	fi
done
echo 'filtered 2018'

mkdir $DATA_PATH/2019/filtered_las/
for i in $DATA_PATH/2019/amsterdam/* ; do
	if [ ! -f $(echo $i | sed s/amsterdam/filtered_las/) ]; then
		pdal pipeline cast_type_pipeline.json cast_type_pipeline.json \
			--readers.las.filename=$i \
			--writers.las.filename=$(echo $i | sed s/amsterdam/filtered_las/)
	fi

done
echo 'filtered 2019'

entwine build -c $DATA_PATH/config-2018-cesium.json
echo 'tiled 2018 to epsg 4978'
entwine build -c $DATA_PATH/config-2019-cesium.json
echo 'tiled 2019 to epsg 4978'

entwine convert -i $DATA_PATH/2018/entwined-4978/ -o $DATA_PATH/2018/cesium/
echo 'converted 2018 to cesium';
entwine convert -i $DATA_PATH/2019/entwined-4978/ -o $DATA_PATH/2019/cesium/
echo 'converted 2019 to cesium';


