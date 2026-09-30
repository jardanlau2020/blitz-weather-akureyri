import os, time, threading, requests
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
CITY = os.environ.get("CITY", "Akureyri")
LAT = float(os.environ.get("LAT", "65.6835"))
LON = float(os.environ.get("LON", "-18.1002"))
TZ = os.environ.get("TZ", "Atlantic/Reykjavik")
WORKER_URL = os.environ.get("WORKER_URL", "https://weather-push.jardanlau-e4b.workers.dev/weather")

latest_weather = {"temp": "--", "desc": "Initializing", "ts": 0}

def fetch_weather():
    global latest_weather
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone={TZ}"
    try:
        r = requests.get(url, timeout=15).json()
        curr = r.get("current", {})
        temp = curr.get("temperature_2m")
        hum = curr.get("relative_humidity_2m")
        wind = curr.get("wind_speed_10m")
        w_data = {
            "platform": "blitz-oodd",
            "city": CITY,
            "flag": "🇮🇸",
            "name": "Blitz oodd",
            "temp": str(temp),
            "desc": "Weather",
            "humidity": str(hum),
            "wind": str(wind),
            "rain": "0",
            "source": "Open-Meteo",
            "ts": int(time.time())
        }
        latest_weather = w_data
        print(f"[Weather] Fetched {CITY}: {temp}°C")
        try:
            pr = requests.post(WORKER_URL, json=w_data, timeout=15)
            print(f"[Weather] Posted to worker: {pr.status_code}")
        except Exception as pe:
            print(f"[Weather] Worker post error: {pe}")
    except Exception as e:
        print(f"[Weather] Fetch error: {e}")

def loop():
    while True:
        fetch_weather()
        time.sleep(300)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"akureyri-weather"}')
        elif self.path in ["/weather", "/weather/today"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            import json
            self.wfile.write(json.dumps(latest_weather).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Akureyri Weather Node (blitz.cloud oodd)")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server started on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    run_server()
