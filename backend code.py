from flask import Flask, request, jsonify
import math
import pyttsx3
import requests
import time

app = Flask(__name__)
#idher json upload kkar sakte ho agar jyada zones add karne ho to
heat_zones = [
    {"zone_id": 1, "highway": "NH-19", "district": "Varanasi", "lat": 25.3176, "lon": 82.9739, "radius_km": 3},
    {"zone_id": 2, "highway": "NH-27", "district": "Lucknow", "lat": 26.8467, "lon": 80.9462, "radius_km": 4},
    {"zone_id": 3, "highway": "NH-30", "district": "Prayagraj", "lat": 25.4358, "lon": 81.8463, "radius_km": 2},
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))
    
def speak_alert(message):  #Namita,Mansi,Dheeru,Yash yaha koi suggestion ho to dena
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        print("TTS Error:", e)

@app.route("/check", methods=["POST"])
def check_zone():
    data = request.json
    lat, lon = data.get("lat"), data.get("lon")

    if lat is None or lon is None:
        return jsonify({"alert": False, "message": "No coordinates provided"}), 400

    for zone in heat_zones:
        dist = haversine(lat, lon, zone["lat"], zone["lon"])
        if dist <= zone["radius_km"]:
            alert_message = f"Slow down! Wildlife zone ahead near {zone['district']} on {zone['highway']}."
            speak_alert(alert_message)  # voice alert chan kar lena agar krna ho to
            return jsonify({"alert": True, "message": alert_message, "distance_km": round(dist, 2), "zone": zone})

    return jsonify({"alert": False, "message": "Safe zone. No wildlife area nearby."})

#client side me kuch update karna ho to batana
def test_client():
    time.sleep(3)  #waiting for svr
    url = "http://127.0.0.1:5000/check"
    test_data = {"lat": 26.8467, "lon": 80.9462}
    try:
        response = requests.post(url, json=test_data) 
        print("\n--- Test Client Output ---")
        print(response.json())
        print("--------------------------\n")
    except Exception as e:      #error handling bhi ho sakta hai
        print("Client error:", e)

if __name__ == "__main__":
    # Run test client after server starts
    from threading import Thread
    Thread(target=test_client, daemon=True).start() #ye threaing h Dheeru iska kaam hai ki server start hone ke baad client bhi run ho jaye
    app.run(debug=True) #iska kaam hai ki server ko debug mode me run karna