Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiNDc1ZjQwMS1hOGI2LTQyNmUtYmYxMi1jODlhNDNlMjViZTkiLCJpZCI6NDc4OSwic2NvcGVzIjpbImFzciIsImdjIl0sImlhdCI6MTU0MTYyNTg3OX0.mNoGLdYuwqsnRRkQtdYNMbJfMBoZF2hPkbc4SRVVqNw';

const bgt = new Cesium.WebMapServiceImageryProvider({
    url: 'https://saturnus.geodan.nl/mapproxy/bgt/service?',
    //url: 'https://saturnus.geodan.nl/cgi-bin/qgis/qgis_mapserv.fcgi?&map=bgt.qgs&',
    layers: 'bgt',
    parameters: {
        crs: 'EPSG:3857'
    }
});

var terraintiles = new Cesium.CesiumTerrainProvider({
    url: 'https://saturnus.geodan.nl/tomt/data/terraintiles_zuidoost/',
    requestVertexNormals: true
});



var viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: terraintiles,
    imageryProvider: bgt
});

viewer.scene.debugShowFramesPerSecond = true;
var tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
    url : 'https://saturnus.geodan.nl/arnot/data/buildingtiles_colorroofs/tiles/tileset.json'
}));

viewer.scene.globe.depthTestAgainstTerrain = true;
viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0, -0.5, 0));
viewer.scene.primitives.add(tileset);


// see : https://cesiumjs.org/Cesium/Apps/Sandcastle/index.html?src=3D%20Tiles%20Feature%20Picking.html
// HTML overlay for showing feature name on mouseover
var nameOverlay = document.createElement('div');
viewer.container.appendChild(nameOverlay);
nameOverlay.className = 'backdrop';
nameOverlay.style.display = 'none';
nameOverlay.style.position = 'absolute';
nameOverlay.style.bottom = '0';
nameOverlay.style.left = '0';
nameOverlay.style['pointer-events'] = 'none';
nameOverlay.style.padding = '4px';
nameOverlay.style.backgroundColor = 'grey';
// Information about the currently selected feature
var selected = {
    feature: undefined,
    originalColor: new Cesium.Color()
};
// An entity object which will hold info about the currently selected feature for infobox display
var selectedEntity = new Cesium.Entity();
// Get default left click handler for when a feature is not picked on left click

// Silhouettes are supported
var silhouetteBlue = Cesium.PostProcessStageLibrary.createEdgeDetectionStage();
silhouetteBlue.uniforms.color = Cesium.Color.BLUE;
silhouetteBlue.uniforms.length = 0.01;
silhouetteBlue.selected = [];

var silhouetteGreen = Cesium.PostProcessStageLibrary.createEdgeDetectionStage();
silhouetteGreen.uniforms.color = Cesium.Color.LIME;
silhouetteGreen.uniforms.length = 0.01;
silhouetteGreen.selected = [];

viewer.scene.postProcessStages.add(Cesium.PostProcessStageLibrary.createSilhouetteStage([silhouetteBlue, silhouetteGreen]));
// Silhouette a feature blue on hover.
viewer.screenSpaceEventHandler.setInputAction(function onMouseMove(movement) {
    // If a feature was previously highlighted, undo the highlight
    silhouetteBlue.selected = [];
    // Pick a new feature
    var pickedFeature = viewer.scene.pick(movement.endPosition);
    if (!Cesium.defined(pickedFeature)) {
        nameOverlay.style.display = 'none';
        return;
    }
    // A feature was picked, so show it's overlay content
    nameOverlay.style.display = 'block';
    nameOverlay.style.bottom = viewer.canvas.clientHeight - movement.endPosition.y + 'px';
    nameOverlay.style.left = movement.endPosition.x + 'px';
    
    //var propertyNames = pickedFeature.getPropertyNames();
    var id = pickedFeature.getProperty("arr").split(',')[0];
    var num_geoms = pickedFeature.getProperty("arr").split(',')[1];
    var area = pickedFeature.getProperty("arr").split(',')[2];
    // id, num_geoms, area = pickedFeature.getProperty("arr").split(',');
    console.log(id, num_geoms, area)
    var name = `id: ${id}`;
    if (!Cesium.defined(name)) {
        name = `id: ${id}`;
    }
    nameOverlay.textContent = name;
    // Highlight the feature if it's not already selected.
    if (pickedFeature !== selected.feature) {
        silhouetteBlue.selected = [pickedFeature];
    }
}, Cesium.ScreenSpaceEventType.MOUSE_MOVE) ;


// Silhouette a feature on selection and show metadata in the InfoBox.
viewer.screenSpaceEventHandler.setInputAction(function onLeftClick(movement) {
    // If a feature was previously selected, undo the highlight
    silhouetteGreen.selected = [];

    // Pick a new feature
    var pickedFeature = viewer.scene.pick(movement.position);
    if (!Cesium.defined(pickedFeature)) {
        clickHandler(movement);
        return;
    }

    // Select the feature if it's not already selected
    if (silhouetteGreen.selected[0] === pickedFeature) {
        return;
    }

    // Save the selected feature's original color
    var highlightedFeature = silhouetteBlue.selected[0];
    if (pickedFeature === highlightedFeature) {
        silhouetteBlue.selected = [];
    }

    // Highlight newly selected feature
    silhouetteGreen.selected = [pickedFeature];

    var id = highlightedFeature.getProperty("arr").split(',')[0];
    var num_geoms = highlightedFeature.getProperty("arr").split(',')[1];
    var area = highlightedFeature.getProperty("arr").split(',')[2];

    // Set feature infobox description
    var featureName = id;
    selectedEntity.name = featureName;
    selectedEntity.description = 'Loading <div class="cesium-infoBox-loading"></div>';
    viewer.selectedEntity = selectedEntity;
    selectedEntity.description = '<table class="cesium-infoBox-defaultTable"><tbody>' +
                                 '<tr><th>num geoms:</th><td>' + num_geoms + '</td></tr>' +
                                 '<tr><th>area:</th><td>' + area + '</td></tr>' +
                                 '</tbody></table>';
}, Cesium.ScreenSpaceEventType.LEFT_CLICK);