# Gmail Summarizer Web App

This project enables users to summarize their Gmail inbox emails using a web application. It integrates Gmail API and uses a pre-trained **transformers pipeline** for summarization. The app allows users to securely log in using Google OAuth and view summaries of their emails.

---

## **Table of Contents**

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation Instructions](#installation-instructions)
- [Setup Gmail API](#setup-gmail-api)
- [Running the App](#running-the-app)
- [Accessing the Summarization](#accessing-the-summarization)
- [Challenges Faced](#challenges-faced)
- [Contributing](#contributing)

---

## **Introduction**

The **Gmail Summarizer** is a web application built using **Flask**, **Google OAuth 2.0**, and **HuggingFace's transformers**. It securely logs users into their Gmail account and fetches emails from their inbox. The content of the emails is then summarized using an AI-powered summarization model.

---

## **Features**

- **Google OAuth Authentication**: Secure login with Google account using OAuth 2.0.
- **Summarization of Emails**: Automatically summarizes emails from Gmail inbox.
- **Fast and Efficient**: Uses batching and asynchronous calls for faster summarization.
- **Email Attachment Extraction**: Extracts and handles email attachments.
- **Secure and Private**: User authentication and email data remain confidential.
  
---

## **Technologies Used**

- **Python**: Backend programming language.
- **Flask**: Web framework for building the application.
- **Google API**: For accessing Gmail data (OAuth 2.0 authentication, Gmail API).
- **Transformers (Hugging Face)**: Pre-trained model for text summarization.
- **SQLAlchemy**: ORM for database management.
- **Aptos Blockchain**: Optional implementation for decentralized authentication.
- **SQLite**: For storing authentication credentials.
  
---

## **Installation Instructions**

### 1. Clone the repository

```bash
git clone https://github.com/your-username/gmail-summarizer.git
cd gmail-summarizer
```
### 2. Set up a virtual environment
Create a virtual environment to isolate project dependencies:
```bash
python -m venv venv
```
   ### Activate the virtual environment:

### On Windows:
```bash
.\venv\Scripts\activate
```
### On macOS/Linux:
```bash
source venv/bin/activate
```
### 3. Install Dependencies
  Run the following command to install all the required dependencies:
```bash
pip install -r requirements.txt
```
## **Setup Gmail API**
To access Gmail data securely, you need to set up the Google Gmail API and obtain credentials.

Go to the **Google Developers Console**.
Create a new project or select an existing one.
Enable the **Gmail API** for your project.
**Go to APIs & Services > Credentials and create OAuth 2.0 credentials.**
Download the **client_secret.json file** and place it in the root of the project directory.
Make sure to set the correct redirect_uri in your OAuth consent screen, which should be:
```bash
http://localhost:5000/callback
```
### Running the App
Ensure the Gmail API is set up and the credentials are in place.
Set up environment variables:
GOOGLE_CLIENT_SECRET_FILE: Path to the client_secret.json file you downloaded.
FLASK_SECRET_KEY: A secret key for your Flask application (you can generate one using Python: import secrets; secrets.token_urlsafe(16)).
For local development, you can create a .env file with the following content:

**GOOGLE_CLIENT_SECRET_FILE=path_to_your_client_secret.json**
**FLASK_SECRET_KEY=your_flask_secret_key**
Run the Flask app:
```bash
python app.py
```
This will start a local server on **http://localhost:5000**.

### **Accessing the Summarization**
Open your browser and go to http://localhost:5000/.
Click on "Login with Google" to authenticate with your Google account.
After successful login, you'll be redirected to the email summarization page where the app fetches and summarizes emails from your Gmail inbox.
The summaries will be displayed along with the subject of each email.


### **Challenges Faced**
Google OAuth Authentication Flow: The OAuth flow was tricky initially, especially when dealing with token refresh and scope handling. I overcame it by reviewing the Google OAuth documentation and using a pre-built Python package (google-auth).
Email Body Decoding: Some emails were in HTML or multipart formats, which required special handling for decoding the body content. This was solved using proper MIME parsing techniques.
Rate Limiting: The Gmail API has limits on the number of API calls. To prevent rate limiting, I implemented pagination and optimized batch fetching of email messages.
Contributing



We welcome contributions! To contribute to this project:

### Fork the repository.
Create a new branch ```git checkout -b feature-name```.
Commit your changes ```git commit -am 'Add new feature'```.
Push to the branch ```git push origin feature-name```.
Create a new Pull Request.
Please make sure your code adheres to our coding style and includes tests where applicable.
