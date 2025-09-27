from flask import Flask, request, jsonify, render_template_string
import math
import pyttsx3
import threading

# Initialize Flask application
app = Flask(__name__)

# --------------------------
# Wildlife zones data
# --------------------------
# Define critical wildlife crossing zones with coordinates and effective radii (in km)
heat_zones = [
    {"zone_id": 1, "highway": "NH-19", "district": "Varanasi", "lat": 25.3176, "lon": 82.9739, "radius_km": 3},
    {"zone_id": 2, "highway": "NH-27", "district": "Lucknow", "lat": 26.8467, "lon": 80.9462, "radius_km": 4},
    {"zone_id": 3, "highway": "NH-30", "district": "Prayagraj", "lat": 25.4358, "lon": 81.8463, "radius_km": 2},
]

# --------------------------
# Haversine formula
# --------------------------
# Calculates the distance between two points on the Earth's surface using their latitude and longitude.
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance (in km) between two geographical points.
    """
    R = 6371  # Radius of Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
         
    return R * 2 * math.asin(math.sqrt(a))

# --------------------------
# Voice alerts (Server-side - used for testing/local host machine)
# --------------------------
def speak_alert(message):
    """Starts a non-blocking thread to generate a voice alert using pyttsx3."""
    # NOTE: This alert is only heard on the server machine, not the client's browser.
    # The browser handles its own TTS (SpeechSynthesis API).
    threading.Thread(target=_speak_thread, args=(message,), daemon=True).start()

def _speak_thread(message):
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        print("TTS Error (Server):", e)

# --------------------------
# API Endpoint: /check
# --------------------------
@app.route("/check", methods=["POST"])
def check_zone():
    """
    Checks if the received coordinates (lat, lon) are within any defined wildlife zone.
    Returns JSON with alert status and nearest distance.
    """
    data = request.json
    lat, lon = data.get("lat"), data.get("lon")
    
    if lat is None or lon is None:
        return jsonify({"alert": False, "message": "No coordinates provided"}), 400

    # Iterate through all zones to check proximity
    for zone in heat_zones:
        dist = haversine(lat, lon, zone["lat"], zone["lon"])
        
        if dist <= zone["radius_km"]:
            # User is within the alert radius
            msg = f"⚠️ Slow down! Wildlife zone ahead near {zone['district']} on {zone['highway']}."
            # Server-side alert (for host machine)
            speak_alert(msg) 
            
            return jsonify({
                "alert": True,
                "message": msg,
                "distance_km": round(dist, 2),
                "zone": zone,
                "zones": heat_zones
            })

    # If no immediate alert, find the nearest zone distance
    nearest = min([haversine(lat, lon, z["lat"], z["lon"]) for z in heat_zones])
    
    return jsonify({
        "alert": False,
        "message": f"✅ Safe zone. Nearest wildlife zone {round(nearest, 2)} km away.",
        "nearest_distance_km": round(nearest, 2),
        "zones": heat_zones
    })

# --------------------------
# Frontend HTML + Leaflet map (using manual input)
# --------------------------
# The single-page web interface to display the map and handle location checking
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wildlife Alert AI (Manual Test)</title>
    <!-- Load Leaflet CSS for map styling -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom CSS for visual appeal */
        body { font-family: Inter, sans-serif; background-color: #f4f7f9; }
        #map { height: 60vh; width: 100%; border-radius: 0 0 1rem 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        #info { padding: 1.5rem; background-color: #ffffff; border-radius: 1rem 1rem 0 0; }
        #alert { font-weight: 700; color: #b91c1c; font-size: 1.25rem; margin-top: 10px; }
        #risk { font-weight: 600; margin-top: 5px; color: #4b5563; }
        button { 
            background-color: #10b981; 
            color: white; 
            padding: 12px 24px; 
            border-radius: 0.5rem; 
            font-size: 1rem; 
            font-weight: bold; 
            transition: background-color 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.5);
            margin-bottom: 10px;
        }
        button:hover { background-color: #059669; }
        .leaflet-container { background: #f4f7f9; }
        input { border: 1px solid #d1d5db; }
        .input-group { display: flex; gap: 1rem; margin-bottom: 1rem; }
        @media (max-width: 640px) {
            .input-group { flex-direction: column; }
        }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center">
    <div class="max-w-4xl w-full">
        <div id="info">
            <h1 class="text-3xl font-extrabold text-gray-800 mb-2">Wildlife Zone AI Alert (Manual Test) 🚗🦌</h1>
            <p class="text-gray-600 mb-4">Enter coordinates below to check if you are within a wildlife zone. Try Lat: 25.31, Lon: 82.97 for an alert.</p>
            
            <div class="input-group">
                <input type="number" id="manualLat" placeholder="Enter Latitude (e.g., 25.317)" value="25.317" class="p-2 border rounded shadow-sm flex-grow focus:ring-green-500 focus:border-green-500">
                <input type="number" id="manualLon" placeholder="Enter Longitude (e.g., 82.973)" value="82.973" class="p-2 border rounded shadow-sm flex-grow focus:ring-green-500 focus:border-green-500">
            </div>

            <button onclick="checkManualLocation()">Check Location</button>
            
            <div id="status" class="text-sm text-gray-500 mt-2">Enter coordinates and press Check.</div>
            <div id="alert" class="mt-3 p-3 bg-red-50 border-l-4 border-red-500 rounded text-red-700 hidden"></div>
            <div id="risk" class="mt-2 p-2 bg-green-50 border-l-4 border-green-500 rounded text-green-700">Awaiting location data...</div>
        </div>
        <div id="map"></div>
    </div>

    <!-- Load Leaflet JavaScript library -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Set up the Leaflet map, centered roughly over the zone area
        let map = L.map('map').setView([25.3176, 82.9739], 6);
        let lastAlert = null;
        let userMarker = null;
        let zoneMarkers = [];

        // Add the standard OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        function speak(text) {
            /** Uses the browser's Web Speech API to speak the alert message. */
            if ('speechSynthesis' in window) {
                // Ensure text is only spoken once per alert change
                if (text === lastAlert) return; 
                
                // Cancel any pending speech before starting a new one
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.pitch = 1.0;
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
                lastAlert = text;
            }
        }

        async function checkManualLocation() {
            const latInput = document.getElementById("manualLat").value;
            const lonInput = document.getElementById("manualLon").value;
            const lat = parseFloat(latInput);
            const lon = parseFloat(lonInput);

            if (isNaN(lat) || isNaN(lon)) {
                document.getElementById("status").innerText = "Please enter valid numeric latitude and longitude.";
                return;
            }

            document.getElementById("status").innerText = `Checking location: Lat ${lat.toFixed(5)}, Lon ${lon.toFixed(5)}`;

            // 1. Update User Marker and Map View
            if (!userMarker) {
                // Create marker and center map the first time
                userMarker = L.marker([lat, lon], {
                    title: "You",
                    icon: L.divIcon({
                        className: 'user-marker',
                        html: '<div style="background-color:#10b981; width:20px; height:20px; border-radius:50%; border: 3px solid white;"></div>'
                    })
                }).addTo(map);
                map.setView([lat, lon], 12);
            } else { 
                // Move existing marker and update view
                userMarker.setLatLng([lat, lon]); 
                map.setView([lat, lon]);
            }

            // 2. Call the Flask API endpoint
            try {
                const response = await fetch("/check", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({lat: lat, lon: lon})
                });
                const data = await response.json();

                // 3. Handle Alert and UI Update
                const alertDiv = document.getElementById("alert");
                const riskDiv = document.getElementById("risk");

                if (data.alert) {
                    alertDiv.innerText = data.message;
                    alertDiv.classList.remove("hidden");
                    riskDiv.classList.add("bg-red-100", "text-red-800");
                    riskDiv.classList.remove("bg-green-50", "text-green-700");
                    riskDiv.innerText = `🚨 Risk Level: HIGH | Distance to Zone: ${data.distance_km} km`;

                    // Trigger browser-side voice alert
                    speak(data.message);
                } else { 
                    alertDiv.classList.add("hidden"); 
                    riskDiv.classList.remove("bg-red-100", "text-red-800");
                    riskDiv.classList.add("bg-green-50", "text-green-700");
                    riskDiv.innerText = `✅ Risk Level: LOW | Nearest Wildlife Zone: ${data.nearest_distance_km} km`;
                    lastAlert = null; // Clear last alert so a new one is spoken upon entering a zone
                }

                // 4. Draw/Redraw Zone Circles on the map
                zoneMarkers.forEach(m => map.removeLayer(m));
                zoneMarkers = [];
                
                data.zones.forEach(z => {
                    const color = data.alert && data.zone.zone_id === z.zone_id ? '#b91c1c' : '#f59e0b'; // Highlight current zone
                    const marker = L.circle([z.lat, z.lon], {
                        color: color, 
                        fillColor: color, 
                        fillOpacity: 0.2, 
                        radius: z.radius_km * 1000 // Leaflet uses meters
                    }).addTo(map).bindPopup(`<b>${z.district} Zone</b><br>Highway: ${z.highway}<br>Radius: ${z.radius_km} km`);
                    zoneMarkers.push(marker);
                });
            } catch (error) {
                console.error("API check failed:", error);
                document.getElementById("status").innerText = "Error communicating with server. Check server console.";
            }
        }

        // Initial drawing of zones when the map loads (using hardcoded zones)
        // This makes sure the zones are visible before the first manual check
        const initialZones = [
            {"zone_id": 1, "highway": "NH-19", "district": "Varanasi", "lat": 25.3176, "lon": 82.9739, "radius_km": 3},
            {"zone_id": 2, "highway": "NH-27", "district": "Lucknow", "lat": 26.8467, "lon": 80.9462, "radius_km": 4},
            {"zone_id": 3, "highway": "NH-30", "district": "Prayagraj", "lat": 25.4358, "lon": 81.8463, "radius_km": 2},
        ];

        initialZones.forEach(z => {
            const marker = L.circle([z.lat, z.lon], {
                color: '#f59e0b', 
                fillColor: '#f59e0b', 
                fillOpacity: 0.2, 
                radius: z.radius_km * 1000 
            }).addTo(map).bindPopup(`<b>${z.district} Zone</b><br>Highway: ${z.highway}<br>Radius: ${z.radius_km} km`);
            zoneMarkers.push(marker);
        });

    </script>
</body>
</html>
"""

@app.route("/")
def home():
    """Renders the main HTML page with the map and manual location input logic."""
    return render_template_string(HTML_PAGE)

# --------------------------
# Run app
# --------------------------
if __name__ == "__main__":
    # Run the Flask app accessible from any device on the local network (LAN)
    print("--- WILDLIFE ALERT AI MANUAL TEST SERVER STARTING ---")
    print("ACTION REQUIRED: Open http://<your-PC-LAN-IP>:5000 on your browser.")
    print("Test coordinates in the UI: Try 25.317, 82.973 (Alert) or 20.0, 75.0 (Safe)")
    # Use host="0.0.0.0" to make it externally visible on the network
    app.run(host="0.0.0.0", port=5000, debug=True)
