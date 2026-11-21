import os, subprocess
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

WATERMARK = "@technoviralshorts"   # <-- yahan apna watermark likhein
N, L = 6, 45

url = os.environ["VIDEO_URL"]
title = os.environ.get("VIDEO_TITLE") or "Short"
tags = [t.strip().lstrip("#") for t in
        os.environ.get("VIDEO_TAGS", "").split(",") if t.strip()]
hashtags = " ".join("#" + t.replace(" ", "") for t in tags) + " #shorts"

if "youtube.com" in url or "youtu.be" in url:
    raise SystemExit("YouTube link GitHub par block hai. Drive link use karein.")

subprocess.run(["curl", "-L", "-f", "-o", "src.mp4", url], check=True)
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "csv=p=0", "src.mp4"], capture_output=True, text=True)
try:
    dur = float(probe.stdout.strip())
except ValueError:
    raise SystemExit("Ye video file nahi hai, direct link use karein.")

L = min(L, int(dur))
step = (dur - L) / N
open("wm.txt", "w").write(WATERMARK)
vf = ("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,"
      "drawtext=textfile=wm.txt:"
      "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
      "fontsize=48:fontcolor=white@0.8:shadowcolor=black:shadowx=2:shadowy=2:"
      "x=w-tw-40:y=h-th-150")

for i in range(N):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(i * step), "-t", str(L), "-i", "src.mp4",
         "-vf", vf, "-c:a", "aac", "-preset", "veryfast", f"clip{i}.mp4"],
        check=True)

creds = Credentials(
    None, refresh_token=os.environ["REFRESH_TOKEN"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    token_uri="https://oauth2.googleapis.com/token")
yt = build("youtube", "v3", credentials=creds)

base = datetime.now(timezone.utc) + timedelta(hours=1)
for i in range(N):
    when = (base + timedelta(hours=3 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
    yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": f"{title} (Part {i+1}) #shorts"[:100],
                          "description": f"{title}\n\n{hashtags}",
                          "tags": tags, "categoryId": "22"},
              "status": {"privacyStatus": "private", "publishAt": when,
                         "selfDeclaredMadeForKids": False}},
        media_body=MediaFileUpload(f"clip{i}.mp4")).execute()
    print("Uploaded clip", i + 1)
