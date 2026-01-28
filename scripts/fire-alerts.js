// Fire Alerts Module - Fetches and displays AI fire detection alerts

(function() {
    const REFRESH_INTERVAL = 5000; // 5 seconds
    let alertsCache = [];
    let markers = [];

    // Fetch fire alerts from backend
    async function fetchFireAlerts() {
        try {
            const response = await fetch('/api/fire-alerts');
            if (!response.ok) {
                console.error('Failed to fetch fire alerts');
                return [];
            }
            const data = await response.json();
            return data.alerts || [];
        } catch (error) {
            console.error('Error fetching fire alerts:', error);
            return [];
        }
    }

    // Format timestamp to readable format
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds

        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    // Create alert card HTML
    function createAlertCard(alert) {
        // Handle both webcam alerts and drone alerts
        const isDrone = alert.source === 'aerial_camera' || alert.device?.includes('Drone');
        const locationText = alert.location ? 
            (isDrone ? 
                `🚁 Drone: ${alert.location.coordinates || 'GPS acquiring...'}` :
                `${alert.location.city || ''}, ${alert.location.state || ''}, ${alert.location.country || ''}`.replace(/^,\s*|,\s*$/g, '').replace(/,\s*,/g, ',')) :
            'Location unavailable';
        
        const confidencePercent = alert.confidence ? (alert.confidence * 100).toFixed(1) : 'N/A';

        return `
            <div class="fire-alert-card" data-alert-id="${alert.id}" style="
                background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
                color: white;
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s;
                box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);
            " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="material-icons-round" style="font-size:20px;">${isDrone ? 'emergency' : 'warning'}</span>
                        <strong style="font-size:14px;">FIRE DETECTED ${isDrone ? '(DRONE)' : ''}</strong>
                    </div>
                    <span style="font-size:11px; opacity:0.9;">${formatTime(alert.timestamp)}</span>
                </div>
                <div style="font-size:12px; opacity:0.95; margin-bottom:6px;">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                        <span class="material-icons-round" style="font-size:14px;">${isDrone ? 'flight' : 'location_on'}</span>
                        <span>${locationText}</span>
                    </div>
                    ${alert.location && (alert.location.latitude || alert.location.lat) && (alert.location.longitude || alert.location.lon) ? `
                    <div style="font-size:11px; opacity:0.8; margin-left:20px;">
                        📍 ${(alert.location.latitude || alert.location.lat).toFixed(6)}, ${(alert.location.longitude || alert.location.lon).toFixed(6)}
                        ${alert.location.altitude ? ` ✈️ ${alert.location.altitude.toFixed(1)}m` : ''}
                    </div>
                    ` : ''}
                    ${alert.confidence ? `
                    <div style="font-size:11px; opacity:0.8; margin-left:20px; margin-top:4px;">
                        🔥 Confidence: ${confidencePercent}%
                    </div>
                    ` : ''}
                </div>
                <div style="display: flex; gap: 6px;">
                    <button onclick="viewAlertOnMap('${alert.id}')" style="
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.4);
                        color: white;
                        padding: 6px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 12px;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                        flex: 1;
                        justify-content: center;
                    " onmouseover="this.style.background='rgba(255,255,255,0.3)'" 
                       onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        <span class="material-icons-round" style="font-size:16px;">map</span>
                        Map
                    </button>
                    ${(alert.imageData || alert.image) ? `
                    <button onclick="viewAlertImage('${alert.id}')" style="
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.4);
                        color: white;
                        padding: 6px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 12px;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                        flex: 1;
                        justify-content: center;
                    " onmouseover="this.style.background='rgba(255,255,255,0.3)'" 
                       onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        <span class="material-icons-round" style="font-size:16px;">photo_camera</span>
                        Image
                    </button>
                    ` : ''}
                    <button onclick="deleteAlert('${alert.id}')" style="
                        background: rgba(255,255,255,0.15);
                        border: 1px solid rgba(255,255,255,0.3);
                        color: white;
                        padding: 6px 10px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 12px;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    " onmouseover="this.style.background='rgba(255,255,255,0.25)'" 
                       onmouseout="this.style.background='rgba(255,255,255,0.15)'"
                       title="Delete this alert">
                        <span class="material-icons-round" style="font-size:16px;">delete</span>
                    </button>
                </div>
            </div>
        `;
    }

    // Display alerts in the sidebar
    function displayAlerts(alerts) {
        const container = document.getElementById('fire-alerts-container');
        const countBadge = document.getElementById('alert-count');
        
        if (!container || !countBadge) return;

        countBadge.textContent = alerts.length;
        
        if (alerts.length === 0) {
            container.innerHTML = '<div style="padding:8px; color:#999; font-size:13px; text-align:center;">No active alerts</div>';
            return;
        }

        // Sort by timestamp (newest first)
        alerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        container.innerHTML = alerts.map(createAlertCard).join('');
    }

    // Add markers to map
    function addMarkersToMap(alerts) {
        // Remove existing markers
        markers.forEach(marker => marker.remove());
        markers = [];

        if (typeof map === 'undefined') return;

        alerts.forEach(alert => {
            // Handle both lat/lon formats
            const lat = alert.location?.latitude || alert.location?.lat;
            const lon = alert.location?.longitude || alert.location?.lon;
            
            if (!lat || !lon) {
                console.log('Skipping alert without location:', alert);
                return;
            }

            const isDrone = alert.source === 'aerial_camera' || alert.device?.includes('Drone');

            // Create a pulsing marker
            const el = document.createElement('div');
            el.className = 'fire-alert-marker';
            el.innerHTML = `
                <div style="
                    width: ${isDrone ? '36px' : '30px'};
                    height: ${isDrone ? '36px' : '30px'};
                    background: radial-gradient(circle, ${isDrone ? '#ff6600' : '#ff4444'} 0%, ${isDrone ? '#cc3300' : '#cc0000'} 70%);
                    border: 3px solid ${isDrone ? '#ffaa00' : 'white'};
                    border-radius: 50%;
                    box-shadow: 0 0 20px rgba(255, 68, 68, 0.6), 0 0 40px rgba(255, 68, 68, 0.4);
                    animation: pulse 2s infinite;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <span class="material-icons-round" style="font-size:${isDrone ? '18px' : '16px'}; color:white;">${isDrone ? 'flight' : 'local_fire_department'}</span>
                </div>
            `;

            // Add CSS animation if not exists
            if (!document.getElementById('fire-marker-animation')) {
                const style = document.createElement('style');
                style.id = 'fire-marker-animation';
                style.textContent = `
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); opacity: 1; }
                        50% { transform: scale(1.2); opacity: 0.8; }
                    }
                `;
                document.head.appendChild(style);
            }

            const marker = new maplibregl.Marker({element: el})
                .setLngLat([lon, lat])
                .setPopup(new maplibregl.Popup({offset: 25})
                    .setHTML(`
                        <div style="padding:8px; background:white; color:#333;">
                            <strong style="color:${isDrone ? '#ff6600' : '#ff4444'};">${isDrone ? '🚁' : '🔥'} ${isDrone ? 'Drone' : 'AI'} Fire Detection Alert</strong>
                            <div style="margin-top:8px; font-size:13px; color:#333;">
                                <div style="color:#333;"><strong>Time:</strong> ${new Date(alert.timestamp).toLocaleString()}</div>
                                ${alert.confidence ? `<div style="color:#333;"><strong>Confidence:</strong> ${(alert.confidence * 100).toFixed(1)}%</div>` : ''}
                                ${alert.location.city ? `<div style="color:#333;"><strong>Location:</strong> ${alert.location.city}${alert.location.state ? ', ' + alert.location.state : ''}</div>` : ''}
                                <div style="color:#333;"><strong>Coordinates:</strong> ${lat.toFixed(6)}, ${lon.toFixed(6)}</div>
                                ${alert.location.altitude ? `<div style="color:#333;"><strong>Altitude:</strong> ${alert.location.altitude.toFixed(1)}m</div>` : ''}
                                ${alert.device ? `<div style="color:#333;"><strong>Device:</strong> ${alert.device}</div>` : ''}
                                ${(alert.imageData || alert.image) ? `<img src="${(alert.imageData || alert.image).startsWith('data:') ? (alert.imageData || alert.image) : 'data:image/jpeg;base64,' + (alert.imageData || alert.image)}" style="width:100%; margin-top:8px; border-radius:4px;" onerror="this.style.display='none'" />` : ''}
                            </div>
                        </div>
                    `))
                .addTo(map);

            markers.push(marker);
        });
    }

    // View alert on map
    window.viewAlertOnMap = function(alertId) {
        const alert = alertsCache.find(a => a.id === alertId);
        if (!alert || !alert.location) {
            console.error('Alert not found or missing location:', alertId, alert);
            return;
        }
        
        const lat = alert.location.latitude || alert.location.lat;
        const lon = alert.location.longitude || alert.location.lon;
        
        console.log('Navigating to alert:', alertId, 'Coordinates:', lat, lon, 'Full alert:', alert);
        
        if (!lat || !lon) {
            console.error('Alert missing coordinates:', alertId, alert.location);
            alert('Location coordinates not available for this alert.');
            return;
        }
        
        if (typeof map !== 'undefined') {
            map.flyTo({
                center: [lon, lat],
                zoom: 15,
                duration: 2000
            });

            // Find and open the marker popup
            setTimeout(() => {
                const marker = markers.find(m => {
                    const lngLat = m.getLngLat();
                    return Math.abs(lngLat.lat - lat) < 0.0001 && 
                           Math.abs(lngLat.lng - lon) < 0.0001;
                });
                
                if (marker) {
                    marker.togglePopup();
                }
            }, 2100);
        }
    };

    // View alert image in modal
    window.viewAlertImage = async function(alertId) {
        let alert = alertsCache.find(a => a.id === alertId);
        let imageData = alert?.imageData || alert?.image;
        
        // If no image data, fetch full alert from server
        if (!alert || !imageData || imageData === 'available') {
            try {
                const response = await fetch(`/api/fire-alert/${alertId}`);
                if (response.ok) {
                    const data = await response.json();
                    alert = data.alert;
                    imageData = alert?.imageData || alert?.image;
                }
            } catch (error) {
                console.error('Error fetching alert:', error);
            }
        }
        
        if (!alert || !imageData || imageData === 'available') {
            console.error('Alert image not found:', alertId);
            alert('Image not available for this alert.');
            return;
        }

        // Create modal if it doesn't exist
        let modal = document.getElementById('fire-alert-image-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'fire-alert-image-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                z-index: 10000;
                display: none;
                justify-content: center;
                align-items: center;
                padding: 20px;
            `;
            modal.innerHTML = `
                <div style="position: relative; max-width: 90%; max-height: 90%; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
                    <div style="background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); color: white; padding: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; font-size: 18px; display: flex; align-items: center; gap: 8px;">
                                <span class="material-icons-round">local_fire_department</span>
                                Fire Detection Image
                            </h3>
                            <p id="modal-alert-info" style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.95;"></p>
                        </div>
                        <button onclick="closeImageModal()" style="background: rgba(255,255,255,0.2); border: none; color: white; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                            <span class="material-icons-round">close</span>
                        </button>
                    </div>
                    <div style="padding: 20px; max-height: calc(90vh - 200px); overflow: auto; display: flex; justify-content: center; align-items: center;">
                        <img id="modal-alert-image" style="max-width: 100%; max-height: 70vh; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" />
                    </div>
                    <div style="padding: 16px; background: #f5f5f5; display: flex; justify-content: center; align-items: center; gap: 12px;">
                        <button onclick="downloadAlertImage()" style="background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; font-weight: 500; min-width: 160px;" onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">
                            <span class="material-icons-round" style="font-size:20px;">download</span>
                            Download Image
                        </button>
                        <button onclick="closeImageModal()" style="background: #666; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 500; min-width: 100px;" onmouseover="this.style.background='#555'" onmouseout="this.style.background='#666'">
                            Close
                        </button>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Close on background click
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeImageModal();
                }
            });

            // Close on Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && modal.style.display === 'flex') {
                    closeImageModal();
                }
            });
        }

        // Update modal content
        const img = document.getElementById('modal-alert-image');
        const info = document.getElementById('modal-alert-info');
        
        // Handle base64 image data with or without prefix
        const imgSrc = imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`;
        img.src = imgSrc;
        
        const locationText = alert.location ? 
            `${alert.location.city || ''}, ${alert.location.state || ''}, ${alert.location.country || ''}`.replace(/^,\s*|,\s*$/g, '').replace(/,\s*,/g, ',') :
            'Location unavailable';
        
        info.innerHTML = `
            📍 ${locationText} • 🕒 ${new Date(alert.timestamp).toLocaleString()}
        `;

        // Store current alert for download
        window.currentAlertImage = alert;

        // Show modal
        modal.style.display = 'flex';
    };

    // Close image modal
    window.closeImageModal = function() {
        const modal = document.getElementById('fire-alert-image-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    };

    // Download alert image
    window.downloadAlertImage = function() {
        if (!window.currentAlertImage) return;
        
        const alert = window.currentAlertImage;
        const imageData = alert.imageData || alert.image;
        const imgSrc = imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`;
        const link = document.createElement('a');
        link.href = imgSrc;
        link.download = `fire_alert_${alert.id}_${new Date(alert.timestamp).getTime()}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Clear all alerts
    window.clearAllAlerts = async function() {
        if (!confirm('Are you sure you want to clear all fire alerts?')) {
            return;
        }

        try {
            const response = await fetch('/api/fire-alerts', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Cleared ${data.count} alerts`);
                
                // Clear local cache and UI
                alertsCache = [];
                displayAlerts([]);
                markers.forEach(marker => marker.remove());
                markers = [];
                
                // Show success message
                const container = document.getElementById('fire-alerts-container');
                if (container) {
                    container.innerHTML = '<div style="padding:8px; color:#4CAF50; font-size:13px; text-align:center;">✓ All alerts cleared</div>';
                    setTimeout(() => {
                        container.innerHTML = '<div style="padding:8px; color:#999; font-size:13px; text-align:center;">No active alerts</div>';
                    }, 2000);
                }
            } else {
                console.error('Failed to clear alerts:', response.statusText);
                alert('Failed to clear alerts. Please try again.');
            }
        } catch (error) {
            console.error('Error clearing alerts:', error);
            alert('Error clearing alerts. Please try again.');
        }
    };

    // Delete single alert
    window.deleteAlert = async function(alertId) {
        if (!confirm('Are you sure you want to delete this alert?')) {
            return;
        }

        try {
            const response = await fetch(`/api/fire-alert/${alertId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                console.log(`✅ Deleted alert ${alertId}`);
                
                // Remove from cache
                alertsCache = alertsCache.filter(a => a.id !== alertId);
                
                // Update display
                displayAlerts(alertsCache);
                
                // Remove marker
                const alert = alertsCache.find(a => a.id === alertId);
                if (alert) {
                    const lat = alert.location?.latitude || alert.location?.lat;
                    const lon = alert.location?.longitude || alert.location?.lon;
                    if (lat && lon) {
                        const markerIndex = markers.findIndex(m => {
                            const lngLat = m.getLngLat();
                            return Math.abs(lngLat.lat - lat) < 0.0001 && 
                                   Math.abs(lngLat.lng - lon) < 0.0001;
                        });
                        if (markerIndex !== -1) {
                            markers[markerIndex].remove();
                            markers.splice(markerIndex, 1);
                        }
                    }
                }
                
                // Refresh to ensure sync
                setTimeout(() => updateAlerts(), 500);
            } else {
                console.error('Failed to delete alert:', response.statusText);
                alert('Failed to delete alert. Please try again.');
            }
        } catch (error) {
            console.error('Error deleting alert:', error);
            alert('Error deleting alert. Please try again.');
        }
    };

    // Update alerts
    async function updateAlerts() {
        const alerts = await fetchFireAlerts();
        if (JSON.stringify(alerts) !== JSON.stringify(alertsCache)) {
            alertsCache = alerts;
            displayAlerts(alerts);
            addMarkersToMap(alerts);
        }
    }

    // Initialize when map is ready
    function initFireAlerts() {
        if (typeof map === 'undefined') {
            setTimeout(initFireAlerts, 500);
            return;
        }
        
        // Initial fetch
        updateAlerts();
        
        // Set up periodic refresh
        setInterval(updateAlerts, REFRESH_INTERVAL);
        
        console.log('🔥 Fire Alerts module initialized');
    }

    // Start initialization
    initFireAlerts();
})();
