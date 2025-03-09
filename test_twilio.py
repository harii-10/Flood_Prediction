from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get credentials from environment
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')
to_number = os.getenv('TO_PHONE_NUMBER')

try:
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Send a test message
    message = client.messages.create(
        body="This is a test message from your Flood Prediction System",
        from_=from_number,
        to=to_number
    )
    
    print(f"Message sent! SID: {message.sid}")
    print(f"Status: {message.status}")

except Exception as e:
    print(f"Error: {str(e)}") 