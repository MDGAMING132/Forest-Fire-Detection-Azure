const map = new maplibregl.Map({
  container: "map",
  center: [75, 20],
  zoom: 2.0,
  maxZoom: 22,
  pitch: 5,
  bearing: 0,

  style: {
    version: 8,
    sources: {
      satellite: {
        type: "raster",
        tiles: [
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ],
        tileSize: 256,
        maxzoom: 17,
        attribution: "Esri, Maxar, Earthstar Geographics"
      },

      terrainSource: {
        type: "raster-dem",
        tiles: [
          "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        ],
        encoding: "terrarium",
        tileSize: 256,
        maxzoom: 15,
        attribution: "AWS Terrain Tiles"
      },

      osmRoads: {
        type: "raster",
        tiles: [
          "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        ],
        tileSize: 256,
        maxzoom: 18,
        attribution: "© OpenStreetMap contributors"
      },

      contours: {
        type: "raster",
        tiles: [
            "https://a.tile.opentopomap.org/{z}/{x}/{y}.png",
            "https://b.tile.opentopomap.org/{z}/{x}/{y}.png",
            "https://c.tile.opentopomap.org/{z}/{x}/{y}.png"
        ],
        tileSize: 256,
        maxzoom: 15,
        attribution: "© OpenTopoMap"
      }
    },

    layers: [
      {
        id: "satellite",
        type: "raster",
        source: "satellite"
      },
      {
        id: "osm-roads",
        type: "raster",
        source: "osmRoads",
        layout: { visibility: "none" }
      },
      {
        id: "contours-layer",
        type: "raster",
        source: "contours",
        paint: {
          "raster-opacity": 1
        },
        layout: {
          visibility: "none"
        }
      }
    ],

    terrain: {
      source: "terrainSource",
      exaggeration: 1.2
    }
  }
});

map.on("load", () => {
  map.setProjection({ type: "globe" });
});

map.addControl(new maplibregl.NavigationControl(), "top-right");
map.addControl(new maplibregl.ScaleControl(), "bottom-left");
map.addControl(new maplibregl.FullscreenControl(), "top-right");

let is3D = true;
const toggleButton = document.createElement("button");
toggleButton.innerText = "2D";
toggleButton.style.position = "absolute";
toggleButton.style.top = "15px";
toggleButton.style.right = "90px";
toggleButton.style.zIndex = 10;
toggleButton.style.padding = "8px";
toggleButton.style.background = "white";
toggleButton.style.border = "1px solid black";
toggleButton.style.cursor = "pointer";
toggleButton.style.borderRadius = "20px";
toggleButton.style.fontSize = "14px";
document.body.appendChild(toggleButton);

toggleButton.onclick = () => {
  if (is3D) {
    map.setTerrain(null);
    map.setProjection({ type: "mercator" });
    map.easeTo({ pitch: 0, bearing: 0 });
    toggleButton.innerText = "3D";
  } else {
    map.setProjection({ type: "globe" });
    map.setTerrain({ source: "terrainSource", exaggeration: 1.2 });
    map.easeTo({ pitch: 5 });
    toggleButton.innerText = "2D";
  }
  is3D = !is3D;
};

const coordsDiv = document.getElementById("coords");
map.on("mousemove", (e) => {
  const lng = e.lngLat.lng.toFixed(6);
  const lat = e.lngLat.lat.toFixed(6);
  coordsDiv.innerHTML = `Lat: ${lat} | Lng: ${lng}`;
});

function setMapView(mode) {
  map.setLayoutProperty("satellite", "visibility", "none");
  map.setLayoutProperty("osm-roads", "visibility", "none");
  map.setLayoutProperty("contours-layer", "visibility", "none");

  if (mode === "satellite") {
    map.setLayoutProperty("satellite", "visibility", "visible");
  }

  if (mode === "roadmap") {
    map.setLayoutProperty("osm-roads", "visibility", "visible");
  }

  if (mode === "contours") {
    map.setLayoutProperty("satellite", "visibility", "visible");
    map.setLayoutProperty("contours-layer", "visibility", "visible");
  }
}

const mapSelectorContainer = document.createElement("div");
mapSelectorContainer.style.position = "absolute";
mapSelectorContainer.style.top = "15px";
mapSelectorContainer.style.right = "140px";
mapSelectorContainer.style.zIndex = 10;
mapSelectorContainer.style.background = "white";
mapSelectorContainer.style.border = "1px solid black";
mapSelectorContainer.style.borderRadius = "20px";
mapSelectorContainer.style.padding = "4px 8px";
mapSelectorContainer.style.display = "flex";
mapSelectorContainer.style.alignItems = "center";
document.body.appendChild(mapSelectorContainer);

const mapIcon = document.createElement("img");
mapIcon.src = "map icon.png";
mapIcon.alt = "Map icon";
mapIcon.style.width = "26px";
mapIcon.style.height = "22px";
mapIcon.style.objectFit = "cover";
mapIcon.style.borderRadius = "4px";
mapIcon.style.marginRight = "6px";
mapSelectorContainer.appendChild(mapIcon);

const mapSelect = document.createElement("select");
mapSelect.style.border = "none";
mapSelect.style.outline = "none";
mapSelect.style.fontSize = "13px";
mapSelect.style.cursor = "pointer";

const optionSatellite = document.createElement("option");
optionSatellite.value = "satellite";
optionSatellite.text = "Satellite";

const optionContours = document.createElement("option");
optionContours.value = "contours";
optionContours.text = "Contours";

const optionRoadmap = document.createElement("option");
optionRoadmap.value = "roadmap";
optionRoadmap.text = "Roadmap";


mapSelect.appendChild(optionSatellite);
mapSelect.appendChild(optionContours);
mapSelect.appendChild(optionRoadmap);

mapSelectorContainer.appendChild(mapSelect);

mapSelect.onchange = () => {
  setMapView(mapSelect.value);
};

setMapView("satellite");
