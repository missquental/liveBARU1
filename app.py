import sys
import subprocess
import threading
import os
import streamlit.components.v1 as components
import streamlit as st

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# ================= CONFIG =================
FOLDER_ID = "https://drive.google.com/drive/folders/16usNQpHCf0gVMiu7khNbj7K48QhOVkFU"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# ================= GOOGLE DRIVE =================
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gdrive"],
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def list_videos_from_drive():
    service = get_drive_service()
    query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/'"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=1000
    ).execute()
    return results.get("files", [])

def download_video(file_id, filename):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    return filename

# ================= FFMPEG =================
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""

    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv"
    ]

    if scale:
        cmd += scale.split()

    cmd.append(output_url)
    log_callback(" ".join(cmd))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        log_callback(line.strip())

# ================= UI =================
def main():
    st.set_page_config(
        page_title="YT Streaming via Google Drive",
        page_icon="📡",
        layout="wide"
    )

    st.title("📡 Live Streaming YouTube (Google Drive Source)")

    # ===== ADS =====
    if st.checkbox("Tampilkan Iklan", True):
        components.html("""
        <div style="padding:20px;text-align:center">
            <script src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
        </div>
        """, height=250)

    # ===== DRIVE VIDEO =====
    st.subheader("📂 Video dari Google Drive")

    if "drive_videos" not in st.session_state:
        with st.spinner("Mengambil daftar video dari Drive..."):
            st.session_state.drive_videos = list_videos_from_drive()

    video_map = {v["name"]: v["id"] for v in st.session_state.drive_videos}

    if not video_map:
        st.error("Tidak ada video di folder Google Drive!")
        return

    selected_video = st.selectbox(
        "Pilih Video",
        list(video_map.keys())
    )

    # ===== STREAM CONFIG =====
    stream_key = st.text_input("Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    logs = []
    log_box = st.empty()

    def log_callback(msg):
        logs.append(msg)
        log_box.text("\n".join(logs[-20:]))

    # ===== BUTTONS =====
    if st.button("🚀 Jalankan Streaming"):
        if not stream_key:
            st.error("Stream Key wajib diisi")
            return

        file_id = video_map[selected_video]
        local_file = f"drive_{selected_video}"

        if not os.path.exists(local_file):
            with st.spinner("Download video dari Google Drive..."):
                download_video(file_id, local_file)

        threading.Thread(
            target=run_ffmpeg,
            args=(local_file, stream_key, is_shorts, log_callback),
            daemon=True
        ).start()

        st.success("Streaming dimulai!")

    if st.button("🛑 Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

    log_box.text("\n".join(logs[-20:]))

if __name__ == "__main__":
    main()
