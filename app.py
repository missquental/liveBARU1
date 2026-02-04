import streamlit as st
import os
import re
import requests
import gdown
import subprocess
import threading
import time
import stat

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="Drive → Live Stream", layout="wide")
FFMPEG_PATH = "./ffmpeg"
DOWNLOAD_DIR = "videos"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===============================
# SETUP FFMPEG (STATIC)
# ===============================
def setup_ffmpeg():
    if os.path.exists(FFMPEG_PATH):
        return

    with st.spinner("Menyiapkan ffmpeg..."):
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        subprocess.run(["wget", "-q", url, "-O", "ffmpeg.tar.xz"])
        subprocess.run(["tar", "-xf", "ffmpeg.tar.xz"])

        folder = next(f for f in os.listdir(".") if f.startswith("ffmpeg-"))
        os.rename(f"{folder}/ffmpeg", "ffmpeg")

        os.chmod("ffmpeg", os.stat("ffmpeg").st_mode | stat.S_IEXEC)

# ===============================
# LIST VIDEO PUBLIC DRIVE
# ===============================
def list_public_drive_videos(folder_id):
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    html = requests.get(url).text

    files = []
    matches = re.findall(r'"([a-zA-Z0-9_-]{33})","([^"]+)"', html)

    for file_id, name in matches:
        if name.lower().endswith((".mp4", ".mkv", ".mov", ".flv")):
            files.append({"id": file_id, "name": name})

    return files

# ===============================
# DOWNLOAD VIDEO
# ===============================
def download_video(file_id, name):
    path = os.path.join(DOWNLOAD_DIR, name)
    if not os.path.exists(path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=False)
    return path

# ===============================
# FFMPEG RUNNER (NO STREAMLIT CALL)
# ===============================
def run_ffmpeg(video_path, rtmp_url):
    cmd = [
        FFMPEG_PATH,
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
    setup_ffmpeg()

    st.title("📡 Google Drive → YouTube Live")
    st.caption("Folder Drive PUBLIC | Tanpa Secret | Siap Live")

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

    if st.button("🔄 Refresh Video"):
        st.session_state.videos = list_public_drive_videos(folder_id)

    if "videos" not in st.session_state:
        st.session_state.videos = list_public_drive_videos(folder_id)

    if not st.session_state.videos:
        st.error("Tidak ada video (pastikan folder PUBLIC)")
        st.stop()

    video_map = {v["name"]: v["id"] for v in st.session_state.videos}

    selected = st.selectbox("Pilih Video", video_map.keys())

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ START LIVE"):
            path = download_video(video_map[selected], selected)
            threading.Thread(
                target=run_ffmpeg,
                args=(path, rtmp_url),
                daemon=True
            ).start()
            st.success("Live streaming dimulai")

    with col2:
        if st.button("⛔ STOP LIVE"):
            os.system("pkill -f ./ffmpeg")
            st.warning("Live dihentikan")

# ===============================
if __name__ == "__main__":
    main()
