from flask import Flask, redirect, url_for, request, render_template, jsonify, session
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
import os
import base64
import mimetypes
from io import BytesIO
from email import message_from_bytes

# Load environment variables
app = Flask(__name__)
CORS(app)

# Set secret key securely
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Use environment variable for client secret file
CLIENT_SECRET_FILE = os.getenv('GOOGLE_CLIENT_SECRET_FILE', r'your client_secret.... .json file (path)')

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
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials

    # Save the new credentials to the database
    existing_creds = OAuthCredentials.query.first()
    if existing_creds:
        db.session.delete(existing_creds) 

    new_creds = OAuthCredentials(
        token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        scopes=",".join(credentials.scopes)
    )
    db.session.add(new_creds)
    db.session.commit()

    return redirect(url_for('summarize_emails')) 

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
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch emails: {str(e)}"}), 500

    messages = results.get('messages', [])
    summaries = []

    # Loop through the messages and summarize the email body
    for message in messages:
        try:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            body = payload.get('body', {}).get('data', '')

            # Extract subject from headers
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

            # Decode the body content (if base64 encoded)
            if body:
                decoded_body = base64.urlsafe_b64decode(body.encode('UTF-8')).decode('UTF-8', errors='ignore')
            else:
                decoded_body = "(No content available)"
            
            # Debugging: Check if the decoded body contains meaningful content
            print(f"Decoded body for email '{subject}': {decoded_body[:100]}...")  # Print the first 100 characters of the body

        except Exception as e:
            decoded_body = f"(Unable to decode email body: {str(e)})"
        
        # Check if decoded_body has meaningful content and summarize it
        if decoded_body and decoded_body != "(No content available)" and decoded_body != "(Unable to decode email body)":
            try:
                # Debugging: Check if the body passed to the summarizer is valid
                print(f"Summarizing body: {decoded_body[:100]}...")  # Print the first 100 characters passed to summarizer
                summary = summarizer(decoded_body, max_length=100, min_length=30, do_sample=False)
                summaries.append({"subject": subject, "summary": summary[0]['summary_text']})
            except Exception as e:
                summaries.append({"subject": subject, "summary": f"(Error summarizing email body: {str(e)})"})
        else:
            summaries.append({"subject": subject, "summary": "(No summary available)"})

        # Extract attachments if present
        attachments = extract_attachments(payload)
        if attachments:
            summaries[-1]["attachments"] = attachments

    # Render the email summaries in the HTML template
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
