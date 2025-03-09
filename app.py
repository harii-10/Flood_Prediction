from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
import joblib
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Enable CORS

API_KEY = "a9081f1dc1add86132518acf611db96f"
LAT, LON = "25.4670", "91.3662" 

# Add error handling for model loading
try:
    # Print current working directory
    print("Current working directory:", os.getcwd())
    print("Checking if model files exist:")
    print("knn_model.pkl exists:", os.path.exists("knn_model.pkl"))
    print("logistic_model.pkl exists:", os.path.exists("logistic_model.pkl"))
    
    # Load trained models
    knn_model = joblib.load("knn_model.pkl")
    logistic_model = joblib.load("logistic_model.pkl")
except Exception as e:
    print(f"Error loading models: {str(e)}")
    raise

def get_weather_data():
    """Fetch real-time weather data"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if "rain" in data:
            rainfall = data["rain"].get("1h", 0)  # Get last 1-hour rainfall
        else:
            rainfall = 0  # No rain reported

        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rainfall": rainfall
        }
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict_flood', methods=['GET'])
def predict_flood():
    try:
        weather_data = get_weather_data()
        print("Weather data received:", weather_data)
        
        features = np.array([[
            weather_data["rainfall"],
            weather_data["temperature"],
            weather_data["humidity"],
            0,  # Feature 4
            0,  # Feature 5
            0,  # Feature 6
            0,  # Feature 7
            0,  # Feature 8
            0,  # Feature 9
            0,  # Feature 10
            0,  # Feature 11
            0,  # Feature 12
            0   # Feature 13
        ]])
        
        print("Features shape:", features.shape)
        print("Features values:", features)

        # Get predictions and convert to standard Python types
        knn_prediction = str(knn_model.predict(features)[0])  # Convert to string
        logistic_prediction = str(logistic_model.predict(features)[0])  # Convert to string
        
        final_prediction = "YES" if (knn_prediction == "YES" or logistic_prediction == "YES") else "NO"
        
        response_data = {
            "weather": {
                "temperature": float(weather_data["temperature"]),  # Convert to float
                "humidity": float(weather_data["humidity"]),       # Convert to float
                "rainfall": float(weather_data["rainfall"])        # Convert to float
            },
            "knn_prediction": knn_prediction,
            "logistic_prediction": logistic_prediction,
            "final_prediction": final_prediction
        }
        print("Response data:", response_data)
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in predict_flood: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
