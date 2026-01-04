import os
import math
from pathlib import Path
from moviepy.editor import VideoFileClip
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SOURCE_DIR = "yt-vids"
PARTS_DIR = "yt-vids_parts"
CHUNK_SECONDS = 60

CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

MAX_UPLOADS_PER_RUN = 10
UPLOADED_LIST_FILE = "uploaded.txt"

DEFAULT_TAGS = ["shorts", "youtubeshorts", "viral", "trending", "shortsvideo"] # type any tag what you want
DEFAULT_PRIVACY = "public"  



def clean_title(raw_title: str) -> str:
    if "-" in raw_title:
        raw_title = raw_title.split("-", 1)[1].strip()
    return raw_title.strip()


def to_vertical_9x16(clip):
    target_w = 1080
    target_h = 1920
    target_ratio = target_w / target_h

    video_ratio = clip.w / clip.h

    if video_ratio > target_ratio:
        new_width = int(clip.h * target_ratio)
        x1 = (clip.w - new_width) // 2
        x2 = x1 + new_width
        clip = clip.crop(x1=x1, y1=0, x2=x2, y2=clip.h)

    clip = clip.resize(height=target_h)
    return clip


def split_video(input_path: str, output_dir: str, chunk_seconds: int):
    os.makedirs(output_dir, exist_ok=True)

    clip = VideoFileClip(input_path)
    duration = clip.duration
    total_chunks = math.ceil(duration / chunk_seconds)

    base_name = Path(input_path).stem
    base_title = clean_title(base_name)

    print(f"Video: {input_path}")
    print(f"Duration: {duration:.1f} sec")
    print(f"Parts: {total_chunks} x ~{chunk_seconds} sec")

    for i in range(total_chunks):
        start = i * chunk_seconds
        end = min((i + 1) * chunk_seconds, duration)

        print(f"Part {i + 1}: {start:.1f} - {end:.1f}")

        subclip = clip.subclip(start, end)
        subclip = to_vertical_9x16(subclip)

        out_filename = f"{base_title}_part_{i + 1}.mp4"
        out_path = os.path.join(output_dir, out_filename)

        subclip.write_videofile(
            out_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp.m4a",
            remove_temp=True,
            verbose=False,
            logger=None,
        )

    clip.close()
    print("Splitting finished.\n")


def split_all_videos():
    if not os.path.exists(SOURCE_DIR):
        print(f"Source folder not found: {SOURCE_DIR}")
        return

    for filename in os.listdir(SOURCE_DIR):
        if not filename.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
            continue
        input_path = os.path.join(SOURCE_DIR, filename)
        split_video(input_path, PARTS_DIR, CHUNK_SECONDS)


def load_uploaded_files() -> set:
    if not os.path.exists(UPLOADED_LIST_FILE):
        return set()
    with open(UPLOADED_LIST_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_uploaded_file(filename: str):
    with open(UPLOADED_LIST_FILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


def get_youtube_service():
    creds = None

    if os.path.exists(TOKEN_FILE) and os.path.getsize(TOKEN_FILE) > 0:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    else:
        if not os.path.exists(CLIENT_SECRETS_FILE):
            raise FileNotFoundError(f"Missing {CLIENT_SECRETS_FILE}")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def get_part_number(filename: str) -> int:
    stem = Path(filename).stem
    try:
        return int(stem.split("_part_")[1])
    except Exception:
        return 0


def upload_video(youtube, video_path: str, title: str, description: str, tags=None, privacy_status="public"):
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
        "status": {"privacyStatus": privacy_status},
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progress: {int(status.progress() * 100)}%")

    print(f"Uploaded. ID: {response.get('id')}\n")
    return response


def upload_existing_parts(max_uploads: int = MAX_UPLOADS_PER_RUN):
    if not os.path.exists(PARTS_DIR):
        print(f"Parts folder not found: {PARTS_DIR}")
        return

    parts = sorted(
        [f for f in os.listdir(PARTS_DIR) if f.lower().endswith(".mp4")],
        key=get_part_number,
    )

    if not parts:
        print("No video parts found in yt-vids_parts.")
        return

    uploaded = load_uploaded_files()

    youtube = get_youtube_service()
    uploads_done = 0

    for filename in parts:
        if uploads_done >= max_uploads:
            break
        if filename in uploaded:
            continue

        full_path = os.path.join(PARTS_DIR, filename)

        raw_stem = Path(filename).stem  
        base_stem = raw_stem.split("_part_")[0]
        base_title = clean_title(base_stem)

        try:
            part_num = raw_stem.split("_part_")[1]
        except Exception:
            part_num = str(get_part_number(filename))

        title = f"{base_title} - Part {part_num}"
        description = f"Part {part_num} from '{base_title}'.\n#shorts"

        try:
            upload_video(
                youtube=youtube,
                video_path=full_path,
                title=title,
                description=description,
                tags=DEFAULT_TAGS,
                privacy_status=DEFAULT_PRIVACY,
            )
        except HttpError as e:
            print("Upload error:", e)
            print("Tip: You may have hit YouTube daily upload limit. Try later or another channel/account.")
            break

        save_uploaded_file(filename)
        uploads_done += 1

    print(f"Done. Uploaded in this run: {uploads_done}")


def menu():
    while True:
        print("\nChoose an action:")
        print("1) Split videos (yt-vids -> yt-vids_parts)")
        print("2) Upload existing parts (yt-vids_parts -> YouTube)")
        print("3) Exit")

        choice = input("Enter 1/2/3: ").strip()

        if choice == "1":
            split_all_videos()
        elif choice == "2":
            try:
                n = input(f"How many videos to upload now? (default {MAX_UPLOADS_PER_RUN}): ").strip()
                n = int(n) if n else MAX_UPLOADS_PER_RUN
            except ValueError:
                n = MAX_UPLOADS_PER_RUN
            upload_existing_parts(max_uploads=n)
        elif choice == "3":
            print("Exit.")
            return
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    menu()
