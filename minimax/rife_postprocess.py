#@title 🎞️ Cell 3: RIFE Frame Interpolation — Post-Processor cho MiniMax H3
# ============================================================
# 100% STANDALONE — KHÔNG phụ thuộc ComfyUI / download.py / minimax.py
# Chạy trực tiếp trên Google Colab (hoặc bất kỳ môi trường Linux + GPU)
# Pipeline: Video 24fps → ffmpeg extract → RIFE PyTorch → ffmpeg encode
# ============================================================

import glob, os, shutil, subprocess, sys, time, uuid
import gradio as gr

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
RIFE_REPO_DIR  = "/content/RIFE"
RIFE_MODEL_DIR = "/content/RIFE/train_log"
RIFE_OUTPUT    = "/content/rife_output"
TEMP_DIR       = "/content/rife_tmp"
COMFYUI_OUTPUT = "/content/ComfyUI/output"  # Đọc video từ minimax.py output

os.makedirs(RIFE_OUTPUT, exist_ok=True)

# ------------------------------------------------------------------
# BƯỚC 1: Cài đặt RIFE (clone repo + tải model)
# ------------------------------------------------------------------
def setup_rife():
    """Clone practical-rife repo và tải model checkpoint."""
    import zipfile
    print("=" * 55)
    print("  🎞️  RIFE Post-Processor — Setup")
    print("=" * 55)

    # 1a. Cài dependencies
    print("📦 Cài đặt dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "torch", "torchvision", "numpy", "opencv-python",
                    "Pillow", "tqdm", "gradio"],
                   capture_output=True)

    # 1b. Clone RIFE repo (practical-rife by hzwer — author gốc)
    if os.path.exists(os.path.join(RIFE_REPO_DIR, "inference_video.py")):
        print(f"✅ RIFE repo đã có: {RIFE_REPO_DIR}")
    else:
        print("⬇️  Clone practical-rife repo...")
        if os.path.exists(RIFE_REPO_DIR):
            shutil.rmtree(RIFE_REPO_DIR)
        ret = subprocess.run(
            ["git", "clone", "https://github.com/hzwer/Practical-RIFE.git", RIFE_REPO_DIR],
            capture_output=True
        )
        if ret.returncode != 0:
            print(f"❌ Clone thất bại: {ret.stderr.decode()}")
            return False
        print("✅ Clone RIFE repo thành công.")

    # 1c. Tải RIFE model v4.26 (từ HuggingFace mirror — file .zip)
    os.makedirs(RIFE_MODEL_DIR, exist_ok=True)
    model_file = os.path.join(RIFE_MODEL_DIR, "flownet.pkl")
    if os.path.exists(model_file) and os.path.getsize(model_file) > 1024 * 1024:
        print("✅ RIFE model đã có: flownet.pkl")
    else:
        # Model là file .zip chứa flownet.pkl — tải rồi giải nén
        zip_url = "https://huggingface.co/Bash2X/RIFE-Models/resolve/main/RIFE_v4.26.zip"
        zip_path = os.path.join(RIFE_MODEL_DIR, "RIFE_v4.26.zip")
        print(f"⬇️  Tải RIFE model v4.26 (~23MB)...")
        has_aria2 = subprocess.run("which aria2c", shell=True, capture_output=True).returncode == 0
        if has_aria2:
            cmd = f'aria2c -c -x 8 -s 8 -d "{RIFE_MODEL_DIR}" -o "RIFE_v4.26.zip" "{zip_url}"'
        else:
            cmd = f'wget -q --show-progress -c "{zip_url}" -O "{zip_path}"'

        if os.system(cmd) != 0 or not os.path.exists(zip_path):
            print("⚠️  Không tải được model. Kiểm tra kết nối mạng.")
            return False

        # Giải nén flownet.pkl từ zip
        print("📦 Giải nén model...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Tìm flownet.pkl trong zip (có thể nằm trong subfolder)
                pkl_names = [n for n in zf.namelist() if n.endswith("flownet.pkl")]
                if not pkl_names:
                    print("❌ Không tìm thấy flownet.pkl trong zip!")
                    return False
                # Extract flownet.pkl ra đúng vị trí
                pkl_data = zf.read(pkl_names[0])
                with open(model_file, "wb") as f:
                    f.write(pkl_data)
            # Xóa zip sau khi giải nén
            os.remove(zip_path)
            print("✅ Tải và giải nén model thành công.")
        except Exception as e:
            print(f"❌ Lỗi giải nén: {e}")
            return False

    print("\n✅ RIFE setup hoàn tất!\n")
    return True


# ------------------------------------------------------------------
# BƯỚC 2: Hàm RIFE interpolation chính
# ------------------------------------------------------------------
def run_rife_interpolation(
    input_video: str,
    multiplier: int = 2,
    output_path: str = None,
    scale: float = 1.0,
    fp16: bool = True,
) -> str:
    """
    Gọi inference_video.py của practical-rife để nội suy video.
    
    Args:
        input_video: Đường dẫn video gốc (24fps từ MiniMax)
        multiplier: 2 = 48fps, 4 = 96fps
        output_path: Đường dẫn output (auto nếu None)
        scale: 1.0 = full res, 0.5 = half res (tiết kiệm VRAM)
        fp16: Dùng half precision (nhanh + ít VRAM hơn)
    
    Returns:
        Đường dẫn video output
    """
    if output_path is None:
        uid = uuid.uuid4().hex[:8]
        output_path = os.path.join(RIFE_OUTPUT, f"rife_{multiplier}x_{uid}.mp4")

    inference_script = os.path.join(RIFE_REPO_DIR, "inference_video.py")
    if not os.path.exists(inference_script):
        raise FileNotFoundError(f"Không tìm thấy {inference_script}. Hãy chạy setup_rife() trước.")

    cmd = [
        sys.executable, inference_script,
        "--video", input_video,
        "--output", output_path,
        "--multi", str(multiplier),
        "--scale", str(scale),
    ]
    if fp16:
        cmd.append("--fp16")

    env = os.environ.copy()
    env["PYTHONPATH"] = RIFE_REPO_DIR

    result = subprocess.run(
        cmd,
        cwd=RIFE_REPO_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 phút max
    )

    if result.returncode != 0:
        error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
        raise RuntimeError(f"RIFE inference thất bại:\n{error_msg}")

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"RIFE không tạo được file output: {output_path}")

    return output_path


def create_slowmo(input_video: str, multiplier: int = 2) -> str:
    """
    Tạo slow-motion: RIFE nội suy thêm frames → giữ FPS gốc → video chậm lại.
    Ví dụ: 24fps + 2× = video dài gấp đôi, vẫn 24fps.
    """
    # Bước 1: RIFE nội suy (tăng số frame lên multiplier×)
    uid = uuid.uuid4().hex[:8]
    rife_temp = os.path.join(RIFE_OUTPUT, f"rife_temp_{uid}.mp4")
    run_rife_interpolation(input_video, multiplier=multiplier, output_path=rife_temp)

    # Bước 2: Encode lại với FPS gốc (24fps) → video chậm lại
    slowmo_path = os.path.join(RIFE_OUTPUT, f"slowmo_{multiplier}x_{uid}.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", rife_temp,
        "-r", "24",  # Giữ 24fps gốc
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an",  # Bỏ audio (slow-mo audio không có ý nghĩa)
        slowmo_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)

    # Xóa file temp
    if os.path.exists(rife_temp):
        os.remove(rife_temp)

    return slowmo_path


# ------------------------------------------------------------------
# BƯỚC 3: Gradio generator function
# ------------------------------------------------------------------
def rife_process(
    video_path: str,
    multiplier_str: str,
    slow_motion: bool,
    use_fp16: bool,
    scale_str: str,
):
    """Generator function cho Gradio — xử lý RIFE và stream status."""
    if not video_path:
        yield None, "⚠️ Chưa chọn video đầu vào!"
        return

    if not os.path.exists(os.path.join(RIFE_REPO_DIR, "inference_video.py")):
        yield None, "❌ RIFE chưa được cài đặt! Chạy lại Cell 3 từ đầu."
        return

    multiplier = int(multiplier_str[0])  # "2× (48fps)" → 2
    scale = float(scale_str.split("×")[0])  # "1.0× (full)" → 1.0
    fps_in = 24  # MiniMax H3 luôn xuất 24fps
    fps_out = fps_in if slow_motion else fps_in * multiplier
    mode_label = f"Slow-motion {multiplier}×" if slow_motion else f"{multiplier}× ({fps_out}fps)"

    # Kiểm tra kích thước video
    size_mb = os.path.getsize(video_path) / 1024 / 1024
    yield None, (
        f"🚀 Bắt đầu RIFE [{mode_label}]\n"
        f"📁 Input: {os.path.basename(video_path)} ({size_mb:.1f} MB)\n"
        f"⚙️ FP16: {'Có' if use_fp16 else 'Không'} · Scale: {scale_str}"
    )

    t_start = time.time()
    try:
        if slow_motion:
            yield None, f"⏳ Đang tạo slow-motion {multiplier}× (giữ 24fps)..."
            out_path = create_slowmo(video_path, multiplier=multiplier)
        else:
            yield None, f"⏳ Đang nội suy {multiplier}× → {fps_out}fps..."
            out_path = run_rife_interpolation(
                video_path,
                multiplier=multiplier,
                scale=scale,
                fp16=use_fp16,
            )
    except Exception as e:
        yield None, f"❌ Lỗi RIFE: {e}"
        return

    elapsed = int(time.time() - t_start)
    out_size = os.path.getsize(out_path) / 1024 / 1024

    yield out_path, (
        f"✅ RIFE hoàn tất! ({elapsed}s)\n"
        f"🎞️ Chế độ: {mode_label}\n"
        f"📁 Output: {os.path.basename(out_path)} ({out_size:.1f} MB)\n"
        f"📂 Thư mục: {RIFE_OUTPUT}"
    )


# ------------------------------------------------------------------
# BƯỚC 4: Helpers
# ------------------------------------------------------------------
def get_minimax_videos():
    """Lấy danh sách video output mới nhất từ minimax.py."""
    files = sorted(
        glob.glob(os.path.join(COMFYUI_OUTPUT, "**", "*.mp4"), recursive=True),
        key=os.path.getmtime, reverse=True
    )[:15]
    return files if files else []


def load_selected_video(selected_path):
    """Load video đã chọn từ dropdown."""
    if selected_path and os.path.exists(selected_path):
        return selected_path
    return None


# ------------------------------------------------------------------
# BƯỚC 5: Gradio UI
# ------------------------------------------------------------------
CSS = """
.rife-hdr { background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d2d4d 100%);
            padding: 18px 22px; border-radius: 12px; margin-bottom: 12px; }
.rife-hdr h1 { color: #00d4ff; font-size: 1.5em; margin: 0; }
.rife-hdr p  { color: #8899aa; margin: 4px 0 0; font-size: 0.88em; }
.tip { background: #111a2a; border-left: 3px solid #00aaff;
       padding: 10px 14px; font-size: 0.85em; color: #99bbdd; border-radius: 4px; }
"""

with gr.Blocks(title="RIFE Post-Processor") as demo:
    gr.HTML("""<div class="rife-hdr">
      <h1>🎞️ RIFE Frame Interpolation</h1>
      <p>Post-processor độc lập cho MiniMax H3 — Video 24fps → 48/96fps mượt mà</p>
    </div>""")

    with gr.Row():
        with gr.Column(scale=5):
            # ── Input ──
            with gr.Group():
                gr.Markdown("### 📥 Video Đầu Vào (24fps từ MiniMax H3)")
                video_in = gr.Video(label="Kéo thả video hoặc chọn từ danh sách bên dưới")
                with gr.Row():
                    file_dropdown = gr.Dropdown(
                        label="📂 Chọn nhanh từ ComfyUI output",
                        choices=get_minimax_videos(),
                        interactive=True,
                    )
                    refresh_btn = gr.Button("🔄", scale=0, min_width=50)

            # ── Settings ──
            with gr.Group():
                gr.Markdown("### ⚙️ Cài đặt Nội suy")
                multiplier_radio = gr.Radio(
                    label="🎯 Hệ số nội suy",
                    choices=[
                        "2× (48fps) — Khuyên dùng",
                        "4× (96fps) — Rất mượt, tốn VRAM",
                    ],
                    value="2× (48fps) — Khuyên dùng",
                )
                with gr.Row():
                    slowmo_cb = gr.Checkbox(
                        label="🐢 Slow-motion",
                        value=False,
                        info="Giữ 24fps, thêm frame → video chậm lại"
                    )
                    fp16_cb = gr.Checkbox(
                        label="⚡ FP16 (Half precision)",
                        value=True,
                        info="Nhanh hơn, ít VRAM hơn. TẮT nếu bị artifact"
                    )
                scale_radio = gr.Radio(
                    label="📐 Optical Flow Scale",
                    choices=["1.0× (full — chất lượng cao)", "0.5× (half — tiết kiệm VRAM)"],
                    value="1.0× (full — chất lượng cao)",
                    info="Giảm scale nếu GPU ≤ 16GB hoặc video HD"
                )
                gr.Markdown(
                    "💡 **Mẹo:** Nếu video có chuyển động nhanh/phức tạp, dùng **2×** thay 4× "
                    "để tránh ghosting. Bật **FP16** để giảm ~40% VRAM."
                )

            run_btn = gr.Button("🚀 Bắt Đầu RIFE", variant="primary", size="lg")

        # ── Output ──
        with gr.Column(scale=5):
            video_out = gr.Video(label="🎬 Video sau RIFE")
            status_box = gr.Textbox(
                label="ℹ️ Trạng thái", interactive=False, lines=5,
                value="Chờ xử lý..."
            )

    # ── Events ──
    refresh_btn.click(fn=get_minimax_videos, outputs=[file_dropdown])
    file_dropdown.change(fn=load_selected_video, inputs=[file_dropdown], outputs=[video_in])
    run_btn.click(
        fn=rife_process,
        inputs=[video_in, multiplier_radio, slowmo_cb, fp16_cb, scale_radio],
        outputs=[video_out, status_box],
    )


# ------------------------------------------------------------------
# KHỞI ĐỘNG
# ------------------------------------------------------------------
print("\n" + "=" * 55)
print("  🎞️  RIFE Post-Processor — Khởi động")
print("=" * 55)

if setup_rife():
    print("🟢 RIFE sẵn sàng! Đang mở Gradio UI...\n")
    demo.queue(max_size=2).launch(
        share=True,       # ⭐ BẮT BUỘC cho Colab — tạo public URL
        quiet=True,
        css=CSS,           # ⭐ Gradio 6.0: css phải ở launch(), không phải Blocks()
        server_port=7861,
    )
else:
    print("❌ Setup RIFE thất bại. Kiểm tra output ở trên.")
