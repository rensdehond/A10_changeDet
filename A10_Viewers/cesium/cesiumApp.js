Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI3NDU0ZmY5MC05NGQ2LTQ2MzItYTU2ZC1kOTA2MmI0MzlmODciLCJpZCI6NDU1MSwic2NvcGVzIjpbImFzciIsImdjIl0sImlhdCI6MTU0MTA5NTY0Mn0.HYTFh-384LduDB2N4c3kOTR5W_7HAy8eKbNJYPVHwLw';

var style = document.createElement('style');
style.innerHTML = "body, html { width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; } #top { display: none; }"
document.body.appendChild(style);

var imageryProviders = Cesium.createDefaultImageryProviderViewModels();
var terrainProviders = Cesium.createDefaultTerrainProviderViewModels();

var terrainIndex =  1

var viewer = new Cesium.Viewer('cesiumContainer', {
imageryProviderViewModels: imageryProviders,
selectedImageryProviderViewModel: imageryProviders[6],
terrainProviderViewModels: terrainProviders,
selectedTerrainProviderViewModel: terrainProviders[terrainIndex]
});

window.tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
url: 'http://metis.geodan.nl:8083/tileset.json'	
}));

tileset.style = new Cesium.Cesium3DTileStyle({
pointSize: 3
});

tileset.readyPromise.then(function() {
tileset.pointCloudShading.attenuation = true

console.log('Loaded tileset');
viewer.zoomTo(tileset)
})
.otherwise(function(error){
console.log(error)
});
