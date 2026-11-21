import os, subprocess
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

url = os.environ["VIDEO_URL"]
N, L = 6, 45  # 6 clips, 45 sec each
if "youtube.com" in url or "youtu.be" in url:
    raise SystemExit("YouTube links are blocked on GitHub. Use a Dropbox link.")
subprocess.run(["curl", "-L", "-f", "-o", "src.mp4", url], check=True)
step = max((dur - L) / N, 1)
for i in range(N):
    subprocess.run(["ffmpeg","-y","-ss",str(i*step),"-t",str(L),
        "-i","src.mp4","-vf","crop=ih*9/16:ih,scale=1080:1920",
        "-c:a","aac",f"clip{i}.mp4"], check=True)

creds = Credentials(None, refresh_token=os.environ["REFRESH_TOKEN"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    token_uri="https://oauth2.googleapis.com/token")
yt = build("youtube", "v3", credentials=creds)
base = datetime.now(timezone.utc) + timedelta(hours=1)
for i in range(N):
    when = (base + timedelta(hours=3*i)).strftime("%Y-%m-%dT%H:%M:%SZ")
    yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": f"Short #{i+1} #shorts",
                          "description": "#shorts", "categoryId": "22"},
              "status": {"privacyStatus": "private", "publishAt": when,
                         "selfDeclaredMadeForKids": False}},
        media_body=MediaFileUpload(f"clip{i}.mp4")).execute()
