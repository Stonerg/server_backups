import os
import pickle
import subprocess
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
# Constants
load_dotenv()

# Constants from environment variables
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
TOKEN_FILE = os.getenv("TOKEN_FILE")
SCOPES = [os.getenv("SCOPES")]
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
BACKUP_FILE = os.getenv("BACKUP_FILE")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID") # Google Drive folder where backups will be stored

def authenticate_google_drive():
    """Authenticate with Google Drive API."""
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            print("Loading existing credentials...")
            creds = pickle.load(token)

    # If token is missing or expired, authenticate again
    if not creds or not creds.valid:
        print("Refreshing or generating new credentials...")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

  # Console-based authentication

        # Save credentials for next use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def backup_mysql():
    """Generate a MySQL database backup securely."""
    print("Creating MySQL backup...")
    command = f"mysqldump -h {MYSQL_HOST} -u {MYSQL_USER} -p'{MYSQL_PASSWORD}' {MYSQL_DATABASE} > {BACKUP_FILE}"
    subprocess.run(command, shell=True, check=True)
    print(f"Backup saved to {BACKUP_FILE}")


def upload_to_drive(service):
    """Upload the MySQL backup file to Google Drive."""
    print("Uploading backup to Google Drive...")

    file_metadata = {
        "name": BACKUP_FILE,
        "parents": [DRIVE_FOLDER_ID]  # Upload to the specified folder
    }

    media = MediaFileUpload(BACKUP_FILE, mimetype="application/sql")

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print(f"Backup uploaded successfully, File ID: {file.get('id')}")


def main():
    drive_service = authenticate_google_drive()
    backup_mysql()
    upload_to_drive(drive_service)

if __name__ == "__main__":
    main()
