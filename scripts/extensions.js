(function() {
    'use strict';

    // Wait for map to be ready
    function waitForMap(callback) {
        if (typeof map !== 'undefined' && map.loaded && map.loaded()) {
            callback();
        } else if (typeof map !== 'undefined') {
            map.on('load', callback);
        } else {
            setTimeout(() => waitForMap(callback), 100);
        }
    }

    // Fetch fire data from FIRMS API
    async function fetchFireData() {
        const apiKey = CONFIG.FIRMS_MAP_KEY;
        
        // Get current map bounds to fetch only visible area (more efficient)
        const bounds = map.getBounds();
        const west = bounds.getWest().toFixed(2);
        const south = bounds.getSouth().toFixed(2);
        const east = bounds.getEast().toFixed(2);
        const north = bounds.getNorth().toFixed(2);
        
        // FIRMS API endpoints for different satellites
        const sources = [
            { id: 'VIIRS_SNPP_NRT', name: 'VIIRS SNPP' },
            { id: 'VIIRS_NOAA20_NRT', name: 'VIIRS NOAA-20' }
        ];
        
        let allFeatures = [];
        
        for (const source of sources) {
            try {
                // Use area endpoint with bounding box
                const url = `https://firms.modaps.eosdis.nasa.gov/api/area/csv/${apiKey}/${source.id}/${west},${south},${east},${north}/1`;
                
                console.log(`Fetching ${source.name}...`);
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    console.warn(`${source.name}: ${response.status}`);
                    continue;
                }
                
                const text = await response.text();
                
                // Check if it's valid CSV
                if (text.includes('<!DOCTYPE') || text.includes('<html') || text.length < 50) {
                    console.warn(`${source.name}: Invalid response`);
                    continue;
                }
                
                const features = csvToGeoJSON(text, source.name);
                allFeatures = allFeatures.concat(features);
                
                console.log(`${source.name}: ${features.length} records`);
                
            } catch (err) {
                console.error(`${source.name}:`, err.message);
            }
        }
        
        return {
            type: 'FeatureCollection',
            features: allFeatures
        };
    }

    // Convert CSV to GeoJSON
    function csvToGeoJSON(csv, source) {
        const lines = csv.trim().split('\n');
        if (lines.length < 2) return [];
        
        const headers = lines[0].toLowerCase().split(',');
        const latIdx = headers.indexOf('latitude');
        const lonIdx = headers.indexOf('longitude');
        const frpIdx = headers.indexOf('frp');
        const confIdx = headers.indexOf('confidence');
        const dateIdx = headers.indexOf('acq_date');
        const timeIdx = headers.indexOf('acq_time');
        const brightIdx = headers.findIndex(h => h.includes('bright'));
        
        const features = [];
        
        for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',');
            const lat = parseFloat(cols[latIdx]);
            const lon = parseFloat(cols[lonIdx]);
            
            if (isNaN(lat) || isNaN(lon)) continue;
            
            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [lon, lat]
                },
                properties: {
                    frp: parseFloat(cols[frpIdx]) || 10,
                    confidence: cols[confIdx] || 'nominal',
                    date: cols[dateIdx] || '',
                    time: cols[timeIdx] || '',
                    brightness: parseFloat(cols[brightIdx]) || 300,
                    source: source
                }
            });
        }
        
        return features;
    }

    // Add fire layer to map
    function addFireLayer(geojson) {
        const sourceId = 'fire-source';
        const glowId = 'fire-glow';
        const layerId = 'fire-points';
        
        // Update or add source
        if (map.getSource(sourceId)) {
            map.getSource(sourceId).setData(geojson);
        } else {
            map.addSource(sourceId, {
                type: 'geojson',
                data: geojson
            });
            
            // Glow effect layer
            map.addLayer({
                id: glowId,
                type: 'circle',
                source: sourceId,
                paint: {
                    'circle-radius': [
                        'interpolate', ['linear'], ['zoom'],
                        2, ['interpolate', ['linear'], ['get', 'frp'], 0, 3, 100, 8, 500, 15],
                        8, ['interpolate', ['linear'], ['get', 'frp'], 0, 8, 100, 20, 500, 40]
                    ],
                    'circle-color': [
                        'interpolate', ['linear'], ['get', 'frp'],
                        0, '#ffff00',
                        50, '#ffa500',
                        150, '#ff4500',
                        300, '#ff0000'
                    ],
                    'circle-blur': 1,
                    'circle-opacity': 0.5
                }
            });
            
            // Main fire points
            map.addLayer({
                id: layerId,
                type: 'circle',
                source: sourceId,
                paint: {
                    'circle-radius': [
                        'interpolate', ['linear'], ['zoom'],
                        2, ['interpolate', ['linear'], ['get', 'frp'], 0, 2, 100, 5, 500, 10],
                        8, ['interpolate', ['linear'], ['get', 'frp'], 0, 5, 100, 12, 500, 25]
                    ],
                    'circle-color': [
                        'interpolate', ['linear'], ['get', 'frp'],
                        0, '#ffff00',
                        50, '#ffa500',
                        150, '#ff4500',
                        300, '#ff0000'
                    ],
                    'circle-stroke-width': 1,
                    'circle-stroke-color': '#fff'
                }
            });
            
            // Click popup
            map.on('click', layerId, (e) => {
                const f = e.features[0];
                const p = f.properties;
                const coords = f.geometry.coordinates;
                
                new maplibregl.Popup()
                    .setLngLat(coords)
                    .setHTML(`
                        <div style="font-family: system-ui; min-width: 180px;">
                            <div style="font-weight: 600; color: #ff4500; margin-bottom: 8px; font-size: 14px;">
                                 Fire Detected
                            </div>
                            <div style="font-size: 12px; line-height: 1.6; color: #333;">
                                <b>Intensity:</b> ${p.frp} MW<br>
                                <b>Confidence:</b> ${p.confidence}<br>
                                <b>Source:</b> ${p.source}<br>
                                <b>Date:</b> ${p.date}<br>
                                <b>Time:</b> ${p.time} UTC<br>
                                <b>Location:</b> ${coords[1].toFixed(4)}°, ${coords[0].toFixed(4)}°
                            </div>
                        </div>
                    `)
                    .addTo(map);
            });
            
            map.on('mouseenter', layerId, () => {
                map.getCanvas().style.cursor = 'pointer';
            });
            map.on('mouseleave', layerId, () => {
                map.getCanvas().style.cursor = '';
            });
        }
        
        return geojson.features.length;
    }

    // Load fires for current view
    async function loadFires() {
        try {
            const geojson = await fetchFireData();
            addFireLayer(geojson);
        } catch (err) {
            console.error('Fire load error:', err);
        }
    }

    // Auto-reload on map move
    let moveTimeout;
    function setupAutoReload() {
        map.on('moveend', () => {
            // Only auto-reload if we already have data
            if (map.getSource('fire-source')) {
                clearTimeout(moveTimeout);
                moveTimeout = setTimeout(() => {
                    console.log(' Reloading fires for new view...');
                    loadFires();
                }, 1000);
            }
        });
    }

    // Initialize
    waitForMap(() => {
        console.log('Fire intelligence: initializing...');
        setupAutoReload();
        
        // Auto-load fires on start
        setTimeout(() => {
            loadFires();
        }, 1000);
        
        console.log('Fire intelligence: ready. Open the sidebar for controls.');
    });

})();
