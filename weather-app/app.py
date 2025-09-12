from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# 🔑 Replace this with your actual OpenWeatherMap API key
API_KEY = "YOUR_API_KEY"

@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")

@app.route("/weather/<city>")
def get_data(city):
    """
    Fetch weather data for a given city from OpenWeatherMap API.
    Returns formatted JSON on success or error message with status code on failure.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        # Send request to OpenWeatherMap
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()

        # Format response with only required fields
        weather_data = {
            "city": data["name"],
            "temperature": f"{data['main']['temp']}°C",
            "condition": data["weather"][0]["description"],
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed": f"{data['wind']['speed']} km/h",
            "icon": data["weather"][0]["icon"]
        }
        return jsonify(weather_data)

    except requests.exceptions.HTTPError:
        # Handle specific HTTP status codes
        if res.status_code == 404:
            return jsonify({"error": "Error 404: Page Not Found", "status": 404}), 404
        elif res.status_code == 401:
            return jsonify({"error": "Invalid API key", "status": 401}), 401
        else:
            return jsonify({"error": "API returned an error", "status": res.status_code}), res.status_code

    except requests.exceptions.RequestException:
        # Catch network issues, timeouts, etc.
        return jsonify({"error": "Network Error", "status": 500}), 500

if __name__ == "__main__":
    # Debug mode for development only (not for production!)
    app.run(debug=True)