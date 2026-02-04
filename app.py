import sys
import subprocess
import threading
import os
import re
import requests
import gdown
import streamlit as st
import streamlit.components.v1 as components

# ================= FFMPEG STREAM =================
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    cmd = [
        "ffmpeg", "-re",
        "-stream_loop", "-1",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-c:a", "aac",
        "-b:a", "128k"
    ]

    if is_shorts:
        cmd += ["-vf", "scale=720:1280"]

    cmd += ["-f", "flv", output_url]

    log_callback(" ".join(cmd))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        log_callback(line.strip())

# ================= GOOGLE DRIVE PUBLIC =================
def list_public_drive_videos(folder_id):
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    html = requests.get(url).text

    files = []
    matches = re.findall(r'"([a-zA-Z0-9_-]{33})","([^"]+)"', html)

    for file_id, name in matches:
        if name.lower().endswith((".mp4", ".flv", ".mkv", ".mov")):
            files.append({"id": file_id, "name": name})

    return files

# ================= UI =================
def main():
    st.set_page_config(
        page_title="YouTube Live Streaming (Google Drive)",
        page_icon="📡",
        layout="wide"
    )

    st.title("📡 Live Streaming YouTube (Google Drive Public Folder)")

    # ===== ADS (OPSIONAL) =====
    if st.checkbox("Tampilkan Iklan", True):
        components.html("""
        <div style="padding:20px;text-align:center">
            <script src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
        </div>
        """, height=250)

    # ===== GOOGLE DRIVE INPUT =====
    st.subheader("📂 Google Drive Folder")

    folder_input = st.text_input(
        "Google Drive Folder URL / ID",
        placeholder="https://drive.google.com/drive/folders/XXXX"
    )

    if not folder_input:
        st.warning("Masukkan Folder Google Drive (PUBLIC)")
        st.stop()

    folder_id = folder_input.rstrip("/").split("/")[-1]

    # ===== LOAD VIDEO LIST =====
    if "drive_videos" not in st.session_state or st.button("🔄 Refresh Video"):
        with st.spinner("Mengambil video dari Google Drive..."):
            st.session_state.drive_videos = list_public_drive_videos(folder_id)

    if not st.session_state.drive_videos:
        st.error("Tidak ada video (pastikan folder PUBLIC)")
        st.stop()

    video_map = {v["name"]: v["id"] for v in st.session_state.drive_videos}

    selected_video = st.selectbox(
        "Pilih Video",
        list(video_map.keys())
    )

    # ===== STREAM CONFIG =====
    stream_key = st.text_input("Stream Key YouTube", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    logs = []
    log_box = st.empty()

    def log_callback(msg):
        logs.append(msg)
        log_box.text("\n".join(logs[-20:]))

    # ===== START STREAM =====
    if st.button("🚀 Jalankan Streaming"):
        if not stream_key:
            st.error("Stream Key wajib diisi")
            st.stop()

        file_id = video_map[selected_video]
        local_file = f"drive_{selected_video}"

        if not os.path.exists(local_file):
            with st.spinner("Download video dari Google Drive..."):
                gdown.download(
                    f"https://drive.google.com/uc?id={file_id}",
                    local_file,
                    quiet=False
                )

        threading.Thread(
            target=run_ffmpeg,
            args=(local_file, stream_key, is_shorts, log_callback),
            daemon=True
        ).start()

        st.success("Streaming dimulai!")

    # ===== STOP STREAM =====
    if st.button("🛑 Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

    log_box.text("\n".join(logs[-20:]))

if __name__ == "__main__":
    main()
