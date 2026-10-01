#@title 🎞️ Cell 3: RIFE Frame Interpolation (Live Gradio + Cloudflared Tunnel)
# ==============================================================================
# Cell 3: 100% STANDALONE — Tăng mượt video (24fps → 48fps / 60fps / 96fps)
# Dùng RIFE PyTorch v4.26, giữ trọn âm thanh gốc, khử giật và bóng mờ cho LTX-2.5.
# Hỗ trợ: Live Progress %, Cloudflared Tunnel tự động, Chống OOM VRAM, Tương thích Colab & Local.
# ==============================================================================

import glob
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
import gradio as gr

# ------------------------------------------------------------------
# CONFIG & ĐƯỜNG DẪN THÔNG MINH (COLAB & LOCAL COMPATIBLE)
# ------------------------------------------------------------------
IS_COLAB = os.path.exists("/content") or "COLAB_GPU" in os.environ

if IS_COLAB:
    BASE_DIR       = "/content"
    RIFE_REPO_DIR  = "/content/RIFE"
    RIFE_MODEL_DIR = "/content/RIFE/train_log"
    RIFE_OUTPUT    = "/content/rife_output"
    TEMP_DIR       = "/content/rife_tmp"
    COMFYUI_OUTPUT = "/content/ComfyUI/output"
else:
    PROJECT_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_DIR       = os.path.join(PROJECT_ROOT, "rife_workspace")
    RIFE_REPO_DIR  = os.path.join(BASE_DIR, "RIFE")
    RIFE_MODEL_DIR = os.path.join(RIFE_REPO_DIR, "train_log")
    RIFE_OUTPUT    = os.path.join(PROJECT_ROOT, "output", "rife")
    TEMP_DIR       = os.path.join(BASE_DIR, "tmp")
    COMFYUI_OUTPUT = os.path.join(PROJECT_ROOT, "output")

os.makedirs(RIFE_OUTPUT, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(RIFE_MODEL_DIR), exist_ok=True)


# ------------------------------------------------------------------
# 1. SETUP RIFE & CLOUDFLARED TUNNEL
# ------------------------------------------------------------------
def setup_rife():
    """Tự động clone repo Practical-RIFE, tải và giải nén trọn bộ model RIFE v4.26."""
    print("=" * 65)
    print("  🎞️ Khởi tạo RIFE Frame Interpolation (v4.26) cho LTX-2.5")
    print("=" * 65)

    # 1.1 Kiểm tra/cài đặt dependencies cần thiết
    print("📦 Đang kiểm tra thư viện bổ trợ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "tqdm", "opencv-python", "gradio"],
        capture_output=True
    )

    # 1.2 Cài đặt Cloudflared nếu đang chạy trên Google Colab
    if IS_COLAB and not os.path.exists("/usr/local/bin/cloudflared"):
        print("🌐 Đang cài Cloudflared Tunnel cho Google Colab...")
        try:
            subprocess.run(
                "wget -qnc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared",
                shell=True,
                check=True
            )
            subprocess.run("chmod +x /usr/local/bin/cloudflared", shell=True, check=True)
            print("✅ Đã kích hoạt Cloudflared binary.")
        except Exception as e:
            print(f"⚠️ Không thể cài Cloudflared: {e}")

    # 1.3 Clone repo Practical-RIFE
    inf_script = os.path.join(RIFE_REPO_DIR, "inference_video.py")
    if os.path.exists(inf_script):
        print(f"✅ RIFE repo đã có sẵn tại: {RIFE_REPO_DIR}")
    else:
        print("⬇️ Đang clone Practical-RIFE repo từ GitHub...")
        shutil.rmtree(RIFE_REPO_DIR, ignore_errors=True)
        ret = subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/hzwer/Practical-RIFE.git", RIFE_REPO_DIR],
            capture_output=True,
            text=True
        )
        if ret.returncode != 0:
            print(f"❌ Lỗi clone repo: {ret.stderr}")
            return False
        print("✅ Clone RIFE repo thành công.")

    # 1.4 Tải và giải nén trọn bộ model RIFE v4.26
    os.makedirs(RIFE_MODEL_DIR, exist_ok=True)
    model_pkl = os.path.join(RIFE_MODEL_DIR, "flownet.pkl")
    required_py = os.path.join(RIFE_MODEL_DIR, "IFNet_HDv3.py")

    if os.path.exists(model_pkl) and os.path.exists(required_py) and os.path.getsize(model_pkl) > 1024 * 1024:
        print("✅ Model RIFE v4.26 và các file kiến trúc đã sẵn sàng.")
    else:
        zip_url = "https://huggingface.co/Bash2X/RIFE-Models/resolve/main/RIFE_v4.26.zip"
        zip_path = os.path.join(TEMP_DIR, "RIFE_v4.26.zip")
        print(f"⬇️ Đang tải checkpoint RIFE v4.26 (~23MB) từ HuggingFace...")

        download_success = False
        # Thử bằng curl/wget trước nếu có
        for tool_cmd in [f'curl -L -s "{zip_url}" -o "{zip_path}"', f'wget -q -c "{zip_url}" -O "{zip_path}"']:
            try:
                res = subprocess.run(tool_cmd, shell=True, capture_output=True)
                if res.returncode == 0 and os.path.exists(zip_path) and os.path.getsize(zip_path) > 1024 * 1024:
                    download_success = True
                    break
            except Exception:
                pass

        # Fallback bằng urllib
        if not download_success:
            try:
                req = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as f_out:
                    shutil.copyfileobj(resp, f_out)
                if os.path.exists(zip_path) and os.path.getsize(zip_path) > 1024 * 1024:
                    download_success = True
            except Exception as e:
                print(f"❌ Lỗi tải model qua mạng: {e}")
                return False

        print("📦 Đang giải nén toàn bộ kiến trúc model vào train_log/...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.infolist():
                    # Trích xuất toàn bộ các file bên trong thư mục train_log/
                    if "train_log/" in member.filename and not member.filename.startswith("__MACOSX"):
                        # Trích xuất trực tiếp vào RIFE_REPO_DIR để khớp cấu trúc /RIFE/train_log/...
                        zf.extract(member, RIFE_REPO_DIR)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            print("✅ Tải và cấu hình model RIFE v4.26 thành công.")
        except Exception as e:
            print(f"❌ Lỗi giải nén zip: {e}")
            return False

    print("=" * 65)
    print("  🚀 Hệ thống RIFE Frame Interpolation đã sẵn sàng hoạt động!")
    print("=" * 65 + "\n")
    return True


# ------------------------------------------------------------------
# 2. HỖ TRỢ XỬ LÝ VIDEO & QUẢN LÝ TIẾN TRÌNH LIVE
# ------------------------------------------------------------------
def get_video_fps(video_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", video_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        num, den = r.stdout.strip().split("/")
        return round(float(num) / float(den), 2)
    except Exception:
        return 24.0


def has_audio(video_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0",
           "-show_entries", "stream=codec_type", "-of", "csv=p=0", video_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return "audio" in r.stdout.lower()
    except Exception:
        return False


def get_video_resolution(video_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height", "-of", "csv=p=0", video_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        w, h = map(int, r.stdout.strip().split(","))
        return w, h
    except Exception:
        return 1280, 720


def list_ltx_output_videos():
    """Quét toàn bộ video có thể làm mượt từ ComfyUI hoặc thư mục output."""
    search_dirs = [
        COMFYUI_OUTPUT,
        RIFE_OUTPUT,
        os.path.join(BASE_DIR, "downloads"),
        BASE_DIR,
    ]
    patterns = [f"{d}/**/*.mp4" for d in search_dirs] + [f"{d}/*.mp4" for d in search_dirs]

    files = []
    for pat in patterns:
        files.extend(glob.glob(pat, recursive=True))

    valid_files = []
    for f in set(files):
        if "rife" not in os.path.basename(f).lower() and os.path.isfile(f) and os.path.getsize(f) > 1024 * 50:
            valid_files.append(f)

    valid_files.sort(key=os.path.getmtime, reverse=True)
    return valid_files


def process_rife_live(selected_file, uploaded_file, mode, custom_fps, scale_mode, progress=gr.Progress(track_tqdm=True)):
    """Generator phát sóng tiến trình trực tiếp theo thời gian thực về Gradio UI."""
    target_path = uploaded_file if uploaded_file else selected_file
    if not target_path or not os.path.exists(target_path):
        yield None, "❌ Vui lòng chọn hoặc tải lên một tệp video hợp lệ!"
        return

    in_fps = get_video_fps(target_path)
    w, h = get_video_resolution(target_path)
    video_has_audio = has_audio(target_path)

    # Xác định hệ số nhân hoặc target FPS
    if mode == "2x (24fps → 48fps)":
        exp = 1; fps_arg = None
    elif mode == "4x (24fps → 96fps)":
        exp = 2; fps_arg = None
    elif mode == "Tùy chỉnh target FPS (e.g. 60fps)":
        exp = 1; fps_arg = int(custom_fps)
    else:
        exp = 1; fps_arg = None

    tag = f"rife_job_{int(time.time())}"
    session_dir = os.path.join(TEMP_DIR, tag)
    os.makedirs(session_dir, exist_ok=True)

    # Trích xuất âm thanh gốc nếu có
    audio_file = os.path.join(session_dir, "extracted_audio.aac")
    if video_has_audio:
        yield None, f"🎵 Đang trích xuất luồng âm thanh gốc từ video..."
        subprocess.run(
            ["ffmpeg", "-y", "-i", target_path, "-vn", "-c:a", "copy", audio_file],
            capture_output=True
        )

    rife_raw_video = os.path.join(session_dir, "rife_raw.mp4")
    inf_script = os.path.join(RIFE_REPO_DIR, "inference_video.py")

    cmd = [
        sys.executable, inf_script,
        "--model", RIFE_MODEL_DIR,
        "--video", target_path,
        "--output", rife_raw_video,
        "--exp", str(exp),
    ]
    if fps_arg:
        cmd += ["--fps", str(fps_arg)]

    # Tối ưu bộ nhớ VRAM cho GPU (Colab T4 16GB)
    if scale_mode == "Tự động (Scale 0.5 nếu >= 1080p)" and (w >= 1920 or h >= 1080):
        cmd += ["--scale", "0.5"]
    elif scale_mode == "Scale 0.5 (Tiết kiệm VRAM tối đa)":
        cmd += ["--scale", "0.5"]

    status_header = (
        f"🚀 Đang nội suy khung hình RIFE v4.26\n"
        f"📹 Tệp: {os.path.basename(target_path)} ({w}x{h} @ {in_fps} fps)\n"
        f"⚙️ Chế độ: {mode} | Âm thanh gốc: {'Giữ trọn vẹn' if video_has_audio else 'Không'}\n"
        f"⏳ Đang xử lý các khung hình qua GPU Tensor Cores..."
    )
    yield None, status_header

    t0 = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = RIFE_REPO_DIR

    # Khởi chạy Subprocess đọc stdout trực tiếp (unbuffered)
    proc = subprocess.Popen(
        cmd,
        cwd=RIFE_REPO_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env
    )

    last_yield_time = time.time()
    for line in proc.stdout:
        clean_line = line.strip()
        if not clean_line:
            continue
        print(clean_line)

        # Cập nhật Live lên Gradio khi có thông tin phần trăm hoặc khung hình
        if "%" in clean_line or "frame" in clean_line.lower() or "it/s" in clean_line:
            if time.time() - last_yield_time > 0.4:
                pct_match = re.search(r"(\d+)%", clean_line)
                if pct_match:
                    pct = int(pct_match.group(1)) / 100.0
                    progress(pct, desc=f"Đang làm mượt: {clean_line}")
                yield None, f"{status_header}\n\n⚡ Tiến trình trực tiếp: {clean_line}"
                last_yield_time = time.time()

    proc.wait()
    if proc.returncode != 0 or not os.path.exists(rife_raw_video):
        shutil.rmtree(session_dir, ignore_errors=True)
        yield None, f"❌ Lỗi: Tiến trình RIFE inference gặp sự cố (Exit code {proc.returncode}). Vui lòng kiểm tra VRAM GPU!"
        return

    # Ghép lại âm thanh gốc với video mượt mới
    yield None, "🎬 Đang đóng gói video và ghép lại âm thanh chất lượng cao..."
    final_name = os.path.splitext(os.path.basename(target_path))[0]
    out_fps_str = f"{fps_arg}fps" if fps_arg else f"{int(in_fps * (2**exp))}fps"
    final_output_path = os.path.join(RIFE_OUTPUT, f"{final_name}_RIFE_{out_fps_str}.mp4")

    if video_has_audio and os.path.exists(audio_file) and os.path.getsize(audio_file) > 100:
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", rife_raw_video,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_output_path
        ]
    else:
        mux_cmd = ["ffmpeg", "-y", "-i", rife_raw_video, "-c", "copy", final_output_path]

    subprocess.run(mux_cmd, capture_output=True)
    shutil.rmtree(session_dir, ignore_errors=True)

    elapsed = time.time() - t0
    final_fps = get_video_fps(final_output_path)
    success_msg = (
        f"🎉 Hoàn tất làm mượt xuất sắc sau {elapsed:.1f} giây!\n"
        f"📊 Tốc độ khung hình: {in_fps} fps ➔ {final_fps} fps (Chuyển động mượt mà điện ảnh)\n"
        f"📁 Tệp xuất: {final_output_path}"
    )
    yield final_output_path, success_msg


# ------------------------------------------------------------------
# 3. GIAO DIỆN GRADIO LIVE & CLOUDFLARED LAUNCHER
# ------------------------------------------------------------------
def start_cloudflared_tunnel(port=7860):
    """Khởi chạy Cloudflared tunnel và in link live trycloudflare.com ra console."""
    if not (IS_COLAB and os.path.exists("/usr/local/bin/cloudflared")):
        return

    def _tunnel_worker():
        try:
            proc = subprocess.Popen(
                ["/usr/local/bin/cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in proc.stdout:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    url = match.group(0)
                    print("\n" + "=" * 65)
                    print(f"  🌐 CLOUDFLARED LIVE PUBLIC URL (MỞ NGAY BẤT KỲ ĐÂU):")
                    print(f"  👉 {url}")
                    print("=" * 65 + "\n")
                    break
        except Exception:
            pass

    t = threading.Thread(target=_tunnel_worker, daemon=True)
    t.start()


def build_and_launch():
    setup_rife()
    start_cloudflared_tunnel(port=7860)

    css = """
    .gradio-container { max-width: 1150px !important; margin: 0 auto !important; }
    #rife-header { background: linear-gradient(135deg, #0284c7 0%, #1e40af 100%);
                   border-radius:14px; padding:18px 24px; color:#fff; margin-bottom:14px; }
    """
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=css, title="LTX-2.5 RIFE Post-Processor") as demo:
        with gr.Row(elem_id="rife-header"):
            gr.Markdown(
                "## 🎞️ LTX-2.5 Video Polish: RIFE Frame Interpolation (Live)\n"
                "**Tăng tốc độ khung hình từ 24fps lên 48fps / 60fps / 96fps**, khử bóng mờ chuyển động và giữ trọn âm thanh gốc."
            )

        with gr.Row():
            with gr.Column(scale=5):
                gr.Markdown("### 1. Chọn video nguồn")
                comfy_files = list_ltx_output_videos()
                file_dropdown = gr.Dropdown(
                    choices=comfy_files,
                    value=comfy_files[0] if comfy_files else None,
                    label="📂 Video từ ComfyUI Output / Thư mục dự án",
                    interactive=True
                )
                refresh_btn = gr.Button("🔄 Quét lại danh sách video", size="sm")
                refresh_btn.click(lambda: gr.update(choices=list_ltx_output_videos()), outputs=file_dropdown)

                upload_input = gr.Video(label="Hoặc kéo thả file MP4 từ máy tính lên")

                gr.Markdown("### 2. Tùy chọn làm mượt")
                mode_radio = gr.Radio(
                    choices=["2x (24fps → 48fps)", "4x (24fps → 96fps)", "Tùy chỉnh target FPS (e.g. 60fps)"],
                    value="2x (24fps → 48fps)",
                    label="Hệ số nhân khung hình"
                )
                custom_fps_slider = gr.Slider(
                    minimum=30, maximum=120, value=60, step=1,
                    label="Target FPS (Chỉ áp dụng khi chọn Tùy chỉnh)",
                    visible=False
                )
                scale_dropdown = gr.Dropdown(
                    choices=["Tự động (Scale 0.5 nếu >= 1080p)", "Scale 1.0 (Độ nét cao nhất)", "Scale 0.5 (Tiết kiệm VRAM tối đa)"],
                    value="Tự động (Scale 0.5 nếu >= 1080p)",
                    label="Tối ưu bộ nhớ VRAM (Chống văng Colab T4)"
                )

                mode_radio.change(lambda m: gr.update(visible="Tùy chỉnh" in m), inputs=mode_radio, outputs=custom_fps_slider)
                run_btn = gr.Button("🚀 Bắt đầu làm mượt video", variant="primary", size="lg")

            with gr.Column(scale=5):
                gr.Markdown("### 3. Tiến trình & Kết quả")
                status_box = gr.Textbox(label="Trạng thái xử lý theo thời gian thực", lines=6, interactive=False)
                output_video = gr.Video(label="Video sau khi nội suy mượt mà", interactive=False)

        run_btn.click(
            process_rife_live,
            inputs=[file_dropdown, upload_input, mode_radio, custom_fps_slider, scale_dropdown],
            outputs=[output_video, status_box]
        )

    print("\n🌐 Đang khởi động máy chủ Gradio...")
    demo.queue().launch(share=True, server_name="0.0.0.0", server_port=7860, show_error=True)


if __name__ == "__main__":
    build_and_launch()
