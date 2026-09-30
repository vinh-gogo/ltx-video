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
UNET_FILENAME              = globals().get("UNET_FILENAME", "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors")
TEXT_ENCODER_BF16_FILENAME  = "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
TEXT_ENCODER_INT8_FILENAME  = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
TEXT_ENCODER_FILENAME      = globals().get("TEXT_ENCODER_FILENAME", TEXT_ENCODER_BF16_FILENAME)
VIDEO_VAE_FILENAME         = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME         = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME  = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

# Character Consistency LoRAs & Fast Inference:
# 1. Licon MSR LoRA (Multi-Subject Reference)
MSR_LORA_FILENAME          = "LTX-2.5-Licon-MSR-V1.safetensors"
# 2. Official Lightricks Distilled LoRA 450 (8-step fast inference)
DISTILLED_LORA_FILENAME    = "ltx-2.5-22b-distilled-lora-450-bf16.safetensors"
# 3. Official Lightricks Refine Details IC-LoRA (Stage 2 Sharpness Refiner)
REFINE_DETAILS_LORA_FILENAME = "ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors"
# 4. Official Lightricks Ingredients LoRA (Reference Sheet)
INGREDIENTS_LORA_FILENAME  = "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"
# 5. Real-ESRGAN x4 Post-processing Upscaler
REALESRGAN_FILENAME        = "RealESRGAN_x4.pth"

# Cấu hình tải Text Encoder:
# Mặc định tải bản BF16 chính thức (24GB). Nếu DOWNLOAD_INT8_TEXT_ENCODER=True, tải thêm bản INT8 (12GB) để dự phòng.
DOWNLOAD_INT8_TEXT_ENCODER = globals().get("DOWNLOAD_INT8_TEXT_ENCODER", True)


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

    # 2. Text Encoder BF16 (Gemma 4 12B with Proj - Chuẩn cao cấp) ~24GB
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_BF16_FILENAME}",
     f"{COMFYUI_ROOT}/models/text_encoders", TEXT_ENCODER_BF16_FILENAME, True),
]

if DOWNLOAD_INT8_TEXT_ENCODER:
    DOWNLOAD_JOBS.append((
        f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_INT8_FILENAME}",
        f"{COMFYUI_ROOT}/models/text_encoders", TEXT_ENCODER_INT8_FILENAME, True
    ))

DOWNLOAD_JOBS.extend([
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

    # 7. Official Lightricks Distilled LoRA 450 (Fast 8-step inference LoRA)
    ("https://huggingface.co/Lightricks/LTX-2.5/resolve/main/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors",
     f"{COMFYUI_ROOT}/models/loras", DISTILLED_LORA_FILENAME, True),

    # 8. Official Lightricks IC-LoRA Refine Details (Stage 2 Super Sharpness Refiner)
    ("https://huggingface.co/Lightricks/LTX-2.5-22b-IC-LoRA-Refine-Details/resolve/main/ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors",
     f"{COMFYUI_ROOT}/models/loras", REFINE_DETAILS_LORA_FILENAME, True),

    # 9. Official Ingredients IC-LoRA (Lightricks Character Reference Sheet) — GATED!
    ("https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients/resolve/main/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors",
     f"{COMFYUI_ROOT}/models/loras", INGREDIENTS_LORA_FILENAME, True),

    # 10. Real-ESRGAN x4
    ("https://huggingface.co/ai-forever/Real-ESRGAN/resolve/main/RealESRGAN_x4.pth",
     f"{COMFYUI_ROOT}/models/upscale_models", REALESRGAN_FILENAME, False),
])

# Tải song song tối đa 3 file, 8 luồng/file
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(dl, url, dest, fname, 8, gated) for url, dest, fname, gated in DOWNLOAD_JOBS]
    concurrent.futures.wait(futures)

# Đồng bộ LoRA giữa models/loras/ và models/loras/ltx2.5/ để ComfyUI nhận diện cả 2
try:
    _lora_dir = os.path.join(COMFYUI_ROOT, "models", "loras")
    _sub_dir = os.path.join(_lora_dir, "ltx2.5")
    os.makedirs(_sub_dir, exist_ok=True)
    for _fname in [MSR_LORA_FILENAME, DISTILLED_LORA_FILENAME, REFINE_DETAILS_LORA_FILENAME]:
        _src = os.path.join(_sub_dir, _fname)
        _dst = os.path.join(_lora_dir, _fname)
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

# Đồng bộ Text Encoders giữa models/text_encoders/ và models/clip/ để CLIPLoader luôn nhận diện được
try:
    _te_dir = os.path.join(COMFYUI_ROOT, "models", "text_encoders")
    _clip_dir = os.path.join(COMFYUI_ROOT, "models", "clip")
    os.makedirs(_te_dir, exist_ok=True)
    os.makedirs(_clip_dir, exist_ok=True)
    for _fname in [TEXT_ENCODER_BF16_FILENAME, TEXT_ENCODER_INT8_FILENAME]:
        _src = os.path.join(_te_dir, _fname)
        _dst = os.path.join(_clip_dir, _fname)
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
critical_fails = [f for f in _FAILED_DOWNLOADS if f not in (INGREDIENTS_LORA_FILENAME, DISTILLED_LORA_FILENAME, REFINE_DETAILS_LORA_FILENAME, TEXT_ENCODER_INT8_FILENAME)]

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
        "⚡ <b>Distilled LoRA 450:</b> <code>models/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors</code><br>"
        "✨ <b>Refine Details LoRA:</b> <code>models/loras/ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors</code><br>"
        "🧪 <b>Ingredients IC-LoRA:</b> <code>models/loras/ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors</code><br>"
        "🔤 <b>Text Encoder:</b> Gemma 4 12B (BF16 & INT8 trong <code>models/text_encoders/</code>)<br>"
        "📦 <b>Core Models:</b> Transformer (int8-convrot) + Video/Audio VAEs + Spatial Upscaler x2<br>"
        "👉 Sẵn sàng chuyển sang <b>Cell 2 (%run ltx/ltx2_5_msr.py)</b> để khởi chạy Gradio Live Studio!"
        "</div>"
    ))
