(function () {
  const map = window.map || (typeof map !== "undefined" ? map : null);
  if (!map) return;

  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl(), "bottom-left");
  map.addControl(new maplibregl.FullscreenControl(), "top-right");

  let is3D = true;

  const toggleButton = document.createElement("button");
  toggleButton.innerText = "2D";
  Object.assign(toggleButton.style, {
    position: "absolute",
    top: "15px",
    right: "90px",
    zIndex: 10,
    padding: "8px",
    background: "white",
    border: "1px solid black",
    cursor: "pointer",
    borderRadius: "20px",
    fontSize: "14px",
    fontWeight: "bold"
  });
  document.body.appendChild(toggleButton);

  toggleButton.onclick = () => {
    if (is3D) {
      map.setTerrain(null);
      map.setProjection({ type: "mercator" });
      map.easeTo({ pitch: 0, bearing: 0 });
      toggleButton.innerText = "3D";
    } else {
      map.setProjection({ type: "globe" });
      map.setTerrain({ source: "terrainSource", exaggeration: 1.5 });
      map.easeTo({ pitch: 0 });
      toggleButton.innerText = "2D";
    }
    is3D = !is3D;
  };
})();
