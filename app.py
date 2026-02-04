import streamlit as st
import gdown
import os
import subprocess
import threading
import queue
from pathlib import Path
import streamlit.components.v1 as components

# ===============================
# KONFIGURASI
# ===============================
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1d7fpbrOI9q9Yl6w99-yZGNMB30XNyugf"
VIDEO_DIR = "videos"

Path(VIDEO_DIR).mkdir(parents=True, exist_ok=True)

# ===============================
# DOWNLOAD GOOGLE DRIVE
# ===============================
def download_drive_folder():
    gdown.download_folder(
        url=DRIVE_FOLDER_URL,
        output=VIDEO_DIR,
        quiet=False,
        use_cookies=False
    )

# ===============================
# FFMPEG THREAD (JANGAN SENTUH STREAMLIT DI SINI)
# ===============================
def run_ffmpeg(video_path, stream_key, is_shorts, log_queue):
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    scale = ["-vf", "scale=720:1280"] if is_shorts else []

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
        "-keyint_min", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        *scale,
        rtmp_url
    ]

    log_queue.put("CMD: " + " ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            log_queue.put(line.strip())

    except Exception as e:
        log_queue.put(f"ERROR: {e}")

# ===============================
# STREAMLIT UI (MAIN THREAD)
# ===============================
st.set_page_config(
    page_title="Drive → Live YouTube",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Google Drive → Live YouTube")

# ===============================
# IKLAN (OPSIONAL)
# ===============================
if st.checkbox("Tampilkan Iklan", value=True):
    components.html(
        """
        <div style="padding:15px;background:#f0f2f6;border-radius:10px;text-align:center">
        <script type='text/javascript'
        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
        </script>
        <p style="color:#888">Slot Iklan</p>
        </div>
        """,
        height=250
    )

# ===============================
# SESSION STATE INIT
# ===============================
if "log_queue" not in st.session_state:
    st.session_state.log_queue = queue.Queue()

if "logs" not in st.session_state:
    st.session_state.logs = []

# ===============================
# DOWNLOAD SECTION
# ===============================
st.subheader("📥 Ambil Video dari Google Drive")

if st.button("Download Video"):
    with st.spinner("Mengunduh dari Google Drive..."):
        download_drive_folder()
    st.success("Download selesai")

# ===============================
# LIST VIDEO
# ===============================
st.subheader("🎬 Video Tersedia")

videos = sorted([
    f for f in os.listdir(VIDEO_DIR)
    if f.lower().endswith((".mp4", ".flv"))
])

video_path = None

if videos:
    selected = st.selectbox("Pilih Video", videos)
    video_path = os.path.join(VIDEO_DIR, selected)
    st.video(video_path)
else:
    st.warning("Belum ada video")

# ===============================
# STREAM SETTING
# ===============================
st.subheader("🔴 Live Streaming YouTube")

stream_key = st.text_input("Stream Key YouTube", type="password")
is_shorts = st.checkbox("Mode Shorts (9:16 / 720x1280)")

# ===============================
# BUTTON CONTROL
# ===============================
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Mulai Live"):
        if not video_path or not stream_key:
            st.error("Video & Stream Key wajib diisi")
        else:
            threading.Thread(
                target=run_ffmpeg,
                args=(
                    video_path,
                    stream_key,
                    is_shorts,
                    st.session_state.log_queue
                ),
                daemon=True
            ).start()
            st.success("Streaming dimulai")

with col2:
    if st.button("🛑 Stop Live"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

# ===============================
# LOG OUTPUT (AMAN)
# ===============================
log_box = st.empty()

while not st.session_state.log_queue.empty():
    msg = st.session_state.log_queue.get()
    st.session_state.logs.append(msg)

log_box.text("\n".join(st.session_state.logs[-15:]))
