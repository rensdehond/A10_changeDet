Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1OGUyODEwNC03YTIzLTRjMmItOTk4Ni1iZWNkNGE1MWZhMTkiLCJpZCI6NTQzLCJpYXQiOjE1MjUyNzM4OTd9.F2r6H2XRAcnkHjkFgXAzDieW6TeIxDhTZ5hdikd-_Q8';

var qmesh = new Cesium.CesiumTerrainProvider({
    url: 'https://saturnus.geodan.nl/tomt/data/tiles/',
    requestVertexNormals: true
});


const ahn3wms = new Cesium.WebMapServiceImageryProvider({
        url: 'https://geodata.nationaalgeoregister.nl/ahn3/wms',
        layers: 'ahn3_05m_dtm',
        parameters: {
            crs: 'EPSG:28992'
        }
});

const luchtfotos = new Cesium.WebMapServiceImageryProvider({
        url: 'https://geodata.nationaalgeoregister.nl/luchtfoto/rgb/wms',
        layers: 'Actueel_ortho25',
        parameters: {
            crs: 'EPSG:3857'
        }
});

const bodemvlakken = new Cesium.WebMapServiceImageryProvider({
        url: 'https://saturnus.geodan.nl/mapproxy/bgt/service?',
        //url: 'https://saturnus.geodan.nl/cgi-bin/qgis/qgis_mapserv.fcgi?&map=bodemvlakken.qgs&',
        layers: 'bodemvlakken',
        parameters: {                         
            crs: 'EPSG:3857'
        }
});

const bgt = new Cesium.WebMapServiceImageryProvider({
        url: 'https://saturnus.geodan.nl/mapproxy/bgt/service?',
        //url: 'https://saturnus.geodan.nl/cgi-bin/qgis/qgis_mapserv.fcgi?&map=bgt.qgs&',
        layers: 'bgt',
        parameters: {                         
            crs: 'EPSG:3857'
        }
});

const viewModels = [
    new Cesium.ProviderViewModel({
        name: 'BGT',
        iconUrl: Cesium.buildModuleUrl(
            'Widgets/Images/ImageryProviders/openStreetMap.png'
        ),
        tooltip: 'BGT',
        creationFunction: function() {
            return bgt;
        }
    }),
    new Cesium.ProviderViewModel({
        name: 'Bodemvlakken',
        iconUrl: Cesium.buildModuleUrl(
            'Widgets/Images/ImageryProviders/openStreetMap.png'
        ),
        tooltip: 'Bodemvlakken',
        creationFunction: function() {
            return bodemvlakken;
        }
    }),
    new Cesium.ProviderViewModel({
        name: 'AHN3WMS',
        iconUrl: Cesium.buildModuleUrl(
            'Widgets/Images/ImageryProviders/openStreetMap.png'
        ),
        tooltip: 'AHN3',
        creationFunction: function() {
            return ahn3wms;
        }
    })
];

var viewer = new Cesium.Viewer('cesiumContainer',{
    requestRenderMode: true,
    useLayerPicker: true,
    animation: false,
    timeline: false,
    vrButton: false,
    sceneModePicker: false,
    navigationInstructionsInitiallyVisible: false,
    selectionIndicator: false,
    terrainProvider: qmesh,
    //terrainProviderViewModels: [],
    imageryProviderViewModels: viewModels
});

viewer.scene.globe.depthTestAgainstTerrain = true;
viewer.scene.globe.showGroundAtmosphere = true;
viewer.scene.globe.enableLighting = true;

viewer.scene.fog = new Cesium.Fog();

var tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
     url : "https://saturnus.geodan.nl/tomt/data/buildingtiles_adam/tileset.json",
     show: true,
     debugShowStatistics: false,
     debugShowBoundingVolume: false
}));
tileset.style = new Cesium.Cesium3DTileStyle({
    color : 'color("darksalmon")'
});


let treesets = [
"cesium_trees_120000-486000",
"cesium_trees_120000-487000",
"cesium_trees_120000-488000",
"cesium_trees_121000-486000",
"cesium_trees_121000-487000",
"cesium_trees_121000-488000",
"cesium_trees_122000-486000",
"cesium_trees_122000-487000",
"cesium_trees_122000-488000",
"cesium_trees_123000-486000",
"cesium_trees_123000-487000",
"cesium_trees_123000-488000"
];


treesets.forEach(set=>{
  window.ts = new Cesium.Cesium3DTileset({
        url: 'https://saturnus.geodan.nl/tomt/data/treesets/'+set+'/tileset.json',
        // maximumScreenSpaceError: 16.0,
        pointCloudShading: {
            attenuation: true,
            maximumAttenuation: 2.0,
            // geometricErrorScale: 0.2,
            eyeDomeLighting: true,
            eyeDomeLightingStrength: 1.0,
            eyeDomeLightingRadius: 1.0
        },
        debugShowBoundingVolume: false,
        show: true
  });
  viewer.scene.primitives.add(window.ts);
});


viewer.camera.setView({
    destination : new Cesium.Cartesian3.fromDegrees(4.90314100, 52.37072652, 1300) //AmesterdamPK
});

var currentTime = Cesium.JulianDate.fromDate(new Date('2018-8-21 16:00'));
viewer.clock.currentTime = currentTime;
