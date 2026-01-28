import os
from flask import Flask, jsonify, send_from_directory, request
import requests
from dotenv import load_dotenv
from flask_cors import CORS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
CORS(app)


def get_env(name, default=""):
    value = os.environ.get(name, default)
    return value if value is not None else ""


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/config")
def config():
    return jsonify(
        {
            "FIRMS_MAP_KEY": get_env("FIRMS_MAP_KEY"),
            "FIRMS_WMS_URL": get_env("FIRMS_WMS_URL", "https://firms.modaps.eosdis.nasa.gov/wms/"),
            "ENABLE_FIRMS_WMS": get_env("ENABLE_FIRMS_WMS", "false"),
            "FIRMS_DAYS_DEFAULT": int(get_env("FIRMS_DAYS_DEFAULT", "1")),
            "FIRMS_DAYS_MAX": 5,
            "OPENWEATHER_KEY": get_env("OPENWEATHER_KEY"),
            "DEFAULT_CENTER": [75, 20],
            "DEFAULT_ZOOM": 2,
            "SENTINEL_WMS_URL": get_env("SENTINEL_WMS_URL", "https://tiles.maps.eox.at/wms"),
        }
    )


@app.get("/firms/area")
def firms_area():
    api_key = get_env("FIRMS_MAP_KEY")
    if not api_key:
        return jsonify({"error": "FIRMS_MAP_KEY not configured"}), 400

    source = request.args.get("source")
    west = request.args.get("west")
    south = request.args.get("south")
    east = request.args.get("east")
    north = request.args.get("north")
    days = request.args.get("days", "1")

    if not all([source, west, south, east, north]):
        return jsonify({"error": "Missing required query params"}), 400

    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/{source}/{west},{south},{east},{north}/{days}"
    try:
        resp = requests.get(url, timeout=20)
    except requests.RequestException as exc:
        return jsonify({"error": "FIRMS request failed", "details": str(exc)}), 502

    if resp.status_code != 200:
        return jsonify({"error": "FIRMS request failed", "status": resp.status_code, "details": resp.text[:500]}), 502

    return resp.text, 200, {"Content-Type": "text/csv; charset=utf-8"}


@app.get("/firms/wms")
@app.get("/firms/wms/")
def firms_wms():
    api_key = get_env("FIRMS_MAP_KEY")
    if not api_key:
        return jsonify({"error": "FIRMS_MAP_KEY not configured"}), 400

    layers = request.args.get("layers")
    bbox = request.args.get("bbox")
    if not layers or not bbox:
        return jsonify({"error": "Missing required query params"}), 400

    params = {
        "service": request.args.get("service", "WMS"),
        "request": request.args.get("request", "GetMap"),
        "version": request.args.get("version", "1.1.1"),
        "styles": request.args.get("styles", ""),
        "format": request.args.get("format", "image/png"),
        "transparent": request.args.get("transparent", "true"),
        "height": request.args.get("height", "256"),
        "width": request.args.get("width", "256"),
        "srs": request.args.get("srs", "EPSG:3857"),
        "layers": layers,
        "bbox": bbox,
        "key": api_key,
    }

    try:
        resp = requests.get("https://firms.modaps.eosdis.nasa.gov/wms/", params=params, timeout=30)
    except requests.RequestException as exc:
        return jsonify({"error": "FIRMS WMS request failed", "details": str(exc)}), 502

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    return resp.content, resp.status_code, {"Content-Type": content_type}


@app.get("/sentinelhub/token")
def sentinelhub_token():
    client_id = get_env("SENTINELHUB_CLIENT_ID")
    client_secret = get_env("SENTINELHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        return jsonify({"error": "Sentinel Hub credentials not configured"}), 400

    token_url = "https://services.sentinel-hub.com/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(token_url, data=data, timeout=20)
    if response.status_code != 200:
        return jsonify({"error": "Token request failed", "details": response.text}), 502

    return jsonify(response.json())


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


# Fire Alert Storage
fire_alerts = []

@app.post("/api/fire-alert")
def receive_fire_alert():
    """Receive fire detection from webcam AI"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    alert = {
        "id": str(len(fire_alerts) + 1),
        "type": data.get("type"),
        "confidence": data.get("confidence"),
        "location": data.get("location"),
        "timestamp": data.get("timestamp"),
        "bbox": data.get("bbox"),
        "imageData": data.get("image"),
        "receivedAt": data.get("timestamp")
    }
    fire_alerts.insert(0, alert)
    if len(fire_alerts) > 100:
        fire_alerts.pop()
    
    print(f"🔥 Fire alert received from {alert['location'].get('city', 'Unknown')}")
    return jsonify({"success": True, "message": "Fire alert received", "alertId": alert["id"]})

@app.get("/api/fire-alerts")
def get_fire_alerts():
    """Get all fire alerts"""
    limit = int(request.args.get("limit", 50))
    include_images = request.args.get("includeImages") == "true"
    
    alerts = fire_alerts[:limit]
    if not include_images:
        alerts = [{**a, "imageData": "available" if a.get("imageData") else None} for a in alerts]
    
    return jsonify({"success": True, "count": len(alerts), "total": len(fire_alerts), "alerts": alerts})

@app.get("/api/fire-alert/<alert_id>")
def get_single_alert(alert_id):
    """Get specific alert with image"""
    alert = next((a for a in fire_alerts if a["id"] == alert_id), None)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"success": True, "alert": alert})

@app.delete("/api/fire-alerts")
def clear_all_alerts():
    """Clear all fire alerts"""
    global fire_alerts
    count = len(fire_alerts)
    fire_alerts.clear()
    print(f"🗑️ Cleared {count} fire alerts")
    return jsonify({"success": True, "message": f"Cleared {count} alerts", "count": count})

@app.delete("/api/fire-alert/<alert_id>")
def delete_alert(alert_id):
    """Delete specific fire alert"""
    global fire_alerts
    alert = next((a for a in fire_alerts if a["id"] == alert_id), None)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    fire_alerts.remove(alert)
    print(f"🗑️ Deleted alert {alert_id}")
    return jsonify({"success": True, "message": "Alert deleted"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
