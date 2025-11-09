import json
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
"""
Email CSV weather data script for WeatherLink data logger.
Sends the weather_data.csv file as an attachment to multiple recipients.
Use with crontab to send reports at desired intervals:
# Daily email at 8 PM
0 20 * * * /usr/bin/python3 /path/to/email_csv.py
# Weekly email every Monday at 9 AM
0 9 * * 1 /usr/bin/python3 /path/to/email_csv.py
# Every morning at 7 AM
0 7 * * * /usr/bin/python3 /path/to/email_csv.py
"""
# Email Configuration

with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)   


SENDER_EMAIL = config["email"]["sender_email"]
SENDER_PASSWORD = config["email"]["sender_password"]  # Use app-specific password for Gmail
RECIPIENT_EMAIL = config["email"]["recipient_email"]
SMTP_SERVER = config["email"]["smtp_server"]
SMTP_PORT = config["email"]["smtp_port"]
# Log file path
CSV_LOG = os.path.join(os.path.dirname(__file__), "weather_data.csv")

def send_csv_email():
	"""Send the CSV log file via email to all recipients"""
	if not os.path.isfile(CSV_LOG):
		print(f"Error: {CSV_LOG} not found")
		return False
	
	try:
		# Connect to SMTP server once
		print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
		server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
		server.starttls()
		server.login(SENDER_EMAIL, SENDER_PASSWORD)
		
		# Loop through all recipients
		for recipient in RECIPIENT_EMAIL:
			# Create message
			message = MIMEMultipart()
			message["Subject"] = f"Weather Data Report - {datetime.now().strftime('%Y-%m-%d')}"
			message["From"] = SENDER_EMAIL
			message["To"] = recipient
			
			# Add text body
			body = f"""
Hi,

Please find attached your weather data log from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

This file contains all recorded weather measurements including:
- Temperature
- Humidity
- Dew Point
- Heat Index
- Particulate Matter (PM1, PM2.5, PM10)
- Air Quality Index (AQI)

Best regards,
Your Weather Logger
			"""
			message.attach(MIMEText(body, "plain"))
			
			# Attach CSV file
			with open(CSV_LOG, 'rb') as attachment:
				part = MIMEBase("application", "octet-stream")
				part.set_payload(attachment.read())
				encoders.encode_base64(part)
				part.add_header("Content-Disposition", f"attachment; filename= {CSV_LOG}")
				message.attach(part)
			
			# Send email to this recipient
			server.sendmail(SENDER_EMAIL, recipient, message.as_string())
			print(f"✓ Email sent successfully to {recipient}")
		
		server.quit()
		print(f"✓ All emails sent with attachment: {CSV_LOG}")
		return True
		
	except smtplib.SMTPAuthenticationError:
		print("✗ Error: Invalid email or password. Check your credentials.")
		print("  For Gmail, use an app-specific password: https://support.google.com/accounts/answer/185833")
		return False
	except smtplib.SMTPException as e:
		print(f"✗ SMTP error occurred: {e}")
		return False
	except Exception as e:
		print(f"✗ Error sending email: {e}")
		return False

if __name__ == "__main__":
	if SENDER_EMAIL == "your_email@gmail.com":
		print("Error: Please configure SENDER_EMAIL and SENDER_PASSWORD")
		print("Instructions:")
		print("1. Update SENDER_EMAIL with your Gmail address")
		print("2. Generate an app-specific password at: https://support.google.com/accounts/answer/185833")
		print("3. Update SENDER_PASSWORD with the generated password")
		print("4. Update RECIPIENT_EMAIL with a list of destination emails")
	else:
		send_csv_email()