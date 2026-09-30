#@title 📦 Cell 1: Setup ComfyUI + Tải Models LTX-2.5 A2V Two-Stage Distilled (Audio-to-Video)
# ==============================================================================
# Cell 1: Tự động thiết lập môi trường ComfyUI và tải toàn bộ model weights
# chuẩn xác cho pipeline LTX-2.5 A2V (Audio-driven Video Generation):
#  1. Diffusion Transformer Distilled (bf16 / int8-convrot)
#  2. Text Encoder Gemma 4 (bf16 / int8-convrot)
#  3. Audio VAE (ltx-2.5-audio-vae-bf16)
#  4. Video VAE (ltx-2.5-video-vae-bf16)
#  5. Latent Spatial Upscaler x2 (Stage 2 Refiner)
#
# Tương thích 100% với workflow: workflow/ltx/LTX-2.5_A2V_Two_Stage_Distilled.json
# ==============================================================================

import concurrent.futures
import os
import subprocess
import threading
import time
from getpass import getpass
from pathlib import Path
from IPython.display import display, HTML


def log(msg, color="#00e676"):
    try:
        display(HTML(f"<p style='color:{color}; font-weight:bold; margin:4px 0;'>{msg}</p>"))
    except Exception:
        print(f"[{color}] {msg}")


def sh(cmd):
    """Chạy lệnh shell, tương thích cả Colab và local Linux/Windows."""
    try:
        get_ipython().system(cmd)
    except NameError:
        os.system(cmd)


def pip_install(pkgs, use_uv=True):
    """Cài package bằng uv (tốc độ cao), tự động fallback sang pip tiêu chuẩn."""
    if use_uv:
        ret = os.system(f"uv pip install -q --system {pkgs}")
        if ret == 0:
            return
        log(f"⚠️ uv gặp sự cố, đang fallback sang pip tiêu chuẩn cho: {pkgs}", color="#ffb300")
    os.system(f"pip install -q {pkgs}")


def torch_cuda_ready():
    """Kiểm tra môi trường có sẵn Torch CUDA không."""
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


# --------------------------------------------------------------------------
# [0/4] Kiểm tra Hugging Face Access Token (Gated Repo LTX-2.5)
# --------------------------------------------------------------------------
log("[0/4] Kiểm tra Hugging Face Access Token...")

HF_TOKEN = None
try:
    from google.colab import userdata
    HF_TOKEN = userdata.get("HF_TOKEN")
    if HF_TOKEN:
        log("✅ Đã lấy HF_TOKEN từ Colab Secrets (🔑).")
except Exception:
    pass

if not HF_TOKEN:
    HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    log(
        "🔑 Chưa tìm thấy HF_TOKEN. Vui lòng nhập token tại ô bên dưới "
        "(Token không hiển thị vì lý do bảo mật).\n"
        "Lấy token tại: https://huggingface.co/settings/tokens\n"
        "Đồng thời nhớ bấm 'Agree and access repository' tại:\n"
        "  👉 https://huggingface.co/Lightricks/LTX-2.5\n",
        color="#ffb300",
    )
    try:
        HF_TOKEN = getpass("Dán Hugging Face token rồi nhấn Enter: ").strip()
    except Exception:
        HF_TOKEN = ""

if not HF_TOKEN:
    raise RuntimeError(
        "❌ Cần HF_TOKEN để tải mô hình gốc LTX-2.5 (gated repo). "
        "Vui lòng chạy lại cell và dán token hợp lệ."
    )

os.environ["HF_TOKEN"] = HF_TOKEN
AUTH_HEADER = f"Authorization: Bearer {HF_TOKEN}"

# --------------------------------------------------------------------------
# [1/4] Cài đặt thư viện lõi & clone ComfyUI
# --------------------------------------------------------------------------
log("[1/4] Cài đặt thư viện lõi và clone ComfyUI...")
sh("pip install -q uv")

if torch_cuda_ready():
    import torch
    log(f"✅ Đã có Torch {torch.__version__} (CUDA) -> Bỏ qua cài đặt lại")
else:
    log("⏳ Đang cài Torch CUDA (có thể mất 1-2 phút)...")
    pip_install("torch torchvision torchaudio")

pip_install(
    "torchsde einops diffusers accelerate av spandrel albumentations "
    "onnx opencv-python onnxruntime tqdm ipywidgets gradio soundfile librosa"
)

COMFYUI_ROOT = "/content/ComfyUI"
if not os.path.exists(COMFYUI_ROOT):
    sh("git clone -q https://github.com/comfyanonymous/ComfyUI /content/ComfyUI")
else:
    log("🔄 ComfyUI đã tồn tại -> git pull để cập nhật...")
    sh("cd /content/ComfyUI && git pull -q")

if os.path.exists(f"{COMFYUI_ROOT}/requirements.txt"):
    pip_install(f"-r {COMFYUI_ROOT}/requirements.txt")

sh("apt-get -y install -qq aria2 > /dev/null 2>&1")

# --------------------------------------------------------------------------
# [2/4] Cài đặt Custom Nodes mở rộng cho LTX-2.5 A2V
# --------------------------------------------------------------------------
log("[2/4] Cài đặt các Custom Nodes mở rộng cho LTX-2.5 A2V Studio...")

CUSTOM_NODES = [
    ("https://github.com/Lightricks/ComfyUI-LTXVideo", "ComfyUI-LTXVideo"),
    ("https://github.com/kijai/ComfyUI-KJNodes", "ComfyUI-KJNodes"),
    ("https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite", "ComfyUI-VideoHelperSuite"),
]

cn_dir = os.path.join(COMFYUI_ROOT, "custom_nodes")
os.makedirs(cn_dir, exist_ok=True)

for repo_url, folder_name in CUSTOM_NODES:
    target_path = os.path.join(cn_dir, folder_name)
    if os.path.exists(target_path):
        sh(f"cd {target_path} && git pull -q")
    else:
        sh(f"git clone -q {repo_url} {target_path}")
    req_file = os.path.join(target_path, "requirements.txt")
    if os.path.exists(req_file):
        pip_install(f"-r {req_file}")

# --------------------------------------------------------------------------
# [3/4] Tải Model Weights LTX-2.5 A2V (UNet, Text Encoder, VAEs, Upscaler)
# --------------------------------------------------------------------------
log("[3/4] Đang tải Model Weights chuyên dụng cho A2V Two-Stage Distilled...")

_FAILED_DOWNLOADS = []
_print_lock = threading.Lock()

# Lựa chọn trọng số tối ưu (mặc định int8 cho Colab T4/L4/A100 tiết kiệm VRAM, hoặc bf16)
USE_INT8_MODELS = globals().get("USE_INT8_MODELS", True)

if USE_INT8_MODELS:
    UNET_FILENAME         = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
    TEXT_ENCODER_FILENAME = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
else:
    UNET_FILENAME         = "ltx-2.5-22b-distilled-transformer-bf16.safetensors"
    TEXT_ENCODER_FILENAME = "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"

VIDEO_VAE_FILENAME        = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME        = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"


def dl(url, dest, fname, connections=8, gated=False):
    """Tải file song song bằng aria2c nếu file chưa tồn tại."""
    Path(dest).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(dest, fname)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 1024 * 1024 * 5:
        with _print_lock:
            print(f"⏭️  Đã có sẵn: {fname}")
        return True

    with _print_lock:
        print(f"⬇️  Bắt đầu tải: {fname}")

    cmd = [
        "aria2c", "--console-log-level=warn", "-c",
        "-x", str(connections), "-s", str(connections), "-k", "1M",
        "-d", dest, "-o", fname,
    ]
    if gated:
        cmd += ["--header", AUTH_HEADER]
    cmd.append(url)

    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = max(time.time() - t0, 0.01)
    ok = result.returncode == 0 and os.path.exists(file_path)

    with _print_lock:
        if ok:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✅ Xong: {fname} ({size_mb:.0f}MB trong {elapsed:.0f}s, ~{size_mb / elapsed:.1f}MB/s)")
        else:
            _FAILED_DOWNLOADS.append(fname)
            hint = ""
            if gated and ("401" in (result.stderr or "") or "403" in (result.stderr or "")):
                hint = " (Lỗi xác thực 401/403: Kiểm tra HF_TOKEN và bấm Agree access repo tại HuggingFace)"
            print(f"⚠️ Tải thất bại: {fname}{hint}")
    return ok


DOWNLOAD_JOBS = [
    # 1. Diffusion Model (UNet Distilled)
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/{UNET_FILENAME}",
     f"{COMFYUI_ROOT}/models/diffusion_models", UNET_FILENAME, True),

    # 2. Text Encoder (Gemma with Projection)
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_FILENAME}",
     f"{COMFYUI_ROOT}/models/text_encoders", TEXT_ENCODER_FILENAME, True),

    # 3. Video VAE
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{VIDEO_VAE_FILENAME}",
     f"{COMFYUI_ROOT}/models/vae", VIDEO_VAE_FILENAME, True),

    # 4. Audio VAE (Mã hóa âm thanh đầu vào thành latent audio)
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{AUDIO_VAE_FILENAME}",
     f"{COMFYUI_ROOT}/models/vae", AUDIO_VAE_FILENAME, True),

    # 5. Spatial Upscaler x2 (Stage 2 High-Res Refiner)
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/{SPATIAL_UPSCALER_FILENAME}",
     f"{COMFYUI_ROOT}/models/latent_upscale_models", SPATIAL_UPSCALER_FILENAME, True),
]

# Tải song song tối đa 3 file, 8 luồng/file
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(dl, url, dest, fname, 8, gated) for url, dest, fname, gated in DOWNLOAD_JOBS]
    concurrent.futures.wait(futures)

# --------------------------------------------------------------------------
# [4/4] Kiểm tra tổng kết & Khởi động sẵn sàng
# --------------------------------------------------------------------------
if _FAILED_DOWNLOADS:
    log(f"⚠️ Có {len(_FAILED_DOWNLOADS)} file tải không thành công: {', '.join(_FAILED_DOWNLOADS)}", color="#f44336")
    log("👉 Hãy kiểm tra lại HF_TOKEN, đảm bảo đã nhấn 'Agree and access' trên Hugging Face rồi chạy lại Cell 1.", color="#f44336")
else:
    log("🎉 [Cell 1 Hoàn Tất] Môi trường ComfyUI & Models LTX-2.5 A2V đã sẵn sàng!", color="#00e676")
    log("👉 Tiếp theo: Chạy file 'ltx/ltx2_5_a2v.py' (Cell 2) để mở giao diện A2V Studio.", color="#00b0ff")
