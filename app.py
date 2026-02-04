import streamlit as st
import os
import re
import subprocess
import threading
import requests
import gdown

st.set_page_config(page_title="Drive → YouTube Live", layout="wide")

DOWNLOAD_DIR = "videos"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===============================
# AMBIL VIDEO DARI DRIVE PUBLIC
# ===============================
def list_public_drive_videos(folder_id):
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    html = requests.get(url).text

    videos = []
    matches = re.findall(r'"([a-zA-Z0-9_-]{33})","([^"]+)"', html)

    for file_id, name in matches:
        if name.lower().endswith((".mp4", ".mkv", ".mov", ".flv")):
            videos.append({"id": file_id, "name": name})

    return videos

# ===============================
# DOWNLOAD VIDEO
# ===============================
def download_video(file_id, filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(path):
        gdown.download(
            f"https://drive.google.com/uc?id={file_id}",
            path,
            quiet=False
        )
    return path

# ===============================
# FFMPEG (TANPA STREAMLIT UI)
# ===============================
def run_ffmpeg(video_path, rtmp_url):
    cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        rtmp_url
    ]
    subprocess.Popen(cmd)

# ===============================
# UI
# ===============================
def main():
    st.title("📡 Google Drive → YouTube Live")
    st.caption("Drive PUBLIC | Tanpa Secret | Streamlit Cloud Ready")

    folder_input = st.text_input(
        "Google Drive Folder URL / ID",
        placeholder="https://drive.google.com/drive/folders/XXXXX"
    )

    rtmp_url = st.text_input(
        "RTMP YouTube",
        placeholder="rtmp://a.rtmp.youtube.com/live2/XXXX-XXXX-XXXX"
    )

    if not folder_input or not rtmp_url:
        st.stop()

    folder_id = folder_input.split("/")[-1]

    if st.button("🔄 Load Video"):
        st.session_state.videos = list_public_drive_videos(folder_id)

    if "videos" not in st.session_state:
        st.session_state.videos = list_public_drive_videos(folder_id)

    if not st.session_state.videos:
        st.error("❌ Tidak ada video — pastikan folder PUBLIC (Viewer)")
        st.stop()

    video_map = {v["name"]: v["id"] for v in st.session_state.videos}

    selected = st.selectbox("Pilih Video", video_map.keys())

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ START LIVE"):
            video_path = download_video(video_map[selected], selected)
            threading.Thread(
                target=run_ffmpeg,
                args=(video_path, rtmp_url),
                daemon=True
            ).start()
            st.success("✅ Streaming dimulai (tunggu ±20 detik)")

    with col2:
        if st.button("⛔ STOP LIVE"):
            os.system("pkill ffmpeg")
            st.warning("⛔ Streaming dihentikan")

if __name__ == "__main__":
    main()
