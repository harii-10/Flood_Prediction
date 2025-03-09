from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
to_phone = os.getenv('TO_PHONE_NUMBER')

# Initialize Twilio client
client = Client(account_sid, auth_token)

print(f"\nChecking verification status for {to_phone}")

# Get list of verified numbers
verified_numbers = client.outgoing_caller_ids.list()
verified_phones = [number.phone_number for number in verified_numbers]

if to_phone in verified_phones:
    print(f"✅ {to_phone} is verified")
else:
    print(f"❌ {to_phone} is not verified")
    print("\nVerified numbers in your account:")
    for phone in verified_phones:
        print(f"- {phone}")
    
    print("\nTo verify this number:")
    try:
        validation_request = client.validation_requests.create(
            friendly_name='New Number',
            phone_number=to_phone
        )
        print(f"Validation request sent. Check your phone for a code.")
    except Exception as e:
        print(f"Error sending validation request: {str(e)}") 