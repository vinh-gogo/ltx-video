#@title 📦 Cell 1: Cài đặt ComfyUI + Tải Models LTX-2.5 (MSR, Ingredients, Two-Stage I2V/T2V, Spatial Upscaler)
# ==============================================================================
# Cell 1: Tự động thiết lập toàn bộ môi trường ComfyUI, cài các custom nodes
# và tải các model weights cần thiết cho Lightricks LTX-2.5 Studio (MSR & Ingredients).
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
    """Chạy lệnh shell, tương thích Colab và local."""
    try:
        get_ipython().system(cmd)
    except NameError:
        os.system(cmd)


def pip_install(pkgs, use_uv=True):
    """Cài package bằng uv (tốc độ cao), tự động fallback sang pip."""
    if use_uv:
        ret = os.system(f"uv pip install -q --system {pkgs}")
        if ret == 0:
            return
        log(f"⚠️ uv gặp lỗi, đang fallback sang pip tiêu chuẩn cho: {pkgs}", color="#ffb300")
    os.system(f"pip install -q {pkgs}")


def torch_cuda_ready():
    """Kiểm tra môi trường có sẵn Torch CUDA không."""
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


# --------------------------------------------------------------------------
# [0/4] Kiểm tra Hugging Face Access Token (Gated Models)
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
        "Đồng thời nhớ bấm 'Agree and access repository' tại 2 repo này:\n"
        "  👉 1) https://huggingface.co/Lightricks/LTX-2.5\n"
        "  👉 2) https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients\n",
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
    "onnx opencv-python onnxruntime tqdm ipywidgets gradio"
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
# [2/4] Cài đặt Custom Nodes cho LTX-2.5 Studio
# --------------------------------------------------------------------------
log("[2/4] Cài đặt các Custom Nodes mở rộng (MSR, Ingredients, KJNodes, VHS)...")

CUSTOM_NODES = [
    ("https://github.com/Lightricks/ComfyUI-LTXVideo", "ComfyUI-LTXVideo"),
    ("https://github.com/liconstudio/ComfyUI-LTX2.5-MSR", "ComfyUI-LTX2.5-MSR"),
    ("https://github.com/kijai/ComfyUI-PromptRelay", "ComfyUI-PromptRelay"),
    ("https://github.com/kijai/ComfyUI-KJNodes", "ComfyUI-KJNodes"),
    ("https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite", "ComfyUI-VideoHelperSuite"),
    ("https://github.com/city96/ComfyUI-GGUF", "ComfyUI-GGUF"),
    ("https://github.com/kijai/ComfyUI-MelBandRoFormer", "ComfyUI-MelBandRoFormer"),
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
# [3/4] Tải Model Weights LTX-2.5 (MSR, Ingredients, Two-Stage Upscaler)
# --------------------------------------------------------------------------
log("[3/4] Đang tải Model Weights (UNet, Text Encoder, VAEs, LoRAs, Upscaler)...")

_FAILED_DOWNLOADS = []
_print_lock = threading.Lock()

# Tên model mặc định theo chuẩn ComfyUI và Blueprint
UNET_FILENAME             = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
TEXT_ENCODER_FILENAME     = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
VIDEO_VAE_FILENAME        = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME        = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

# Character Consistency LoRAs:
# 1. Licon MSR LoRA (Multi-Subject Reference)
MSR_LORA_FILENAME         = "LTX-2.5-Licon-MSR-V1.safetensors"
# 2. Official Lightricks Ingredients LoRA (Reference Sheet)
INGREDIENTS_LORA_FILENAME = "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"
# 3. Real-ESRGAN x4 Post-processing Upscaler
REALESRGAN_FILENAME       = "RealESRGAN_x4.pth"


def dl(url, dest, fname, connections=8, gated=False):
    """Tải file song song bằng aria2c nếu chưa có."""
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
    # 1. Diffusion Model (UNet int8 convrot) ~22GB
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/{UNET_FILENAME}",
     f"{COMFYUI_ROOT}/models/diffusion_models", UNET_FILENAME, True),

    # 2. Text Encoder (Gemma int8 convrot) ~12GB
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_FILENAME}",
     f"{COMFYUI_ROOT}/models/text_encoders", TEXT_ENCODER_FILENAME, True),

    # 3. Video VAE
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{VIDEO_VAE_FILENAME}",
     f"{COMFYUI_ROOT}/models/vae", VIDEO_VAE_FILENAME, True),

    # 4. Audio VAE
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{AUDIO_VAE_FILENAME}",
     f"{COMFYUI_ROOT}/models/vae", AUDIO_VAE_FILENAME, True),

    # 5. Spatial Upscaler x2 (Stage 2 High-Res Refiner)
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/{SPATIAL_UPSCALER_FILENAME}",
     f"{COMFYUI_ROOT}/models/latent_upscale_models", SPATIAL_UPSCALER_FILENAME, True),

    # 6. MSR LoRA (Multi-Subject Reference)
    ("https://huggingface.co/LiconStudio/LTX-2.5-Multiple-Subject-Reference/resolve/main/LTX-2.5-Licon-MSR-V1.safetensors",
     f"{COMFYUI_ROOT}/models/loras/ltx2.5", MSR_LORA_FILENAME, False),

    # 7. Official Ingredients IC-LoRA (Lightricks Character Reference Sheet) — GATED!
    ("https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients/resolve/main/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
     f"{COMFYUI_ROOT}/models/loras", INGREDIENTS_LORA_FILENAME, True),

    # 8. Real-ESRGAN x4
    ("https://huggingface.co/ai-forever/Real-ESRGAN/resolve/main/RealESRGAN_x4.pth",
     f"{COMFYUI_ROOT}/models/upscale_models", REALESRGAN_FILENAME, False),
]

# Tải song song tối đa 3 file, 8 luồng/file
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(dl, url, dest, fname, 8, gated) for url, dest, fname, gated in DOWNLOAD_JOBS]
    concurrent.futures.wait(futures)

# Đồng bộ LoRA giữa models/loras/ và models/loras/ltx2.5/ để ComfyUI nhận diện cả 2
try:
    _lora_dir = os.path.join(COMFYUI_ROOT, "models", "loras")
    _sub_dir = os.path.join(_lora_dir, "ltx2.5")
    os.makedirs(_sub_dir, exist_ok=True)
    _src = os.path.join(_sub_dir, "LTX-2.5-Licon-MSR-V1.safetensors")
    _dst = os.path.join(_lora_dir, "LTX-2.5-Licon-MSR-V1.safetensors")
    if os.path.exists(_src) and not os.path.exists(_dst):
        try:
            os.symlink(_src, _dst)
        except Exception:
            import shutil; shutil.copy2(_src, _dst)
    elif os.path.exists(_dst) and not os.path.exists(_src):
        try:
            os.symlink(_dst, _src)
        except Exception:
            import shutil; shutil.copy2(_dst, _src)
except Exception:
    pass

# --------------------------------------------------------------------------
# [4/4] Báo cáo kết quả
# --------------------------------------------------------------------------
critical_fails = [f for f in _FAILED_DOWNLOADS if f != INGREDIENTS_LORA_FILENAME]

if critical_fails:
    log(
        f"❌ Có {len(critical_fails)} file cốt lõi tải lỗi: {', '.join(critical_fails)}.\n"
        "Vui lòng kiểm tra lại quyền truy cập repo https://huggingface.co/Lightricks/LTX-2.5 và chạy lại Cell này.",
        color="#ff5252"
    )
elif INGREDIENTS_LORA_FILENAME in _FAILED_DOWNLOADS:
    display(HTML(
        "<div style='padding:15px;background-color:#fff3e0;border-left:5px solid #ff9800;"
        "border-radius:4px;color:#e65100;font-family:sans-serif;'>"
        "<b>⚠️ Lưu ý về Ingredients IC-LoRA:</b> File <code>ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors</code> chưa tải được.<br>"
        "👉 Để dùng chế độ Ingredients, bạn cần vào link: <a href='https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients' target='_blank'><b>https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients</b></a> và bấm <b>'Agree and access repository'</b>, sau đó chạy lại Cell này.<br>"
        "<b>✅ TUY NHIÊN:</b> Toàn bộ các model cho <b>MSR 2-Stage</b> và <b>Cinema Two-Stage</b> đã tải xong 100%! Bạn có thể chuyển sang <b>Cell 2 (%run ltx/ltx2_5_msr.py)</b> để tạo video ngay lập tức!"
        "</div>"
    ))
else:
    display(HTML(
        "<div style='padding:15px;background-color:#e8f5e9;border-left:5px solid #4caf50;"
        "border-radius:4px;color:#2e7d32;font-family:sans-serif;'>"
        "<b>✨ Initialization Complete!</b> Hệ thống LTX-2.5 Studio đã sẵn sàng.<br>"
        "🧬 <b>MSR LoRA:</b> <code>models/loras/ltx2.5/LTX-2.5-Licon-MSR-V1.safetensors</code><br>"
        "🧪 <b>Ingredients IC-LoRA:</b> <code>models/loras/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors</code><br>"
        "📦 <b>Core Models:</b> Transformer (int8-convrot) + Gemma (int8-convrot) + Video/Audio VAEs + Spatial Upscaler x2<br>"
        "👉 Sẵn sàng chuyển sang <b>Cell 2 (%run ltx/ltx2_5_msr.py)</b> để khởi chạy Gradio Live Studio!"
        "</div>"
    ))
