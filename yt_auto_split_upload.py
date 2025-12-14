import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PARTS_DIR = "yt-vids_parts"
MAX_UPLOADS_PER_RUN = 10

CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
UPLOADED_LIST_FILE = "uploaded.txt"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def clean_title(raw_title: str) -> str:
    if "-" in raw_title:
        raw_title = raw_title.split("-", 1)[1].strip()
    return raw_title.strip()


def load_uploaded_files():
    if not os.path.exists(UPLOADED_LIST_FILE):
        return set()
    with open(UPLOADED_LIST_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_uploaded_file(filename: str):
    with open(UPLOADED_LIST_FILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


def get_youtube_service():
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def get_part_number(filename: str) -> int:
    stem = Path(filename).stem
    try:
        return int(stem.split("_part_")[1])
    except Exception:
        return 0


def upload_video(youtube, video_path: str, title: str, description: str, tags=None):
    if tags is None:
        tags = []

    print(f"Uploading: {video_path}")

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public"},
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
        except Exception as e:
            print("Upload error:", str(e))
            return None

        if status:
            print(f"Progress: {int(status.progress() * 100)}%")

    print(f"Uploaded. ID: {response.get('id')}\n")
    return response


def upload_existing_parts():
    youtube = get_youtube_service()

    if not os.path.exists(PARTS_DIR):
        print("Parts directory not found.")
        return

    parts = sorted(
        [f for f in os.listdir(PARTS_DIR) if f.lower().endswith(".mp4")],
        key=get_part_number,
    )

    if not parts:
        print("No video parts found.")
        return

    uploaded_files = load_uploaded_files()
    uploads_done = 0

    for filename in parts:
        if uploads_done >= MAX_UPLOADS_PER_RUN:
            break

        if filename in uploaded_files:
            continue

        full_path = os.path.join(PARTS_DIR, filename)

        raw_title = Path(filename).stem
        base_title = clean_title(raw_title.split("_part_")[0])

        try:
            part_num = raw_title.split("_part_")[1]
        except Exception:
            part_num = "?"

        title = f"{base_title} - Part {part_num} #shorts"
        description = (
            f"Part {part_num} from video '{base_title}'.\n"
            f"#shorts\nAutomated upload via Python."
        )

        tags = ["shorts", "viral", "youtubeshorts", "trend", "shortsvideo"]

        res = upload_video(youtube, full_path, title, description, tags)
        if res is None:
            break

        save_uploaded_file(filename)
        uploads_done += 1


if __name__ == "__main__":
    upload_existing_parts()
