from flask import Flask, redirect, url_for, request, render_template, jsonify, session
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
import os
# import pyotp
# from flask_mail import Mail, Message
import base64
import mimetypes
from io import BytesIO
from email import message_from_bytes

# Load environment variables
app = Flask(__name__)
CORS(app)

# Set secret key securely
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

#Authentication Layer -1
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER', 'your-email@gmail.com')
# app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS', 'your-email-password')

# mail = Mail(app)

# Use environment variable for client secret file
CLIENT_SECRET_FILE = os.getenv('GOOGLE_CLIENT_SECRET_FILE', r'C:\Users\LENOVO\OneDrive\Documents\Email-Summarizer-Extension\client_secret_817174760885-qkhtkn8ib3uhobfj5ipf34pi60k8pikv.apps.googleusercontent.com.json')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///credentials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define OAuth credentials model
class OAuthCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500), nullable=True)
    token_uri = db.Column(db.String(500))
    client_id = db.Column(db.String(500))
    client_secret = db.Column(db.String(500))
    scopes = db.Column(db.String(500))

# Ensure database is created
with app.app_context():
    db.create_all()

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
summarizer = pipeline("summarization")

# Step 1: OAuth Login Route

# Added step
# @app.route('/setup_otp')
# def setup_otp():
#     email = session.get('email')  # Use the logged-in user's email
#     if not email:
#         return "User email not found in session", 400

#     secret = pyotp.random_base32()
#     session['otp_secret'] = secret

#     totp = pyotp.TOTP(secret)
#     otp = totp.now()

#     # Send OTP via email
#     msg = Message("Your One-Time Password (OTP)",
#                   sender=app.config['MAIL_USERNAME'],
#                   recipients=[email])
#     msg.body = f"Your OTP for login is: {otp}"
#     mail.send(msg)

#     return render_template('enter_otp.html')

# @app.route('/verify_otp', methods=['POST'])
# def verify_otp():
#     user_otp = request.form['otp']
#     secret = session.get('otp_secret')

#     if not secret:
#         return "OTP expired or not found", 400

#     totp = pyotp.TOTP(secret)
#     if totp.verify(user_otp):
#         session['otp_verified'] = True
#         return redirect(url_for('summarize_emails'))
#     else:
#         return "Invalid OTP, try again", 400

@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt="consent"
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    state = session.get('state')
    if not state or 'state' not in request.args:
        return redirect(url_for('login'))

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('callback', _external=True),
        state=state
    )
    # flow.fetch_token(authorization_response=request.url)

    # credentials = flow.credentials

    # # from googleapiclient.discovery import build
    # # service = build('gmail', 'v1', credentials=credentials)
    # # user_info = service.users().getProfile(userId='me').execute()
    # # email = user_info['emailAddress']
    # # session['email'] = email 

    # # Save the new credentials to the database
    # existing_creds = OAuthCredentials.query.first()
    # if existing_creds:
    #     db.session.delete(existing_creds) 

    # new_creds = OAuthCredentials(
    #     token=credentials.token,
    #     refresh_token=credentials.refresh_token,
    #     token_uri=credentials.token_uri,
    #     client_id=credentials.client_id,
    #     client_secret=credentials.client_secret,
    #     scopes=",".join(credentials.scopes)
    # )
    # db.session.add(new_creds)
    # db.session.commit()

    # # if 'otp_verified'  not in session:
    # #     return redirect(url_for('setup_otp'))

    # return redirect(url_for('summarize_emails')) 
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Store credentials in session
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        return redirect(url_for('summarize_emails'))

    except Exception as e:
        return jsonify({"error": f"Failed to authenticate: {str(e)}"}), 500


@app.route('/summarize_emails', methods=['GET'])
def summarize_emails():
    # Fetch the stored credentials
    credentials_record = OAuthCredentials.query.first()
    if not credentials_record:
        return redirect(url_for('login'))  # If no credentials, redirect to login

    credentials = Credentials(
        token=credentials_record.token,
        refresh_token=credentials_record.refresh_token,
        token_uri=credentials_record.token_uri,
        client_id=credentials_record.client_id,
        client_secret=credentials_record.client_secret,
        scopes=credentials_record.scopes.split(",")
    )

    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    service = build('gmail', 'v1', credentials=credentials)

    try:
        # Fetch emails (Gmail API automatically orders by the newest emails first)
        results = service.users().messages().list(
            userId='me', labelIds=['INBOX', 'CATEGORY_PERSONAL']
        ).execute()  # No maxResults set to fetch all emails
        messages = results.get('messages', [])

        # Debugging: Log the message IDs to check their order
        print(f"Fetched message IDs: {[msg['id'] for msg in messages]}")

    except Exception as e:
        return jsonify({"error": f"Failed to fetch emails: {str(e)}"}), 500

    summaries = []

    # Iterate over the fetched messages
    for message in messages:
        try:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            parts = payload.get('parts', [])
            body = ""

            # Safely extract the subject
            subject = 'No Subject'  # Default value if subject is missing
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break

            # Extract body content from parts if available
            for part in parts:
                if part.get('mimeType') == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('UTF-8', errors='ignore')
                    break

            # Debugging: Check extracted body
            print(f"Decoded body for email '{subject}': {body[:100]}...")  # Print first 100 chars of body

        except Exception as e:
            body = f"(Unable to decode email body: {str(e)})"

        if body:
            try:
                print(f"Summarizing body: {body[:100]}...")  # Check first 100 chars before summarizing
                # Summarize to about 50 words (you can adjust the lengths here)
                summary = summarizer(body, max_length=150, min_length=30, do_sample=False)  # Adjusted for length
                summaries.append({"subject": subject, "summary": summary[0]['summary_text']})
            except Exception as e:
                summaries.append({"subject": subject, "summary": f"(Error summarizing email body: {str(e)})"})
        else:
            summaries.append({"subject": subject, "summary": "(No summary available)"})

    return render_template('summarized_emails.html', summaries=summaries)   

def decode_body(payload):
    # Check if body is base64 encoded
    body_data = payload.get('body', {}).get('data', '')
    if body_data:
        try:
            decoded_body = base64.urlsafe_b64decode(body_data.encode('UTF-8')).decode('UTF-8', errors='ignore')
            return decoded_body
        except Exception as e:
            return f"(Error decoding body: {str(e)})"
    
    # Check if the body contains parts like MIME Text (HTML or plain text)
    parts = payload.get('parts', [])
    for part in parts:
        filename = part.get('filename', '')
        mime_type = part.get('mimeType', '')
        part_body = part.get('body', {}).get('data', '')
        
        if part_body:
            try:
                decoded_part = base64.urlsafe_b64decode(part_body.encode('UTF-8')).decode('UTF-8', errors='ignore')
                if mime_type == 'text/html':
                    return decoded_part  # Return the HTML body content
                elif mime_type == 'text/plain':
                    return decoded_part  # Return the plain text version of the body
            except Exception as e:
                return f"(Error decoding part: {str(e)})"
    
    # If nothing is found, return placeholder
    return "(No content available)"

@app.route('/')
def home():
    return "Welcome to the Gmail Summarizer! <a href='/login'>Login with Google</a>"

# Function to extract attachments from email
def extract_attachments(payload):
    attachments = []
    for part in payload.get('parts', []):
        filename = part.get('filename')
        mime_type = part.get('mimeType')
        body = part.get('body', {})
        attachment_data = body.get('data')
        
        if attachment_data:
            # Decode base64-encoded attachment
            data = base64.urlsafe_b64decode(attachment_data.encode('UTF-8'))
            attachments.append({
                'filename': filename,
                'data': data,
                'mime_type': mime_type
            })
        elif part.get('body', {}).get('attachmentId'):
            # If attachment is too large, we fetch it from Gmail using the attachmentId
            attachment = service.users().messages().attachments().get(
                userId='me', messageId=payload['headers'][0]['value'], id=part['body']['attachmentId']
            ).execute()
            data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
            attachments.append({
                'filename': filename,
                'data': data,
                'mime_type': mime_type
            })
    return attachments

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
