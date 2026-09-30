#@title 🎞️ Cell 3: RIFE Frame Interpolation — Post-Processor cho LTX-2.5
# ==============================================================================
# Cell 3: 100% STANDALONE — Tăng mượt video (24fps → 48fps / 60fps / 96fps)
# Dùng RIFE PyTorch v4.26, giữ nguyên audio gốc, khử giật và bóng mờ cho phim LTX-2.5.
# ==============================================================================

import glob
import os
import shutil
import subprocess
import sys
import time
import uuid
import gradio as gr

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
RIFE_REPO_DIR  = "/content/RIFE"
RIFE_MODEL_DIR = "/content/RIFE/train_log"
RIFE_OUTPUT    = "/content/rife_output"
TEMP_DIR       = "/content/rife_tmp"
COMFYUI_OUTPUT = "/content/ComfyUI/output"  # Thư mục xuất video của LTX-2.5

os.makedirs(RIFE_OUTPUT, exist_ok=True)


# ------------------------------------------------------------------
# BƯỚC 1: Cài đặt RIFE (clone repo + tải model)
# ------------------------------------------------------------------
def setup_rife():
    """Clone practical-rife repo và tải model checkpoint v4.26."""
    import zipfile
    print("=" * 60)
    print("  🎞️ RIFE Frame Interpolation Setup cho LTX-2.5")
    print("=" * 60)

    # 1a. Dependencies
    print("📦 Kiểm tra dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "torch", "torchvision", "numpy", "opencv-python", "Pillow", "tqdm", "gradio"],
        capture_output=True
    )

    # 1b. Clone repo
    if os.path.exists(os.path.join(RIFE_REPO_DIR, "inference_video.py")):
        print(f"✅ RIFE repo đã có sẵn tại: {RIFE_REPO_DIR}")
    else:
        print("⬇️ Đang clone practical-rife repo...")
        if os.path.exists(RIFE_REPO_DIR):
            shutil.rmtree(RIFE_REPO_DIR)
        ret = subprocess.run(
            ["git", "clone", "https://github.com/hzwer/Practical-RIFE.git", RIFE_REPO_DIR],
            capture_output=True
        )
        if ret.returncode != 0:
            print(f"❌ Clone thất bại: {ret.stderr.decode('utf-8', errors='ignore')}")
            return False
        print("✅ Clone RIFE repo thành công.")

    # 1c. Tải checkpoint RIFE v4.26
    os.makedirs(RIFE_MODEL_DIR, exist_ok=True)
    model_file = os.path.join(RIFE_MODEL_DIR, "flownet.pkl")
    if os.path.exists(model_file) and os.path.getsize(model_file) > 1024 * 1024:
        print("✅ RIFE model v4.26 đã có sẵn.")
    else:
        zip_url = "https://huggingface.co/Bash2X/RIFE-Models/resolve/main/RIFE_v4.26.zip"
        zip_path = os.path.join(RIFE_MODEL_DIR, "RIFE_v4.26.zip")
        print("⬇️ Đang tải RIFE model v4.26 (~23MB)...")
        has_aria2 = subprocess.run("which aria2c", shell=True, capture_output=True).returncode == 0
        if has_aria2:
            cmd = f'aria2c -c -x 8 -s 8 -d "{RIFE_MODEL_DIR}" -o "RIFE_v4.26.zip" "{zip_url}"'
        else:
            cmd = f'wget -q --show-progress -c "{zip_url}" -O "{zip_path}"'

        if os.system(cmd) != 0 or not os.path.exists(zip_path):
            print("⚠️ Không tải được checkpoint. Vui lòng kiểm tra kết nối mạng.")
            return False

        print("📦 Giải nén model...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                pkl_names = [n for n in zf.namelist() if n.endswith("flownet.pkl")]
                if not pkl_names:
                    print("❌ Không tìm thấy flownet.pkl trong zip!")
                    return False
                pkl_data = zf.read(pkl_names[0])
                with open(model_file, "wb") as f:
                    f.write(pkl_data)
            os.remove(zip_path)
            print("✅ Tải và giải nén model hoàn tất.")
        except Exception as e:
            print(f"❌ Lỗi giải nén: {e}")
            return False

    print("\n✅ RIFE setup thành công!\n")
    return True


# ------------------------------------------------------------------
# BƯỚC 2: RIFE Processing Functions
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


def run_rife(input_video_path, exp_scale=1, target_fps=None, progress_callback=None):
    """Nội suy khung hình video bằng RIFE v4.26, bảo toàn âm thanh gốc."""
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Video không tồn tại: {input_video_path}")

    tag = f"ltx_rife_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    session_dir = os.path.join(TEMP_DIR, tag)
    os.makedirs(session_dir, exist_ok=True)

    input_fps = get_video_fps(input_video_path)
    video_has_audio = has_audio(input_video_path)

    audio_file = os.path.join(session_dir, "audio.aac")
    if video_has_audio:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_video_path, "-vn", "-c:a", "copy", audio_file],
            capture_output=True
        )

    rife_out_video = os.path.join(session_dir, "rife_interpolated.mp4")
    inf_script = os.path.join(RIFE_REPO_DIR, "inference_video.py")

    cmd = [
        sys.executable, inf_script,
        "--model", RIFE_MODEL_DIR,
        "--video", input_video_path,
        "--output", rife_out_video,
        "--exp", str(exp_scale),
    ]
    if target_fps:
        cmd += ["--fps", str(target_fps)]

    print(f"🎬 Chạy RIFE: {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line, end="")
        if progress_callback and ("%" in line or "frame" in line.lower()):
            progress_callback(line.strip())

    proc.wait()
    if proc.returncode != 0 or not os.path.exists(rife_out_video):
        shutil.rmtree(session_dir, ignore_errors=True)
        raise RuntimeError("RIFE inference_video.py gặp lỗi hoặc không tạo được video.")

    final_name = os.path.splitext(os.path.basename(input_video_path))[0]
    out_fps_str = f"{target_fps}fps" if target_fps else f"{int(input_fps * (2**exp_scale))}fps"
    final_output_path = os.path.join(RIFE_OUTPUT, f"{final_name}_RIFE_{out_fps_str}.mp4")

    if video_has_audio and os.path.exists(audio_file) and os.path.getsize(audio_file) > 100:
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", rife_out_video,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_output_path
        ]
    else:
        mux_cmd = ["ffmpeg", "-y", "-i", rife_out_video, "-c", "copy", final_output_path]

    subprocess.run(mux_cmd, capture_output=True)
    shutil.rmtree(session_dir, ignore_errors=True)
    elapsed = time.time() - t0
    print(f"✅ Hoàn tất RIFE sau {elapsed:.1f}s -> {final_output_path}")
    return final_output_path


# ------------------------------------------------------------------
# BƯỚC 3: Giao diện Gradio Live
# ------------------------------------------------------------------
def list_ltx_output_videos():
    """Lấy danh sách video xuất từ LTX-2.5."""
    patterns = [
        f"{COMFYUI_OUTPUT}/**/*.mp4",
        f"{COMFYUI_OUTPUT}/*.mp4",
        "/content/*.mp4",
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat, recursive=True))
    files = [f for f in set(files) if "rife" not in f.lower() and os.path.getsize(f) > 1024 * 50]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def process_rife_ui(selected_file, uploaded_file, mode, custom_fps):
    target_path = uploaded_file if uploaded_file else selected_file
    if not target_path or not os.path.exists(target_path):
        return None, "❌ Vui lòng chọn hoặc tải lên một file video hợp lệ!"

    in_fps = get_video_fps(target_path)
    if mode == "2x (24fps → 48fps)":
        exp = 1; fps_arg = None
    elif mode == "4x (24fps → 96fps)":
        exp = 2; fps_arg = None
    elif mode == "Tùy chỉnh target FPS (e.g. 60fps)":
        exp = 1; fps_arg = int(custom_fps)
    else:
        exp = 1; fps_arg = None

    yield None, f"🔄 Đang khởi tạo RIFE... Video gốc: {os.path.basename(target_path)} ({in_fps} fps)"
    try:
        out_video = run_rife(target_path, exp_scale=exp, target_fps=fps_arg)
        out_fps = get_video_fps(out_video)
        yield out_video, f"🎉 Nội suy thành công! FPS ban đầu: {in_fps} ➔ FPS mới: {out_fps}\n📁 Lưu tại: {out_video}"
    except Exception as e:
        yield None, f"❌ Lỗi: {e}"


def build_rife_gui():
    setup_rife()
    css = """
    .gradio-container { max-width: 1100px !important; margin: 0 auto !important; }
    #rife-header { background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                   border-radius:14px; padding:18px 24px; color:#fff; margin-bottom:14px; }
    """
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=css, title="LTX-2.5 RIFE Post-Processor") as demo:
        with gr.Row(elem_id="rife-header"):
            gr.Markdown(
                "## 🎞️ LTX-2.5 Video Polish: RIFE Frame Interpolation\n"
                "Tăng tốc độ khung hình từ 24fps lên 48fps / 60fps mượt mà, "
                "khử giật chuyển động điện ảnh và giữ trọn âm thanh gốc."
            )

        with gr.Row():
            with gr.Column(scale=5):
                gr.Markdown("### 1. Chọn video nguồn")
                comfy_files = list_ltx_output_videos()
                file_dropdown = gr.Dropdown(
                    choices=comfy_files,
                    value=comfy_files[0] if comfy_files else None,
                    label="📂 Video từ ComfyUI Output (LTX-2.5)",
                    interactive=True
                )
                refresh_btn = gr.Button("🔄 Làm mới danh sách video", size="sm")
                refresh_btn.click(lambda: gr.update(choices=list_ltx_output_videos()), outputs=file_dropdown)

                upload_input = gr.Video(label="Hoặc kéo thả file MP4 từ máy tính")

                gr.Markdown("### 2. Tùy chọn nội suy")
                mode_radio = gr.Radio(
                    choices=["2x (24fps → 48fps)", "4x (24fps → 96fps)", "Tùy chỉnh target FPS (e.g. 60fps)"],
                    value="2x (24fps → 48fps)",
                    label="Chế độ tăng mượt (FPS Multiplier)"
                )
                custom_fps_slider = gr.Slider(
                    minimum=30, maximum=120, value=60, step=1,
                    label="Target FPS (Chỉ áp dụng khi chọn tùy chỉnh)",
                    visible=False
                )

                def _toggle_fps(m):
                    return gr.update(visible="Tùy chỉnh" in m)
                mode_radio.change(_toggle_fps, inputs=mode_radio, outputs=custom_fps_slider)

                run_btn = gr.Button("🚀 Bắt đầu làm mượt video", variant="primary", size="lg")

            with gr.Column(scale=5):
                gr.Markdown("### 3. Kết quả")
                status_box = gr.Textbox(label="Trạng thái xử lý", lines=4, interactive=False)
                output_video = gr.Video(label="Video sau nội suy", interactive=False)

        run_btn.click(
            process_rife_ui,
            inputs=[file_dropdown, upload_input, mode_radio, custom_fps_slider],
            outputs=[output_video, status_box]
        )
    return demo


if __name__ == "__main__":
    demo = build_rife_gui()
    demo.queue().launch(share=True, inbrowser=True)
