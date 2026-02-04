import os
import subprocess
import threading
import streamlit as st
import gdown
import streamlit.components.v1 as components

DOWNLOAD_DIR = "drive_videos"

# ================= FFMPEG =================
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

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
        "-b:a", "128k"
    ]

    if is_shorts:
        cmd += ["-vf", "scale=720:1280"]

    cmd += ["-f", "flv", output_url]

    log_callback(" ".join(cmd))

    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    for line in p.stdout:
        log_callback(line.strip())

# ================= DOWNLOAD FOLDER =================
def download_drive_folder(folder_url):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    gdown.download_folder(
        folder_url,
        output=DOWNLOAD_DIR,
        quiet=False,
        use_cookies=False
    )

def list_local_videos():
    videos = []
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for f in files:
            if f.lower().endswith((".mp4", ".mkv", ".mov", ".flv")):
                videos.append(os.path.join(root, f))
    return videos

# ================= UI =================
def main():
    st.set_page_config(
        page_title="YT Streaming (Google Drive Public)",
        page_icon="📡",
        layout="wide"
    )

    st.title("📡 Live Streaming YouTube (Google Drive Public Folder)")

    # ===== DRIVE INPUT =====
    folder_url = st.text_input(
        "Google Drive Folder URL",
        value="https://drive.google.com/drive/folders/16usNQpHCf0gVMiu7khNbj7K48QhOVkFU"
    )

    if st.button("⬇️ Ambil Video dari Google Drive"):
        with st.spinner("Download folder dari Google Drive..."):
            download_drive_folder(folder_url)
        st.success("Folder berhasil di-download")

    videos = list_local_videos()

    if not videos:
        st.warning("Belum ada video, klik tombol download dulu")
        st.stop()

    selected_video = st.selectbox(
        "Pilih Video",
        videos
    )

    stream_key = st.text_input("Stream Key YouTube", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    logs = []
    log_box = st.empty()

    def log_callback(msg):
        logs.append(msg)
        log_box.text("\n".join(logs[-20:]))

    if st.button("🚀 Jalankan Streaming"):
        if not stream_key:
            st.error("Stream Key wajib diisi")
            st.stop()

        threading.Thread(
            target=run_ffmpeg,
            args=(selected_video, stream_key, is_shorts, log_callback),
            daemon=True
        ).start()

        st.success("🚀 Streaming dimulai")

    if st.button("🛑 Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

    log_box.text("\n".join(logs[-20:]))

if __name__ == "__main__":
    main()
