import os
import subprocess
import threading
import queue
import time
import streamlit as st
import gdown

DOWNLOAD_DIR = "drive_videos"
log_queue = queue.Queue()

# ================= FFMPEG =================
def run_ffmpeg(video_path, stream_key, is_shorts):
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

    log_queue.put("▶️ FFmpeg command:")
    log_queue.put(" ".join(cmd))

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in p.stdout:
        log_queue.put(line.strip())

# ================= DRIVE =================
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
        page_title="YT Live (Google Drive Public)",
        page_icon="📡",
        layout="wide"
    )

    st.title("📡 YouTube Live dari Google Drive (PUBLIC)")

    folder_url = st.text_input(
        "Google Drive Folder URL",
        value="https://drive.google.com/drive/folders/16usNQpHCf0gVMiu7khNbj7K48QhOVkFU"
    )

    if st.button("⬇️ Download Video"):
        with st.spinner("Mengunduh dari Google Drive..."):
            download_drive_folder(folder_url)
        st.success("Download selesai")

    videos = list_local_videos()
    if not videos:
        st.info("Belum ada video. Klik Download dulu.")
        st.stop()

    selected_video = st.selectbox("Pilih Video", videos)
    stream_key = st.text_input("Stream Key YouTube", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    if st.button("🚀 Mulai Streaming"):
        if not stream_key:
            st.error("Stream Key wajib diisi")
            st.stop()

        threading.Thread(
            target=run_ffmpeg,
            args=(selected_video, stream_key, is_shorts),
            daemon=True
        ).start()

        st.success("🚀 Streaming dimulai")

    if st.button("🛑 Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

    # ===== LOG VIEWER (AMAN) =====
    st.subheader("📜 Log FFmpeg")
    log_box = st.empty()

    logs = []
    while not log_queue.empty():
        logs.append(log_queue.get())

    if logs:
        st.session_state.setdefault("logs", [])
        st.session_state.logs.extend(logs)

    log_box.text("\n".join(st.session_state.get("logs", [])[-30:]))

    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()
