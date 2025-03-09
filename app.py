from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
import joblib
import numpy as np
import os
import sqlite3
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS

API_KEY = "a9081f1dc1add86132518acf611db96f"
LAT, LON = "9.4533", "77.8024" 

# Load environment variables
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Add this after loading environment variables to debug
print("Twilio Configuration:")
print(f"Account SID starts with: {TWILIO_ACCOUNT_SID[:6]}...")
print(f"Auth Token starts with: {TWILIO_AUTH_TOKEN[:6]}...")
print(f"From Number: {TWILIO_PHONE_NUMBER}")

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

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect("rainfall.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rainfall (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        rainfall REAL
                    )''')
    conn.commit()
    conn.close()

def save_rainfall(rainfall):
    """Save rainfall data to database"""
    conn = sqlite3.connect("rainfall.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rainfall (date, rainfall) VALUES (DATE('now'), ?)", (rainfall,))
    conn.commit()
    conn.close()

def get_weather_data():
    """Fetch real-time weather data and save rainfall"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if "rain" in data:
            rainfall = data["rain"].get("1h", 0)  # Get last 1-hour rainfall
        else:
            rainfall = 0  # No rain reported

        # Save rainfall in the database
        save_rainfall(rainfall)

        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rainfall": rainfall
        }
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
        raise

def get_location_name(lat, lon):
    """Get location name from coordinates using OpenWeatherMap API"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        data = response.json()
        city = data.get('name', 'Unknown City')
        if 'sys' in data:
            country = data['sys'].get('country', '')
            return f"{city}, {country}" if country else city
        return city
    except Exception as e:
        print(f"Error getting location name: {str(e)}")
        return "Unknown Location"

def send_flood_alert(weather_data, prediction):
    """Send SMS alert about flood prediction"""
    try:
        # Reload environment variables to get the latest phone number
        load_dotenv(override=True)
        to_phone = os.getenv('TO_PHONE_NUMBER')
        
        print("\nSMS Debug Information:")
        print(f"Account SID: {TWILIO_ACCOUNT_SID}")
        print(f"From Number: {TWILIO_PHONE_NUMBER}")
        print(f"To Number: {to_phone}")
        print(f"Verification Status: Checking...")
        
        # Check if the number is verified
        try:
            # Get list of verified numbers
            verified_numbers = twilio_client.outgoing_caller_ids.list()
            verified_phones = [number.phone_number for number in verified_numbers]
            
            if to_phone in verified_phones:
                print(f"Phone number {to_phone} is verified")
            else:
                print(f"Warning: {to_phone} is not in verified numbers list")
                print("Verified numbers:", verified_phones)
        except Exception as ve:
            print(f"Error checking verification: {str(ve)}")
        
        # Get location name based on coordinates
        location = get_location_name(LAT, LON)
        
        # Change message based on prediction
        if prediction == "YES":
            message = f"""⚠️ FLOOD ALERT ⚠️
Location: {location}
Temperature: {weather_data['temperature']}°C
Humidity: {weather_data['humidity']}%
Rainfall: {weather_data['rainfall']}mm
Flood Risk: {prediction}

Please take necessary precautions!"""
        else:
            message = f"""🌤️ Weather Update
Location: {location}
Temperature: {weather_data['temperature']}°C
Humidity: {weather_data['humidity']}%
Rainfall: {weather_data['rainfall']}mm
Flood Risk: {prediction}

No flood risk detected at this time."""

        print(f"\nAttempting to send SMS to {to_phone}")
        print(f"Message content:\n{message}")
        
        # Send SMS regardless of prediction
        message_response = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        print(f"\nSMS Response:")
        print(f"Status: {message_response.status}")
        print(f"SID: {message_response.sid}")
        print(f"Error Code: {message_response.error_code}")
        print(f"Error Message: {message_response.error_message}")
        
    except Exception as e:
        print(f"\nDetailed error in send_flood_alert:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
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
        knn_prediction = str(knn_model.predict(features)[0])
        logistic_prediction = str(logistic_model.predict(features)[0])
        
        final_prediction = "YES" if (knn_prediction == "YES" or logistic_prediction == "YES") else "NO"
        
        # Send SMS alert and track success
        try:
            send_flood_alert(weather_data, final_prediction)
            # Get current phone number for status
            current_phone = os.getenv('TO_PHONE_NUMBER')
            sms_status = {"success": True, "number": current_phone}
        except Exception as e:
            sms_status = {"success": False, "error": str(e)}
        
        response_data = {
            "weather": {
                "temperature": float(weather_data["temperature"]),
                "humidity": float(weather_data["humidity"]),
                "rainfall": float(weather_data["rainfall"])
            },
            "knn_prediction": knn_prediction,
            "logistic_prediction": logistic_prediction,
            "final_prediction": final_prediction,
            "sms_status": sms_status  # Add SMS status to response
        }
        print("Response data:", response_data)
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in predict_flood: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_rainfall_data', methods=['GET'])
def get_rainfall_data():
    """API endpoint to get historical rainfall data"""
    try:
        conn = sqlite3.connect("rainfall.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date, rainfall FROM rainfall ORDER BY date ASC")
        rows = cursor.fetchall()
        conn.close()

        data = [{"date": row[0], "rainfall": row[1]} for row in rows]
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching rainfall data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
