
YouTube Shorts Auto Split & Upload

This project is a Python automation tool that helps you:
- split long videos into 60-second clips
- convert clips to vertical 9:16 format
- upload them to YouTube as Shorts automatically

==================================================

FEATURES

- Split long videos into 60-second parts
- Automatic vertical 9:16 crop (Shorts-ready)
- Automatic title format:
  Original Video Title — Part X #shorts
- Automatic tags for Shorts
- Upload via official YouTube Data API v3
- Google OAuth authorization

==================================================

REQUIREMENTS

- Python 3.11
  https://www.python.org/downloads/release/python-3110/
- Google account with a YouTube channel
- Google Cloud project with YouTube Data API enabled

==================================================

PROJECT STRUCTURE

youtube-shorts-uploader/
- yt_auto_split_upload.py
- requirements.txt
- README.md
- .gitignore
- yt-vids/        (input long videos)
- yt-vids_parts/  (generated Shorts videos)

==================================================

INSTALLATION

1. Clone repository

https://github.com/your-username/youtube-shorts-uploader

2. Create virtual environment

python -m venv .venv
Windows:
.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

==================================================

GOOGLE CLOUD SETUP (DETAILED STEP-BY-STEP)

Step 1: Open Google Cloud Console
https://console.cloud.google.com/

Step 2: Create a new project
- Click project selector (top bar)
- Click "New Project"
- Enter project name
- Click "Create"

Step 3: Enable YouTube Data API v3
https://console.cloud.google.com/apis/library

- Search for "YouTube Data API v3"
- Click "Enable"

Step 4: Configure OAuth consent screen
https://console.cloud.google.com/apis/credentials/consent

- User Type: External
- App name: Any name
- User support email: your email
- Developer contact email: your email
- Save and continue (skip scopes)
- Add your Gmail to Test Users
- Save

Step 5: Create OAuth Client ID
https://console.cloud.google.com/apis/credentials

- Click "Create Credentials"
- OAuth client ID
- Application type: Desktop app
- Name: YouTube Uploader
- Create and download JSON

Step 6: Rename file
Rename downloaded file to:

client_secret.json

Place it next to yt_auto_split_upload.py

IMPORTANT:
Do NOT upload client_secret.json or token.json to GitHub.

==================================================

HOW TO USE

1. Put long videos into folder:
yt-vids/

2. Run script

python yt_auto_split_upload.py

3. First run:
- Browser opens
- Login to Google account
- Allow permissions
- token.json is created automatically

==================================================

SWITCHING YOUTUBE ACCOUNTS / CHANNELS

To upload to another channel:

1. Delete token.json
2. Run script again
3. Login with another Google account or channel

==================================================

UPLOAD LIMITS

YouTube has daily upload limits.

If you see error:
uploadLimitExceeded

- Stop script
- Wait 24 hours
- Or switch to another channel

==================================================

NOTES

- Shorts requirements:
  - Vertical format (9:16)
  - Duration 60 seconds or less
- YouTube automatically detects Shorts

==================================================

DISCLAIMER

This project uses the official YouTube Data API.
Use responsibly and follow YouTube platform rules.

==================================================

LICENSE

MIT

