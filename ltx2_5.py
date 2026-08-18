# @title [Cell 1] Cài đặt môi trường ComfyUI + LTX-2.5

import concurrent.futures
import os
import subprocess
import threading
import time
from getpass import getpass
from pathlib import Path
from IPython.display import display, HTML


def log(msg, color="#00e676"):
    display(HTML(f"<p style='color:{color}; font-weight:bold;'>{msg}</p>"))


def sh(cmd):
    """Chạy 1 lệnh shell, in trực tiếp output (không nuốt log) để thấy tiến trình thật."""
    get_ipython().system(cmd)


def pip_install(pkgs, use_uv=True):
    """Cài package bằng uv (nhanh hơn pip resolver gốc rất nhiều). Tự fallback về pip nếu uv lỗi."""
    if use_uv:
        ret = os.system(f"uv pip install -q --system {pkgs}")
        if ret == 0:
            return
        log(f"⚠️ uv lỗi, fallback sang pip cho: {pkgs}", color="#ffb300")
    os.system(f"pip install -q {pkgs}")


def torch_cuda_ready():
    """Kiểm tra Colab đã có sẵn torch bản GPU chưa, để tránh tải lại ~2-4GB không cần thiết."""
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


# --------------------------------------------------------------------------
# [0/4] Lấy Hugging Face Access Token — BẮT BUỘC vì Lightricks/LTX-2.5 (và
# LoRA Ingredients bên dưới) đều bị gate
# --------------------------------------------------------------------------
log("[0/4] Kiểm tra Hugging Face Access Token...")

HF_TOKEN = None
try:
    from google.colab import userdata  # chỉ có trong môi trường Colab
    HF_TOKEN = userdata.get("HF_TOKEN")
    if HF_TOKEN:
        log("✅ Đã lấy HF_TOKEN từ Colab Secrets (biểu tượng 🔑 bên trái).")
except Exception:
    pass

if not HF_TOKEN:
    HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    log(
        "🔑 Chưa tìm thấy HF_TOKEN. Dán access token của bạn vào ô bên dưới "
        "(token này KHÔNG hiển thị ra màn hình). Lấy token tại: "
        "https://huggingface.co/settings/tokens — và nhớ bấm 'Agree and access "
        "repository' tại CẢ HAI trang sau trước khi chạy tiếp:\n"
        "  1) https://huggingface.co/Lightricks/LTX-2.5\n"
        "  2) https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients "
        "(nếu muốn dùng LoRA giữ nhân vật ở bước [3/4] bên dưới)",
        color="#ffb300",
    )
    HF_TOKEN = getpass("Dán Hugging Face token rồi nhấn Enter: ").strip()

if not HF_TOKEN:
    raise RuntimeError(
        "❌ Không có HF_TOKEN thì không tải được model LTX-2.5 (repo bị gate). "
        "Hãy chạy lại cell và dán token hợp lệ."
    )

os.environ["HF_TOKEN"] = HF_TOKEN
AUTH_HEADER = f"Authorization: Bearer {HF_TOKEN}"

# Bật/tắt việc tải LoRA giữ nhân vật. Để False nếu bạn chỉ muốn dùng bản gốc
# không LoRA, hoặc muốn tự upload LoRA của riêng bạn (đã train từ nhân vật cụ
# thể) thẳng vào /content/ComfyUI/models/loras/ sau này.
DOWNLOAD_CHARACTER_LORA = False

# --------------------------------------------------------------------------
# [1/4] Cài thư viện lõi + clone/cập nhật ComfyUI
# --------------------------------------------------------------------------
log("[1/4] Installing core dependencies...")
sh("pip install -q uv")  # cài uv trước, dùng cho mọi bước pip install sau này

if torch_cuda_ready():
    import torch
    log(f"✅ Đã có sẵn Torch {torch.__version__} (CUDA) -> bỏ qua cài lại, tiết kiệm ~2-4 phút")
else:
    log("⏳ Chưa có Torch CUDA sẵn -> đang cài (bước này thường lâu nhất)...")
    pip_install("torch torchvision torchaudio")

pip_install(
    "torchsde einops diffusers accelerate av spandrel albumentations "
    "onnx opencv-python onnxruntime tqdm ipywidgets"
)

if not os.path.exists("/content/ComfyUI"):
    sh("git clone -q https://github.com/comfyanonymous/ComfyUI")
else:
    log("🔄 ComfyUI đã tồn tại -> git pull để lấy bản mới nhất (LTX-2.5 cần bản nightly)...")
    sh("cd /content/ComfyUI && git pull -q")
pip_install("-r /content/ComfyUI/requirements.txt")
sh("apt-get -y install -qq aria2 > /dev/null 2>&1")

# --------------------------------------------------------------------------
# [2/4] Clone/cập nhật custom nodes
# --------------------------------------------------------------------------
# LƯU Ý: các node lõi của pipeline LTX-2.5 (LTXVAddGuide, LTXVConcatAVLatent,
# LTXVSeparateAVLatent, LTXVAudioVAEDecode...) giờ nằm trong CHÍNH ComfyUI
# core (cnr_id "comfy-core"), không còn phụ thuộc custom node ComfyUI-LTXVideo
# để hoạt động cơ bản. Vẫn giữ lại các custom node bên dưới vì: KJNodes vẫn
# cần cho preview/tiny-VAE, ComfyUI-LTXVideo vẫn cần cho IC-LoRA control
# (canny/depth/HDR...) nếu bạn dùng sau này, VideoHelperSuite cần cho việc
# xử lý video. ComfyUI-GGUF được giữ lại (không bắt buộc với luồng chính
# int8-convrot) phòng khi bạn muốn thử GGUF quant cộng đồng sau này.
# LoraLoaderModelOnly (dùng để nạp LoRA giữ nhân vật ở Cell 2) là node LÕI có
# sẵn trong ComfyUI, KHÔNG cần custom node riêng.
log("[2/4] Cloning/updating custom nodes...")
get_ipython().run_line_magic("cd", "-q /content/ComfyUI/custom_nodes")

CUSTOM_NODES = [
    "https://github.com/kijai/ComfyUI-KJNodes",
    "https://github.com/city96/ComfyUI-GGUF",
    "https://github.com/Lightricks/ComfyUI-LTXVideo/",
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite",
    "https://github.com/kijai/ComfyUI-MelBandRoFormer",
]
for repo_url in CUSTOM_NODES:
    node_name = repo_url.rstrip("/").split("/")[-1]
    if os.path.exists(node_name):
        sh(f"cd {node_name} && git pull -q && cd ..")
    else:
        sh(f"git clone -q {repo_url}")
    req_file = f"{node_name}/requirements.txt"
    if os.path.exists(req_file):
        pip_install(f"-r {req_file}")

# --------------------------------------------------------------------------
# [3/4] Tải model weights cho LTX-2.5 + LoRA giữ nhân vật (song song, có log tiến trình)
# --------------------------------------------------------------------------
log("[3/4] Fetching LTX-2.5 model weights (this may take a while — tổng ~40GB)...")

_FAILED_DOWNLOADS = []
_print_lock = threading.Lock()

# Tên file dùng chung cho toàn bộ notebook — Cell 2 đọc lại các biến này.
# Cấu hình mặc định: bản "distilled" (đã tối ưu số bước, KHÔNG cần LoRA
# distill riêng như pipeline LTX-2.3 cũ) — đây là cấu hình ComfyUI chính
# thức khuyến nghị cho cả 3 workflow T2V/I2V/FLF2V.
UNET_FILENAME = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
TEXT_ENCODER_FILENAME = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
TEXT_ENCODER_ENHANCER_FILENAME = "gemma4_e2b_it_bf16.safetensors"  # dùng riêng cho Prompt Enhancer, không phải dual-clip
VIDEO_VAE_FILENAME = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

# LoRA giữ đồng bộ nhân vật/props/bối cảnh xuyên suốt (IC-LoRA "Ingredients").
# Repo: Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients (train trên 2.3, Lightricks
# xác nhận đa số chạy tốt trên 2.5 nhưng khuyến cáo tự kiểm chứng).
# Cường độ khuyến nghị chính chủ: strength = 1.0 (Cell 2 đặt sẵn mặc định này).
CHARACTER_LORA_REPO = "Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients"
CHARACTER_LORA_FILENAME = "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors"

# LoRA distilled chính thức của Lightricks cho LTX-2.5 (bf16, checkpoint 450).
# Dùng như LoRA #1/#2 thông thường (LoraLoaderModelOnly) — KHÔNG phải IC-LoRA
# Ingredients (không cần ảnh tham khảo). Repo: Lightricks/LTX-2.5-Diffusers.
# Bật True để tải tự động; False nếu bạn không cần hoặc muốn tải thủ công.
DOWNLOAD_DISTILLED_LORA = True
DISTILLED_LORA_REPO = "Lightricks/LTX-2.5-Diffusers"
DISTILLED_LORA_FILENAME = "ltx-2.5-22b-distilled-lora-450-bf16.safetensors"


def dl(url, dest, fname, connections=8, gated=False):
    """Tải 1 file bằng aria2c nếu chưa có. An toàn để gọi song song từ nhiều thread.
    gated=True -> gắn header Authorization (bắt buộc cho mọi file trong
    Lightricks/LTX-2.5 và Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients, vì cả 2
    repo đều yêu cầu đăng nhập + accept license riêng)."""
    Path(dest).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(dest, fname)
    if os.path.exists(file_path):
        with _print_lock:
            print(f"⏭️  Đã có sẵn, bỏ qua: {fname}")
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
            print(f"✅ Xong: {fname}  ({size_mb:.0f}MB trong {elapsed:.0f}s, ~{size_mb / elapsed:.1f}MB/s)")
        else:
            _FAILED_DOWNLOADS.append(fname)
            hint = ""
            if gated and ("401" in (result.stderr or "") or "403" in (result.stderr or "")):
                hint = (" (lỗi xác thực — kiểm tra lại HF_TOKEN và đã bấm 'Agree and access "
                        "repository' đúng trang repo của file này chưa)")
            print(f"⚠️ Tải thất bại: {fname}{hint}")
    return ok


# Danh sách file cần tải: (url, thư mục đích, tên file, có bị gate hay không)
DOWNLOAD_JOBS = [
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/{UNET_FILENAME}",
     "/content/ComfyUI/models/diffusion_models", UNET_FILENAME, True),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_FILENAME}",
     "/content/ComfyUI/models/text_encoders", TEXT_ENCODER_FILENAME, True),
    (f"https://huggingface.co/Comfy-Org/gemma-4/resolve/main/text_encoders/{TEXT_ENCODER_ENHANCER_FILENAME}",
     "/content/ComfyUI/models/text_encoders", TEXT_ENCODER_ENHANCER_FILENAME, False),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{VIDEO_VAE_FILENAME}",
     "/content/ComfyUI/models/vae", VIDEO_VAE_FILENAME, True),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{AUDIO_VAE_FILENAME}",
     "/content/ComfyUI/models/vae", AUDIO_VAE_FILENAME, True),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/{SPATIAL_UPSCALER_FILENAME}",
     "/content/ComfyUI/models/latent_upscale_models", SPATIAL_UPSCALER_FILENAME, True),
]

if DOWNLOAD_CHARACTER_LORA:
    DOWNLOAD_JOBS.append((
        f"https://huggingface.co/{CHARACTER_LORA_REPO}/resolve/main/{CHARACTER_LORA_FILENAME}",
        "/content/ComfyUI/models/loras", CHARACTER_LORA_FILENAME, True,
    ))
else:
    log("ℹ️ DOWNLOAD_CHARACTER_LORA=False -> bỏ qua tải LoRA giữ nhân vật. "
        "Bạn có thể tự copy LoRA .safetensors của mình vào "
        "/content/ComfyUI/models/loras/ rồi chọn trong dropdown ở Cell 2.",
        color="#90caf9")

if DOWNLOAD_DISTILLED_LORA:
    DOWNLOAD_JOBS.append((
        f"https://huggingface.co/{DISTILLED_LORA_REPO}/resolve/main/{DISTILLED_LORA_FILENAME}",
        "/content/ComfyUI/models/loras", DISTILLED_LORA_FILENAME, True,
    ))
else:
    log("ℹ️ DOWNLOAD_DISTILLED_LORA=False -> bỏ qua tải LoRA distilled chính thức. "
        "Tự copy vào /content/ComfyUI/models/loras/ nếu cần.",
        color="#90caf9")

# Tải tối đa 3 file cùng lúc, 8 luồng/file.
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(dl, url, dest, fname, 8, gated) for url, dest, fname, gated in DOWNLOAD_JOBS]
    concurrent.futures.wait(futures)

# --------------------------------------------------------------------------
# [4/4] Tổng kết
# --------------------------------------------------------------------------
if _FAILED_DOWNLOADS:
    lora_hint = ""
    if DOWNLOAD_CHARACTER_LORA and CHARACTER_LORA_FILENAME in _FAILED_DOWNLOADS:
        lora_hint = (f"<br>⚠️ Riêng LoRA giữ nhân vật cần bạn bấm 'Agree and access repository' tại "
                     f"https://huggingface.co/{CHARACTER_LORA_REPO} (đây là license RIÊNG, khác với "
                     f"license của Lightricks/LTX-2.5).")
    if DOWNLOAD_DISTILLED_LORA and DISTILLED_LORA_FILENAME in _FAILED_DOWNLOADS:
        lora_hint += (f"<br>⚠️ Riêng LoRA distilled chính thức cần bạn bấm 'Agree and access repository' tại "
                      f"https://huggingface.co/{DISTILLED_LORA_REPO}.")
    log(f"⚠️ {len(_FAILED_DOWNLOADS)} file tải lỗi: {', '.join(_FAILED_DOWNLOADS)}. "
        f"Kiểm tra HF_TOKEN + đã accept license repo chưa, rồi chạy lại cell này "
        f"(file đã tải xong sẽ tự bỏ qua) trước khi qua Cell 2.{lora_hint}",
        color="#ff5252")
else:
    lora_note = (
        "<br>🎭 LoRA giữ nhân vật (Ingredients IC-LoRA) đã sẵn sàng trong "
        "<code>models/loras/</code> — chọn nó ở mục '🎭 LoRA giữ nhân vật/phong cách' trong Cell 2. "
        "Cường độ khuyến nghị: 1.0."
        if DOWNLOAD_CHARACTER_LORA else
        "<br>ℹ️ Chưa tải LoRA giữ nhân vật (đã tắt DOWNLOAD_CHARACTER_LORA)."
    )
    distilled_lora_note = (
        "<br>🚀 LoRA distilled chính thức (<code>ltx-2.5-22b-distilled-lora-450-bf16</code>) đã sẵn sàng "
        "trong <code>models/loras/</code> — chọn ở LoRA #1 trong Cell 2, cường độ khuyến nghị: 1.0."
        if DOWNLOAD_DISTILLED_LORA else
        "<br>ℹ️ Chưa tải LoRA distilled chính thức (đã tắt DOWNLOAD_DISTILLED_LORA)."
    )
    display(HTML(
        "<div style='padding:15px;background-color:#e8f5e9;border-left:5px solid #4caf50;"
        "border-radius:4px;color:#2e7d32;font-family:sans-serif;'>"
        "<b>✨ Initialization Complete!</b> Môi trường LTX-2.5 đã sẵn sàng."
        f"{lora_note}"
        f"{distilled_lora_note}"
        "<br><small>⚠️ Nhắc lại: transformer + text encoder chính ~37GB VRAM/weights — "
        "cần GPU 24GB+ (L4/A100). Trên T4 16GB nhiều khả năng sẽ OOM dù bật Low VRAM Mode.</small>"
        "<br><small>⚠️ LoRA Ingredients được train trên LTX-2.3; Lightricks xác nhận đa số "
        "LoRA/IC-LoRA 2.3 chạy được trên 2.5 nhưng khuyến cáo tự kiểm chứng chất lượng trước khi "
        "dùng cho công việc quan trọng.</small>"
        "</div>"
    ))

# @title [Cell 2] LTX-2.5 AI Video Studio — v0.5.0

get_ipython().system("pip install -q gradio opencv-python")

import copy
import glob
import json
import math
import os
import random
import re
import shutil
import socket
import subprocess
import time
import urllib.request

import cv2
import gradio as gr

# ==========================================================================
# CẤU HÌNH CHUNG
# ==========================================================================
INPUT_DIR = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"
LORA_DIR = "/content/ComfyUI/models/loras/"

UNET_FILENAME = globals().get("UNET_FILENAME", "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors")
TEXT_ENCODER_FILENAME = globals().get("TEXT_ENCODER_FILENAME", "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors")
VIDEO_VAE_FILENAME = globals().get("VIDEO_VAE_FILENAME", "ltx-2.5-video-vae-bf16.safetensors")
AUDIO_VAE_FILENAME = globals().get("AUDIO_VAE_FILENAME", "ltx-2.5-audio-vae-bf16.safetensors")
SPATIAL_UPSCALER_FILENAME = globals().get("SPATIAL_UPSCALER_FILENAME", "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors")
_DEFAULT_CHARACTER_LORA = globals().get("CHARACTER_LORA_FILENAME", None)   # do Cell 1 tải, nếu có
_DEFAULT_DISTILLED_LORA = globals().get("DISTILLED_LORA_FILENAME", None)   # LoRA distilled chính thức, nếu Cell 1 đã tải

MAX_FLF_SB_SCENES = 20
LATENT_GROUP_FRAMES = 8
PASS2_FIXED_NOISE_SEED = 42

SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.85, 0.7250, 0.4219, 0.0"

NEGATIVE_PROMPT_DEFAULT = (
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, jpeg artifacts, glitches, watermark, text, logo, signature, "
    "copyright, subtitles, distorted sound, saturated sound, loud"
)

NO_LORA_LABEL = "(Không dùng)"

CHAR_MODE_SMOOTH = "🔗 Nối cảnh mượt (mặc định — khung cuối cảnh trước)"
CHAR_MODE_STRICT = "🎯 Bám nhân vật 100% (luôn dùng ảnh tham khảo cố định)"
CHAR_MODE_PERIODIC = "⚖️ Kết hợp: bám lại ảnh tham khảo mỗi N cảnh"
CHAR_MODE_CHOICES = [CHAR_MODE_SMOOTH, CHAR_MODE_STRICT, CHAR_MODE_PERIODIC]

# ==========================================================================
# HÀM TIỆN ÍCH DÙNG CHUNG
# ==========================================================================
def is_server_running(port=8188):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


_SERVER_STATE = {"running_low_vram": None}
_COMFY_NODES = None  # cache danh sách node ComfyUI, reset khi server restart


def _get_comfy_nodes():
    """Lazy-load danh sách node types từ ComfyUI API (gọi 1 lần/session).
    Trả về set tên node, hoặc set rỗng nếu không lấy được."""
    global _COMFY_NODES
    if _COMFY_NODES is None:
        try:
            resp = urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8188/object_info"), timeout=10)
            _COMFY_NODES = set(json.loads(resp.read()).keys())
        except Exception:
            _COMFY_NODES = set()
    return _COMFY_NODES


def ensure_server(low_vram, boot_timeout=300):
    global _COMFY_NODES
    need_restart = (not is_server_running()) or (_SERVER_STATE["running_low_vram"] != low_vram)
    if not need_restart:
        return
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    _COMFY_NODES = None  # reset node cache sau khi server restart
    os.chdir("/content/ComfyUI")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    cmd = ["python", "main.py"]
    if low_vram:
        cmd.append("--cache-none")
    subprocess.Popen(cmd)
    waited = 0
    while not is_server_running():
        time.sleep(2)
        waited += 2
        if waited > boot_timeout:
            raise RuntimeError(f"Server không khởi động được sau {boot_timeout}s. Kiểm tra lại /content/ComfyUI.")
    _SERVER_STATE["running_low_vram"] = low_vram


def force_restart_server():
    global _COMFY_NODES
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    _SERVER_STATE["running_low_vram"] = None
    _COMFY_NODES = None  # reset node cache
    return "✅ Đã tắt server cũ để giải phóng VRAM. Lần tạo video tiếp theo sẽ tự khởi động lại."


def snap_fps_safe(fps):
    try:
        fps = float(fps)
    except (TypeError, ValueError):
        fps = 24.0
    safe = int(round(fps / LATENT_GROUP_FRAMES) * LATENT_GROUP_FRAMES)
    return max(LATENT_GROUP_FRAMES, safe)


def total_frames_for(duration_seconds, fps):
    return int(duration_seconds) * int(fps) + 1


def half_dims(width, height):
    """Kích thước cho PASS 1 (độ phân giải thấp, dùng để sample nhanh trước khi
    upscale x2 ở PASS 2). Làm tròn LÊN (ceiling) về bội số của 32 — thay vì làm
    tròn xuống như trước — để sau khi PASS 2 upscale x2, video đầu ra KHÔNG bao
    giờ bị hụt phân giải so với mức người dùng chọn (đảm bảo đạt tối thiểu 720p
    khi chọn preset HD 720p)."""
    def snap_half_up(v):
        v = int(v)
        half = v / 2.0
        return max(32, int(math.ceil(half / 32.0)) * 32)
    return snap_half_up(width), snap_half_up(height)


def extract_frame_at_percent(video_path, output_path, percent=100):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        last_frame = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            last_frame = frame
        cap.release()
        if last_frame is not None:
            cv2.imwrite(output_path, last_frame)
        return output_path

    target_index = max(0, min(total_frames - 1, int(round((percent / 100.0) * (total_frames - 1)))))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_index)
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        last_good = None
        idx = 0
        while True:
            ret2, f2 = cap.read()
            if not ret2:
                break
            last_good = f2
            if idx >= target_index:
                break
            idx += 1
        frame = last_good
    cap.release()
    if frame is not None:
        cv2.imwrite(output_path, frame)
    return output_path


def extract_audio_track(video_path, output_path):
    """Tách audio track từ 1 video ra file .wav — dùng làm 'giọng tham khảo'
    để khoá giọng nói cho các cảnh tiếp theo (tính năng Voice Lock thử nghiệm,
    xem apply_voice_lock() bên dưới). Trả về output_path nếu thành công, None
    nếu thất bại (vd video không có audio track)."""
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
           "-ar", "44100", "-ac", "1", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(output_path):
        return output_path
    return None


def split_prompts(text):
    if not text or not text.strip():
        return []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n[ \t]*\n+", normalized.strip())
    return [b.strip() for b in blocks if b.strip()]


def count_scenes(text):
    n = len(split_prompts(text))
    return f"🔹 **Số phân cảnh nhận diện được:** {n}"


def update_storyboard_flf_ui(text):
    count = min(len(split_prompts(text)), MAX_FLF_SB_SCENES)
    msg = f"🔹 **Phân cảnh nhận diện được:** {count}"
    first_updates, last_updates = [], []
    for i in range(MAX_FLF_SB_SCENES):
        if i < count:
            first_updates.append(gr.update(visible=True))
            last_updates.append(gr.update(visible=True))
        else:
            first_updates.append(gr.update(value=None, visible=False))
            last_updates.append(gr.update(value=None, visible=False))
    return [msg] + first_updates + last_updates


_ASPECT_RATIO_MAP = {
    "480x832": (480, 832),
    "832x480": (832, 480),
    "1280x720": (1280, 720),
    "720x1280": (720, 1280),
    "720x720": (720, 720),
}


def parse_aspect_ratio(ratio_str):
    for key, dims in _ASPECT_RATIO_MAP.items():
        if key in ratio_str:
            return dims
    return 512, 512


def safe_dims(width, height):
    """Làm tròn LÊN (ceiling) về bội số của 32 gần nhất — thay vì làm tròn gần
    nhất (round) như trước — để kích thước thực tế đưa vào workflow KHÔNG BAO
    GIỜ nhỏ hơn giá trị người dùng chọn. Ví dụ chọn 1280x720 sẽ luôn cho ra
    video có chiều tối thiểu 1280x736 (đạt/vượt chuẩn 720p), thay vì trước đây
    có thể bị làm tròn xuống còn 1280x704 (thấp hơn 720p)."""
    def snap_up(v):
        v = int(v)
        return max(256, int(math.ceil(v / 32.0)) * 32)
    return snap_up(width), snap_up(height)


def get_seed(v_seed):
    try:
        v = int(v_seed)
    except (TypeError, ValueError):
        v = -1
    return random.randint(1, 999999999) if v == -1 else v


# --------------------------------------------------------------------------
# LoRA: quét thư mục + helper chèn node vào workflow
# --------------------------------------------------------------------------
def list_available_loras():
    """Quét models/loras/ để lấy danh sách LoRA hiện có — bao gồm LoRA giữ
    nhân vật do Cell 1 tải (nếu có) và bất kỳ .safetensors nào bạn tự thêm
    vào (vd LoRA tự train riêng cho 1 nhân vật cụ thể)."""
    os.makedirs(LORA_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(LORA_DIR) if f.lower().endswith((".safetensors", ".pt", ".ckpt")))
    return [NO_LORA_LABEL] + files


def default_ic_lora_choice():
    """Mặc định cho dropdown 'IC-LoRA Ingredients' (KHÔNG dùng cho LoRA #1/#2
    thường nữa — xem changelog v0.5.0 ở đầu file). Tự chọn sẵn file Ingredients
    nếu Cell 1 đã tải nó, vì đây đúng là chỗ file đó nên được dùng."""
    choices = list_available_loras()
    if _DEFAULT_CHARACTER_LORA and _DEFAULT_CHARACTER_LORA in choices:
        return _DEFAULT_CHARACTER_LORA
    return NO_LORA_LABEL


def refresh_lora_dropdowns():
    choices = list_available_loras()
    return gr.update(choices=choices), gr.update(choices=choices)


def apply_lora_stack(wf, model_source, lora1_name, lora1_strength, lora2_name, lora2_strength, start_id=100):
    """Chèn tối đa 2 LoRA nối tiếp ngay sau UNETLoader bằng LoraLoaderModelOnly
    (node LÕI của ComfyUI). Dùng *ModelOnly* vì LoRA/IC-LoRA giữ nhân vật của
    LTX-2.5 chỉ train trên transformer (DiT: các lớp attention + feed-forward),
    KHÔNG động vào text encoder — nạp qua CLIP là thừa và có thể gây lệch.
    Trả về model_ref (["id", 0]) để gán vào input "model" của các node Guider.
    Nếu cả 2 lora_name đều là NO_LORA_LABEL/None thì trả nguyên model_source,
    workflow chạy y hệt bản không-LoRA.
    """
    model_ref = list(model_source)
    node_id = start_id
    for name, strength in ((lora1_name, lora1_strength), (lora2_name, lora2_strength)):
        if name and name != NO_LORA_LABEL:
            wf[str(node_id)] = {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {"model": model_ref, "lora_name": name, "strength_model": float(strength)},
            }
            model_ref = [str(node_id), 0]
            node_id += 1
    return model_ref


def encode_voice_reference(wf, audio_vae_ref, voice_ref_audio_name, start_id=200):
    """Mã hoá 1 audio tham khảo (LoadAudio + LTXVAudioVAEEncode) MỘT LẦN, để dùng
    lại cho cả pass 1 và pass 2 mà không tốn công mã hoá lại. Trả về
    (audio_latent_ref hoặc None, next_free_id)."""
    if not voice_ref_audio_name:
        return None, start_id
    node_load = str(start_id)
    node_encode = str(start_id + 1)
    wf[node_load] = {"class_type": "LoadAudio", "inputs": {"audio": voice_ref_audio_name}}
    wf[node_encode] = {"class_type": "LTXVAudioVAEEncode",
                        "inputs": {"audio": [node_load, 0], "audio_vae": audio_vae_ref}}
    return [node_encode, 0], start_id + 2


def set_audio_ref_tokens(wf, positive_ref, negative_ref, audio_latent_ref, start_id):
    """[THỬ NGHIỆM] Gắn 1 audio_latent tham khảo (đã mã hoá sẵn bằng
    encode_voice_reference) vào MỘT CẶP positive/negative cụ thể bằng
    LTXVSetAudioRefTokens, để ép model bám theo đúng 1 giọng nói xuyên suốt
    nhiều lượt generate riêng biệt (nhiều scene/segment/pass), thay vì để mỗi
    lần tự đoán ngẫu nhiên 1 giọng mới (dễ ra nam/nữ lẫn lộn). Có thể gọi lại
    nhiều lần (vd 1 lần/pass) với cùng audio_latent_ref.

    Đã đối chiếu với mã nguồn iclora.py mới nhất của ComfyUI-LTXVideo (tháng
    8/2026): node nhận đúng 3 input (positive, negative, audio_latent) và trả
    về 3 output (positive, negative, frozen_audio) — code này dùng output[0]
    và output[1], khớp đúng.

    Trả về (positive_ref_mới, negative_ref_mới, next_free_id). Nếu
    audio_latent_ref là None thì trả nguyên positive_ref/negative_ref.
    """
    if audio_latent_ref is None:
        return positive_ref, negative_ref, start_id
    if "LTXVSetAudioRefTokens" not in _get_comfy_nodes():
        print("⚠️ [Voice Lock] Node 'LTXVSetAudioRefTokens' không có trong ComfyUI "
              "→ bỏ qua Voice Lock. Hãy bấm '🔄 Restart' rồi thử lại, "
              "hoặc cập nhật ComfyUI-LTXVideo (cd /content/ComfyUI/custom_nodes/ComfyUI-LTXVideo && git pull).")
        return positive_ref, negative_ref, start_id
    node_id = str(start_id)
    wf[node_id] = {"class_type": "LTXVSetAudioRefTokens",
                    "inputs": {"positive": positive_ref, "negative": negative_ref, "audio_latent": audio_latent_ref}}
    return [node_id, 0], [node_id, 1], start_id + 1


def _is_ic_lora_file(filename):
    """Kiểm tra (dựa trên tên file) liệu đây có phải IC-LoRA Ingredients của
    Lightricks không. LoRA thường đặt vào IC-LoRA dropdown sẽ bị bỏ qua thay
    vì gây lỗi 'LTXICLoRALoaderModelOnly not found'."""
    name = (filename or "").lower()
    return "ic-lora" in name or "ic_lora" in name or "ingredients" in name


def apply_ic_lora_ingredients(wf, model_source, positive_ref, negative_ref, latent_ref, vae_ref,
                               ic_lora_name, ic_lora_strength, ref_image_name, guide_strength, start_id=150):
    """Nạp đúng cơ chế IC-LoRA "Ingredients" chính thức của Lightricks để giữ
    nhân vật/bối cảnh bám theo 1 ảnh tham khảo (reference sheet) xuyên suốt
    video — dùng đúng 2 node chính thức trong iclora.py của ComfyUI-LTXVideo:
    LTXICLoRALoaderModelOnly + LTXAddVideoICLoRAGuide.

    Đã đối chiếu trực tiếp với mã nguồn mới nhất (master, 8/2026) của
    https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/iclora.py:
      - LTXICLoRALoaderModelOnly.outputs = (model, latent_downscale_factor)
        -> latent_downscale_factor PHẢI lấy từ output[1] (đọc từ metadata
        "reference_downscale_factor" trong file .safetensors), không hardcode.
      - LTXAddVideoICLoRAGuide.inputs = (positive, negative, vae, latent,
        image, frame_idx, strength, latent_downscale_factor, crop,
        use_tiled_encode, tile_size, tile_overlap) — tên và thứ tự khớp 100%
        với dict "inputs" bên dưới.
      - "latent" đưa vào LTXAddVideoICLoRAGuide BẮT BUỘC phải là latent VIDEO
        THUẦN (5D, chưa ghép audio) — mọi nơi gọi hàm này trong file đều
        truyền latent_ref TRƯỚC bước LTXVConcatAVLatent, nên đã đúng.

    QUAN TRỌNG (lý do hàm này tồn tại thay vì dùng LoraLoaderModelOnly như
    LoRA thường): nạp LoRA Ingredients bằng LoraLoaderModelOnly thông thường
    chỉ đổi TRỌNG SỐ model, nhưng ảnh tham khảo không hề được "đăng ký" vào
    cơ chế attention đặc biệt mà IC-LoRA được train để đọc — HuggingFace của
    chính LoRA này ghi rõ: "a generic LoRA loader that ignores the reference
    path will not apply the conditioning". LTXAddVideoICLoRAGuide mới là node
    thật sự mã hoá ảnh tham khảo (bằng VAE) rồi tiêm vào latent + gắn "guide
    attention entry" vào positive/negative — đúng cơ chế mà IC-LoRA cần để
    "nhìn thấy" ảnh tham khảo trong suốt quá trình sinh video.

    Chỉ áp dụng an toàn cho PASS 1 (đúng theo workflow chính thức
    "Single_Stage" của Lightricks — Ingredients IC-LoRA hiện KHÔNG có bản
    two-stage chính thức). Pass 2 (nếu có) chỉ upscale/refine kết quả pass 1
    — đã mang sẵn ảnh hưởng của reference — nên KHÔNG tiêm lại latent guide ở
    pass 2 để tránh lệch shape giữa 2 độ phân giải khác nhau.

    Trả về (model_ref, positive_ref_mới, negative_ref_mới, latent_ref_mới).
    Nếu thiếu ic_lora_name hoặc thiếu ref_image_name thì trả nguyên các ref
    đầu vào — không đổi hành vi/workflow gốc.
    """
    if not ic_lora_name or ic_lora_name == NO_LORA_LABEL or not ref_image_name or not _is_ic_lora_file(ic_lora_name):
        return model_source, positive_ref, negative_ref, latent_ref

    node_loader = str(start_id)
    node_load_img = str(start_id + 1)
    node_guide = str(start_id + 2)

    wf[node_loader] = {
        "class_type": "LTXICLoRALoaderModelOnly",
        "inputs": {"model": model_source, "lora_name": ic_lora_name, "strength_model": float(ic_lora_strength)},
    }
    wf[node_load_img] = {"class_type": "LoadImage", "inputs": {"image": ref_image_name}}
    wf[node_guide] = {
        "class_type": "LTXAddVideoICLoRAGuide",
        "inputs": {
            "positive": positive_ref, "negative": negative_ref, "vae": vae_ref, "latent": latent_ref,
            "image": [node_load_img, 0], "frame_idx": 0, "strength": float(guide_strength),
            # latent_downscale_factor PHẢI lấy từ output thứ 2 của LTXICLoRALoaderModelOnly
            # (đọc từ metadata của chính file LoRA) — không tự đặt cứng 1.0, đúng như
            # workflow JSON chính thức của Lightricks nối 2 node này.
            "latent_downscale_factor": [node_loader, 1],
            "crop": "disabled", "use_tiled_encode": False, "tile_size": 256, "tile_overlap": 64,
        },
    }
    return [node_loader, 0], [node_guide, 0], [node_guide, 1], [node_guide, 2]


# ==========================================================================
# 3 WORKFLOW LTX-2.5
# ==========================================================================
def _clip_text_nodes(prompt_text, negative_text):
    return {
        "1": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": prompt_text}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": negative_text}},
    }


def build_t2v_workflow(*, prompt_text, negative_text=NEGATIVE_PROMPT_DEFAULT, width, height, fps, duration, seed,
                        lora1_name=NO_LORA_LABEL, lora1_strength=1.0,
                        lora2_name=NO_LORA_LABEL, lora2_strength=0.6,
                        ic_lora_name=NO_LORA_LABEL, ic_lora_strength=1.0,
                        ic_ref_image_name=None, ic_guide_strength=1.0,
                        voice_ref_audio_name=None):
    safe_fps = snap_fps_safe(fps)
    total_frames = total_frames_for(duration, safe_fps)
    half_w, half_h = half_dims(width, height)

    wf = _clip_text_nodes(prompt_text, negative_text)
    wf.update({
        "4": {"class_type": "LTXVConditioning",
              "inputs": {"positive": ["2", 0], "negative": ["3", 0], "frame_rate": float(safe_fps)}},
        "5": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "7": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "8": {"class_type": "EmptyLTXVLatentVideo",
              "inputs": {"width": half_w, "height": half_h, "length": total_frames, "batch_size": 1}},
        "9": {"class_type": "LTXVEmptyLatentAudio",
              "inputs": {"audio_vae": ["7", 0], "frames_number": total_frames, "frame_rate": float(safe_fps), "batch_size": 1}},
        "10": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["8", 0], "audio_latent": ["9", 0]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "13": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "14": {"class_type": "LTXVDualCFGGuider",
               "inputs": {"model": ["5", 0], "positive": ["4", 0], "negative": ["4", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "15": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["11", 0], "guider": ["14", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["10", 0]}},
        "16": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["15", 0]}},
        "17": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "18": {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["16", 0], "upscale_model": ["17", 0], "vae": ["6", 0]}},
        "19": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["18", 0], "audio_latent": ["9", 0]}},
        "20": {"class_type": "RandomNoise", "inputs": {"noise_seed": PASS2_FIXED_NOISE_SEED}},
        "21": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "22": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS2}},
        "23": {"class_type": "LTXVDualCFGGuider",
               "inputs": {"model": ["5", 0], "positive": ["4", 0], "negative": ["4", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "24": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["20", 0], "guider": ["23", 0], "sampler": ["21", 0], "sigmas": ["22", 0], "latent_image": ["19", 0]}},
        "25": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["24", 0]}},
        "26": {"class_type": "VAEDecodeTiled",
               "inputs": {"samples": ["25", 0], "vae": ["6", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "27": {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["25", 1], "audio_vae": ["7", 0]}},
        "28": {"class_type": "CreateVideo", "inputs": {"images": ["26", 0], "audio": ["27", 0], "fps": float(safe_fps)}},
        "29": {"class_type": "SaveVideo",
               "inputs": {"video": ["28", 0], "filename_prefix": "video/ltx25_t2v", "format": "auto", "codec": "auto"}},
    })

    # --- Chèn LoRA thường (giữ nhân vật kiểu "thẳng" / phong cách) ---
    model_ref = apply_lora_stack(wf, ["5", 0], lora1_name, lora1_strength, lora2_name, lora2_strength)

    # --- IC-LoRA Ingredients: neo nhân vật/bối cảnh bằng ảnh tham khảo qua
    # đúng cơ chế attention chuyên dụng — chỉ áp dụng cho PASS 1.
    model_ref, p1_pos, p1_neg, p1_video_latent = apply_ic_lora_ingredients(
        wf, model_ref, ["4", 0], ["4", 1], ["8", 0], ["6", 0],
        ic_lora_name, ic_lora_strength, ic_ref_image_name, ic_guide_strength)

    # --- [THỬ NGHIỆM] Khoá giọng nói — áp dụng cho CẢ 2 pass (audio được
    # sample lại từ đầu ở mỗi pass nên cần khoá lại mỗi pass).
    audio_ref, next_id = encode_voice_reference(wf, ["7", 0], voice_ref_audio_name, start_id=200)
    p1_pos, p1_neg, next_id = set_audio_ref_tokens(wf, p1_pos, p1_neg, audio_ref, start_id=next_id)
    p2_pos, p2_neg, next_id = set_audio_ref_tokens(wf, ["4", 0], ["4", 1], audio_ref, start_id=next_id)

    wf["10"]["inputs"]["video_latent"] = p1_video_latent
    wf["14"]["inputs"]["model"] = model_ref
    wf["14"]["inputs"]["positive"] = p1_pos
    wf["14"]["inputs"]["negative"] = p1_neg
    wf["23"]["inputs"]["model"] = model_ref
    wf["23"]["inputs"]["positive"] = p2_pos
    wf["23"]["inputs"]["negative"] = p2_neg
    return wf


def build_i2v_workflow(*, image_name, prompt_text, negative_text=NEGATIVE_PROMPT_DEFAULT, width, height, fps, duration, seed,
                        image_strength=0.7,
                        lora1_name=NO_LORA_LABEL, lora1_strength=1.0,
                        lora2_name=NO_LORA_LABEL, lora2_strength=0.6,
                        ic_lora_name=NO_LORA_LABEL, ic_lora_strength=1.0,
                        ic_ref_image_name=None, ic_guide_strength=1.0,
                        voice_ref_audio_name=None):
    safe_fps = snap_fps_safe(fps)
    total_frames = total_frames_for(duration, safe_fps)
    half_w, half_h = half_dims(width, height)

    wf = _clip_text_nodes(prompt_text, negative_text)
    wf.update({
        "4": {"class_type": "LTXVConditioning",
              "inputs": {"positive": ["2", 0], "negative": ["3", 0], "frame_rate": float(safe_fps)}},
        "5": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "7": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "30": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "31": {"class_type": "ImageResizeKJv2",
               "inputs": {"width": width, "height": height, "upscale_method": "lanczos", "keep_proportion": "crop",
                          "pad_color": "0, 0, 0", "crop_position": "center", "divisible_by": 32, "device": "cpu",
                          "image": ["30", 0]}},
        "32": {"class_type": "LTXVPreprocess", "inputs": {"img_compression": 18, "image": ["31", 0]}},
        "8": {"class_type": "EmptyLTXVLatentVideo",
              "inputs": {"width": half_w, "height": half_h, "length": total_frames, "batch_size": 1}},
        "33": {"class_type": "LTXVImgToVideoInplace",
               "inputs": {"vae": ["6", 0], "image": ["32", 0], "latent": ["8", 0], "strength": float(image_strength), "bypass": False}},
        "9": {"class_type": "LTXVEmptyLatentAudio",
              "inputs": {"audio_vae": ["7", 0], "frames_number": total_frames, "frame_rate": float(safe_fps), "batch_size": 1}},
        "10": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["33", 0], "audio_latent": ["9", 0]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "13": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "14": {"class_type": "LTXVDualCFGGuider",
               "inputs": {"model": ["5", 0], "positive": ["4", 0], "negative": ["4", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "15": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["11", 0], "guider": ["14", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["10", 0]}},
        "16": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["15", 0]}},
        "17": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "18": {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["16", 0], "upscale_model": ["17", 0], "vae": ["6", 0]}},
        "34": {"class_type": "LTXVImgToVideoInplace",
               "inputs": {"vae": ["6", 0], "image": ["32", 0], "latent": ["18", 0], "strength": 1.0, "bypass": False}},
        "19": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["34", 0], "audio_latent": ["9", 0]}},
        "20": {"class_type": "RandomNoise", "inputs": {"noise_seed": PASS2_FIXED_NOISE_SEED}},
        "21": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "22": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS2}},
        "23": {"class_type": "LTXVDualCFGGuider",
               "inputs": {"model": ["5", 0], "positive": ["4", 0], "negative": ["4", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "24": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["20", 0], "guider": ["23", 0], "sampler": ["21", 0], "sigmas": ["22", 0], "latent_image": ["19", 0]}},
        "25": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["24", 0]}},
        "26": {"class_type": "VAEDecodeTiled",
               "inputs": {"samples": ["25", 0], "vae": ["6", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "27": {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["25", 1], "audio_vae": ["7", 0]}},
        "28": {"class_type": "CreateVideo", "inputs": {"images": ["26", 0], "audio": ["27", 0], "fps": float(safe_fps)}},
        "29": {"class_type": "SaveVideo",
               "inputs": {"video": ["28", 0], "filename_prefix": "video/ltx25_i2v", "format": "auto", "codec": "auto"}},
    })

    # --- Chèn LoRA thường (giữ nhân vật kiểu "thẳng" / phong cách) ---
    model_ref = apply_lora_stack(wf, ["5", 0], lora1_name, lora1_strength, lora2_name, lora2_strength)

    # --- IC-LoRA Ingredients: neo nhân vật/bối cảnh bằng ảnh tham khảo qua
    # đúng cơ chế attention chuyên dụng. Áp dụng SAU khi ảnh gốc/khung nối
    # tiếp của scene đã được tiêm vào latent (node 33) — đúng thứ tự trong
    # workflow chính thức của Lightricks (ImgToVideo trước, IC-LoRA Guide
    # sau). Chỉ áp dụng cho PASS 1.
    model_ref, p1_pos, p1_neg, p1_video_latent = apply_ic_lora_ingredients(
        wf, model_ref, ["4", 0], ["4", 1], ["33", 0], ["6", 0],
        ic_lora_name, ic_lora_strength, ic_ref_image_name, ic_guide_strength)

    # --- [THỬ NGHIỆM] Khoá giọng nói — áp dụng cho CẢ 2 pass (audio được
    # sample lại từ đầu ở mỗi pass nên cần khoá lại mỗi pass).
    audio_ref, next_id = encode_voice_reference(wf, ["7", 0], voice_ref_audio_name, start_id=200)
    p1_pos, p1_neg, next_id = set_audio_ref_tokens(wf, p1_pos, p1_neg, audio_ref, start_id=next_id)
    p2_pos, p2_neg, next_id = set_audio_ref_tokens(wf, ["4", 0], ["4", 1], audio_ref, start_id=next_id)

    wf["10"]["inputs"]["video_latent"] = p1_video_latent
    wf["14"]["inputs"]["model"] = model_ref
    wf["14"]["inputs"]["positive"] = p1_pos
    wf["14"]["inputs"]["negative"] = p1_neg
    wf["23"]["inputs"]["model"] = model_ref
    wf["23"]["inputs"]["positive"] = p2_pos
    wf["23"]["inputs"]["negative"] = p2_neg
    return wf


def build_flf2v_workflow(*, first_image_name, last_image_name, prompt_text, negative_text=NEGATIVE_PROMPT_DEFAULT,
                          width, height, fps, duration, seed, first_strength=0.7, last_strength=0.7,
                          lora1_name=NO_LORA_LABEL, lora1_strength=1.0,
                          lora2_name=NO_LORA_LABEL, lora2_strength=0.6,
                          ic_lora_name=NO_LORA_LABEL, ic_lora_strength=1.0,
                          ic_ref_image_name=None, ic_guide_strength=1.0,
                          voice_ref_audio_name=None):
    safe_fps = snap_fps_safe(fps)
    total_frames = total_frames_for(duration, safe_fps)

    wf = _clip_text_nodes(prompt_text, negative_text)
    wf.update({
        "4": {"class_type": "LTXVConditioning",
              "inputs": {"positive": ["2", 0], "negative": ["3", 0], "frame_rate": float(safe_fps)}},
        "5": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "7": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "8": {"class_type": "EmptyLTXVLatentVideo",
              "inputs": {"width": width, "height": height, "length": total_frames, "batch_size": 1}},
        "9": {"class_type": "LoadImage", "inputs": {"image": first_image_name}},
        "10": {"class_type": "ImageResizeKJv2",
               "inputs": {"width": width, "height": height, "upscale_method": "lanczos", "keep_proportion": "crop",
                          "pad_color": "0, 0, 0", "crop_position": "center", "divisible_by": 32, "device": "cpu",
                          "image": ["9", 0]}},
        "11": {"class_type": "LTXVPreprocess", "inputs": {"img_compression": 18, "image": ["10", 0]}},
        "12": {"class_type": "LoadImage", "inputs": {"image": last_image_name}},
        "13": {"class_type": "ImageResizeKJv2",
               "inputs": {"width": width, "height": height, "upscale_method": "lanczos", "keep_proportion": "crop",
                          "pad_color": "0, 0, 0", "crop_position": "center", "divisible_by": 32, "device": "cpu",
                          "image": ["12", 0]}},
        "14": {"class_type": "LTXVPreprocess", "inputs": {"img_compression": 18, "image": ["13", 0]}},
        "15": {"class_type": "LTXVAddGuide",
               "inputs": {"positive": ["4", 0], "negative": ["4", 1], "vae": ["6", 0], "latent": ["8", 0],
                          "image": ["11", 0], "frame_idx": 0, "strength": float(first_strength)}},
        "16": {"class_type": "LTXVAddGuide",
               "inputs": {"positive": ["15", 0], "negative": ["15", 1], "vae": ["6", 0], "latent": ["15", 2],
                          "image": ["14", 0], "frame_idx": -1, "strength": float(last_strength)}},
        "17": {"class_type": "LTXVEmptyLatentAudio",
               "inputs": {"audio_vae": ["7", 0], "frames_number": total_frames, "frame_rate": float(safe_fps), "batch_size": 1}},
        "18": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["16", 2], "audio_latent": ["17", 0]}},
        "19": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "20": {"class_type": "SamplerEulerAncestral", "inputs": {"eta": 0.0, "s_noise": 1.0}},
        "21": {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "22": {"class_type": "LTXVDualCFGGuider",
               "inputs": {"model": ["5", 0], "positive": ["16", 0], "negative": ["16", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "23": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["19", 0], "guider": ["22", 0], "sampler": ["20", 0], "sigmas": ["21", 0], "latent_image": ["18", 0]}},
        "24": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["23", 0]}},
        "25": {"class_type": "LTXVCropGuides",
               "inputs": {"positive": ["16", 0], "negative": ["16", 1], "latent": ["24", 0]}},
        "26": {"class_type": "VAEDecodeTiled",
               "inputs": {"samples": ["25", 2], "vae": ["6", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "27": {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["24", 1], "audio_vae": ["7", 0]}},
        "28": {"class_type": "CreateVideo", "inputs": {"images": ["26", 0], "audio": ["27", 0], "fps": float(safe_fps)}},
        "29": {"class_type": "SaveVideo",
               "inputs": {"video": ["28", 0], "filename_prefix": "video/ltx25_flf2v", "format": "auto", "codec": "auto"}},
    })

    # --- Chèn LoRA thường (giữ nhân vật kiểu "thẳng" / phong cách) ---
    model_ref = apply_lora_stack(wf, ["5", 0], lora1_name, lora1_strength, lora2_name, lora2_strength)

    # --- IC-LoRA Ingredients: chèn TRƯỚC chuỗi guide Đầu/Cuối sẵn có (node
    # 15/16) — cùng kiểu chuỗi guide nối tiếp mà FLF2V đã dùng sẵn.
    model_ref, p0_pos, p0_neg, p0_latent = apply_ic_lora_ingredients(
        wf, model_ref, ["4", 0], ["4", 1], ["8", 0], ["6", 0],
        ic_lora_name, ic_lora_strength, ic_ref_image_name, ic_guide_strength)
    wf["15"]["inputs"]["positive"] = p0_pos
    wf["15"]["inputs"]["negative"] = p0_neg
    wf["15"]["inputs"]["latent"] = p0_latent

    # --- [THỬ NGHIỆM] Khoá giọng nói (FLF2V chỉ có 1 pass) ---
    audio_ref, next_id = encode_voice_reference(wf, ["7", 0], voice_ref_audio_name, start_id=200)
    final_pos, final_neg, next_id = set_audio_ref_tokens(wf, ["16", 0], ["16", 1], audio_ref, start_id=next_id)

    wf["22"]["inputs"]["model"] = model_ref
    wf["22"]["inputs"]["positive"] = final_pos
    wf["22"]["inputs"]["negative"] = final_neg
    return wf


def submit_and_wait(workflow, scene_label="", max_wait_seconds=1800, poll_interval=2):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        response = urllib.request.urlopen(req, timeout=30)
        prompt_id = json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = str(e)
        raise RuntimeError(f"ComfyUI từ chối workflow ở {scene_label}:\n{error_body[:800]}")
    except Exception as e:
        raise RuntimeError(f"Lỗi gửi job API ở {scene_label}: {e}")

    waited = 0
    while waited < max_wait_seconds:
        try:
            history = json.loads(urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}"), timeout=30).read())
            if str(prompt_id) in history:
                return prompt_id
            queue = json.loads(urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8188/queue"), timeout=30).read())
            is_running = any(
                str(job[1]) == str(prompt_id)
                for job in queue.get("queue_running", []) + queue.get("queue_pending", [])
            )
            if not is_running:
                raise RuntimeError(f"Render thất bại ở {scene_label} (nghi ngờ tràn VRAM)")
        except RuntimeError:
            raise
        except Exception:
            raise RuntimeError(f"Server bị crash giữa chừng ở {scene_label}!")
        time.sleep(poll_interval)
        waited += poll_interval
    raise RuntimeError(f"Timeout: {scene_label} chạy quá {max_wait_seconds // 60} phút, đã hủy chờ.")


def find_latest_video(output_dir=OUTPUT_DIR):
    mp4_files = glob.glob(f"{output_dir}*.mp4") + glob.glob(f"{output_dir}video/*.mp4")
    if not mp4_files:
        return None
    return max(mp4_files, key=os.path.getmtime)


def has_audio_stream(video_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a",
           "-show_entries", "stream=index", "-of", "csv=p=0", video_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return bool(result.stdout.strip())
    except Exception:
        return True


def ensure_audio_track(video_path):
    if has_audio_stream(video_path):
        return video_path
    fixed_path = video_path.rsplit(".", 1)[0] + "_silentaudio.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest", "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        fixed_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(fixed_path):
        return fixed_path
    return video_path


def concat_videos(video_list, out_name, output_dir=OUTPUT_DIR):
    safe_video_list = [ensure_audio_track(v) for v in video_list]
    concat_file_path = os.path.join(output_dir, f"concat_{out_name}.txt")
    with open(concat_file_path, "w") as f:
        for vid in safe_video_list:
            f.write(f"file '{os.path.abspath(vid)}'\n")
    final_output = os.path.join(output_dir, f"{out_name}_{int(time.time())}.mp4")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file_path,
           "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", final_output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(final_output):
        raise RuntimeError("Ghép nối video bằng ffmpeg thất bại. Các file phân đoạn lẻ vẫn còn trong thư mục output.")
    return final_output


def _wants_char_ref(i, char_mode, char_ref_path, periodic_n):
    """Quyết định phân cảnh thứ i (0-based) có nên bám ảnh tham khảo nhân vật
    cố định hay không, dựa trên chế độ đã chọn."""
    if not char_ref_path:
        return False
    if char_mode == CHAR_MODE_STRICT:
        return True
    if char_mode == CHAR_MODE_PERIODIC:
        n = int(periodic_n) if periodic_n else 0
        return n > 0 and (i % n == 0)
    return False


# ==========================================================================
# TAB 1 — Video dài từ 1 ảnh + 1 prompt (I2V)
# ==========================================================================
def generate_long_video_gradio(img_path, pos_prompt, aspect_ratio, v_length, v_fps, v_seed, num_segments,
                                low_vram, frame_percent, fixed_seed, image_strength,
                                lora1_name, lora1_strength, lora2_name, lora2_strength,
                                voice_ref_audio, auto_voice_lock):
    if not img_path:
        yield None, "⚠️ Dạ anh vui lòng tải ảnh lên trước giúp em nha!"
        return
    if not pos_prompt or not pos_prompt.strip():
        yield None, "⚠️ Dạ anh nhập giúp em câu lệnh (prompt) nha!"
        return

    num_segments = int(num_segments)
    frame_percent = int(frame_percent)
    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

    yield None, "🔄 Đang kiểm tra / khởi động server (chỉ load lại nếu cần)..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, f"❌ {e}"
        return

    base_seed = get_seed(v_seed)
    yield None, f"✅ Server sẵn sàng. Bắt đầu tạo {num_segments} phân đoạn... (Base Seed: {base_seed})"
    os.makedirs(INPUT_DIR, exist_ok=True)

    voice_ref_name = None
    if voice_ref_audio:
        voice_ref_name = f"voice_ref_manual_{int(time.time())}.wav"
        shutil.copy(voice_ref_audio, os.path.join(INPUT_DIR, voice_ref_name))

    current_img_path = img_path
    generated_videos = []
    for i in range(num_segments):
        label = f"phân đoạn {i + 1}/{num_segments}"
        seed_i = base_seed if fixed_seed else (base_seed + i)
        voice_note = " 🎤 khoá giọng" if voice_ref_name else ""
        yield None, f"🔄 Đang tạo {label}{voice_note}... (Seed: {seed_i})"
        img_name = f"segment_{i}_{int(time.time())}.png"
        shutil.copy(current_img_path, os.path.join(INPUT_DIR, img_name))
        wf = build_i2v_workflow(image_name=img_name, prompt_text=pos_prompt, width=safe_width, height=safe_height,
                                 fps=v_fps, duration=v_length, seed=seed_i, image_strength=image_strength,
                                 lora1_name=lora1_name, lora1_strength=lora1_strength,
                                 lora2_name=lora2_name, lora2_strength=lora2_strength,
                                 voice_ref_audio_name=voice_ref_name)
        try:
            submit_and_wait(wf, scene_label=label)
        except Exception as e:
            yield None, f"❌ {e}"
            return
        latest_video = find_latest_video()
        if not latest_video:
            yield None, f"⚠️ Không tìm thấy file video đầu ra ở {label}!"
            return
        generated_videos.append(latest_video)
        if voice_ref_name is None and auto_voice_lock and i == 0:
            auto_ref_path = os.path.join(INPUT_DIR, f"voice_ref_auto_{int(time.time())}.wav")
            if extract_audio_track(latest_video, auto_ref_path):
                voice_ref_name = os.path.basename(auto_ref_path)
        if i < num_segments - 1:
            next_img_path = os.path.join(INPUT_DIR, f"extracted_frame_{i}_{int(time.time())}.png")
            extract_frame_at_percent(latest_video, next_img_path, frame_percent)
            current_img_path = next_img_path
            yield latest_video, f"🔔 [DING] ✅ Xong {label}. Đã lấy khung hình tại {frame_percent}% clip làm chuẩn cho đoạn sau..."

    if len(generated_videos) > 1:
        yield None, "🔄 Đang ghép nối các phân đoạn..."
        try:
            final_output = concat_videos(generated_videos, "final_long_video")
        except Exception as e:
            yield generated_videos[-1], f"⚠️ {e}"
            return
        total_seconds = num_segments * v_length
        yield final_output, f"🔔 [DING] 🎉 Hoàn tất toàn bộ video ({total_seconds}s)! Base Seed: {base_seed}"
    else:
        yield generated_videos[0], f"🔔 [DING] 🎉 Render Complete! (Seed: {base_seed})"


# ==========================================================================
# TAB 2 — Chuỗi kịch bản nối tiếp (I2V)
# ==========================================================================
def generate_sequence_i2v_gradio(img_path, prompts_text, aspect_ratio, v_length, v_fps, v_seed,
                                  low_vram, frame_percent, image_strength,
                                  lora1_name, lora1_strength, lora2_name, lora2_strength,
                                  char_ref_path, char_mode, periodic_n,
                                  ic_lora_name, ic_lora_strength, ic_guide_strength,
                                  voice_ref_audio, auto_voice_lock):
    if not img_path:
        yield None, None, "⚠️ Dạ anh vui lòng tải ảnh lên trước giúp em nha!"
        return
    prompts = split_prompts(prompts_text)
    if not prompts:
        yield None, None, "⚠️ Dạ anh nhập giúp em ít nhất 1 dòng kịch bản (prompt) nha!"
        return
    if char_mode != CHAR_MODE_SMOOTH and not char_ref_path:
        yield None, None, ("⚠️ Bạn đã chọn chế độ bám nhân vật nhưng chưa tải 'Ảnh tham khảo nhân vật' — "
                            "em sẽ tự chuyển về chế độ 'Nối cảnh mượt' cho lần chạy này nha!")
        char_mode = CHAR_MODE_SMOOTH

    frame_percent = int(frame_percent)
    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)
    total_videos = len(prompts)

    yield None, None, f"🔄 Đang kiểm tra / khởi động server để quay {total_videos} phân cảnh..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, None, f"❌ {e}"
        return

    base_seed = get_seed(v_seed)
    yield None, None, f"✅ Server đã sẵn sàng. Bắt đầu quay... (Base Seed: {base_seed})"
    os.makedirs(INPUT_DIR, exist_ok=True)

    voice_ref_name = None
    if voice_ref_audio:
        voice_ref_name = f"voice_ref_manual_{int(time.time())}.wav"
        shutil.copy(voice_ref_audio, os.path.join(INPUT_DIR, voice_ref_name))

    ic_ref_img_name = None
    if char_ref_path:
        ic_ref_img_name = f"ic_ref_{int(time.time())}.png"
        shutil.copy(char_ref_path, os.path.join(INPUT_DIR, ic_ref_img_name))

    generated_videos = []
    current_img_path = img_path
    for i, p in enumerate(prompts):
        label = f"phân cảnh {i + 1}/{total_videos}"

        if _wants_char_ref(i, char_mode, char_ref_path, periodic_n):
            seed_img_for_scene = char_ref_path
            src_note = "🎯 ảnh tham khảo nhân vật (cố định)"
        else:
            seed_img_for_scene = current_img_path
            src_note = "🔗 nối tiếp từ cảnh trước" if i > 0 else "ảnh gốc upload"
        if voice_ref_name:
            src_note += " + 🎤 khoá giọng"
        if ic_ref_img_name and ic_lora_name and ic_lora_name != NO_LORA_LABEL:
            src_note += " + 🧬 IC-LoRA guide"

        yield generated_videos, None, f"🔄 Đang quay {label} [{src_note}]... (Seed: {base_seed})\n📝 Nội dung: {p}"
        img_name = f"seq_frame_{i}_{int(time.time())}.png"
        shutil.copy(seed_img_for_scene, os.path.join(INPUT_DIR, img_name))
        wf = build_i2v_workflow(image_name=img_name, prompt_text=p, width=safe_width, height=safe_height,
                                 fps=v_fps, duration=v_length, seed=base_seed, image_strength=image_strength,
                                 lora1_name=lora1_name, lora1_strength=lora1_strength,
                                 lora2_name=lora2_name, lora2_strength=lora2_strength,
                                 ic_lora_name=ic_lora_name, ic_lora_strength=ic_lora_strength,
                                 ic_ref_image_name=ic_ref_img_name, ic_guide_strength=ic_guide_strength,
                                 voice_ref_audio_name=voice_ref_name)
        try:
            submit_and_wait(wf, scene_label=label)
        except Exception as e:
            yield generated_videos, None, f"❌ {e}"
            return
        latest_video = find_latest_video()
        if not latest_video:
            yield generated_videos, None, f"⚠️ Không tìm thấy file video {i + 1}!"
            return
        generated_videos.append(latest_video)
        if voice_ref_name is None and auto_voice_lock and i == 0:
            auto_ref_path = os.path.join(INPUT_DIR, f"voice_ref_auto_{int(time.time())}.wav")
            if extract_audio_track(latest_video, auto_ref_path):
                voice_ref_name = os.path.basename(auto_ref_path)
        if i < total_videos - 1:
            # Vẫn luôn trích khung hình nối tiếp (kể cả khi cảnh này dùng ảnh
            # tham khảo) để chế độ "Nối cảnh mượt"/"Kết hợp" có sẵn khung cho
            # các cảnh tiếp theo không rơi vào lượt bám ảnh tham khảo.
            next_img_path = os.path.join(INPUT_DIR, f"extracted_frame_seq_{i}_{int(time.time())}.png")
            extract_frame_at_percent(latest_video, next_img_path, frame_percent)
            current_img_path = next_img_path
            yield generated_videos, None, f"🔔 [DING] ✅ Xong {label}. Đã chuẩn bị khung nối tiếp cho cảnh {i + 2}..."
        else:
            yield generated_videos, None, f"🔔 [DING] ✅ Đã quay xong toàn bộ {total_videos} phân cảnh!"

    if len(generated_videos) > 1:
        yield generated_videos, None, "🔄 Đang tiến hành ghép nối các phân cảnh..."
        try:
            final_output = concat_videos(generated_videos, "final_seq_video")
        except Exception as e:
            yield generated_videos, None, f"⚠️ {e}"
            return
        yield generated_videos, final_output, f"🔔 [DING] 🎉 Đã gộp xong phim! Base Seed: {base_seed}"
    else:
        yield generated_videos, generated_videos[0], f"🔔 [DING] 🎉 Render Complete! (Seed: {base_seed})"


# ==========================================================================
# TAB 3 — Storyboard (T2V / I2V / FLF2V tự động)
# ==========================================================================
def resolve_scene_first_image(i, current_first_path, current_last_path, latest_video,
                               char_ref_path, char_mode, periodic_n, frame_percent):
    """Quyết định ảnh 'Đầu' thực tế dùng cho phân cảnh i. Thứ tự ưu tiên:
    1) Ảnh người dùng tự upload riêng cho đúng cảnh đó — LUÔN được tôn trọng,
       không bao giờ bị ghi đè bởi chế độ bám nhân vật.
    2) Nếu KHÔNG có ảnh upload riêng và chế độ bám nhân vật đang bật cho cảnh
       này (Bám 100%, hoặc Kết hợp đúng chu kỳ N) -> dùng ảnh tham khảo nhân
       vật cố định làm ảnh Đầu, đảm bảo nhân vật không trôi/lệch qua từng
       cảnh 10s.
    3) Ngược lại giữ đúng hành vi gốc: trích khung hình cuối của cảnh trước.
    Trả về (first_path, last_path, ghi_chú_nguồn_ảnh).
    """
    want_ref = _wants_char_ref(i, char_mode, char_ref_path, periodic_n)

    if current_first_path is None and current_last_path is not None:
        if want_ref:
            return char_ref_path, current_last_path, "ảnh tham khảo nhân vật (cố định) + ảnh Cuối upload"
        if latest_video is not None:
            tmp_path = os.path.join(INPUT_DIR, f"auto_first_for_flf_{i}_{int(time.time())}.png")
            extract_frame_at_percent(latest_video, tmp_path, frame_percent)
            return tmp_path, current_last_path, f"trích từ video cảnh trước ({frame_percent}%) + ảnh Cuối upload"
        return None, None, None

    if current_first_path is None and current_last_path is None:
        if want_ref:
            return char_ref_path, None, "ảnh tham khảo nhân vật (cố định)"
        if latest_video is not None:
            next_img_path = os.path.join(INPUT_DIR, f"extracted_first_flfsb_{i}_{int(time.time())}.png")
            extract_frame_at_percent(latest_video, next_img_path, frame_percent)
            return next_img_path, None, f"trích từ video cảnh trước ({frame_percent}%)"
        return None, None, None

    return current_first_path, current_last_path, "ảnh upload"


def generate_storyboard_flf_gradio(*args):
    n = MAX_FLF_SB_SCENES
    first_img_inputs = args[:n]
    last_img_inputs = args[n:2 * n]
    (
        prompts_text, aspect_ratio, v_length, v_fps, v_seed,
        low_vram, frame_percent, first_strength, last_strength, image_strength,
        lora1_name, lora1_strength, lora2_name, lora2_strength,
        char_ref_path, char_mode, periodic_n,
        ic_lora_name, ic_lora_strength, ic_guide_strength,
        voice_ref_audio, auto_voice_lock,
    ) = args[2 * n:]

    frame_percent = int(frame_percent)
    v_length = int(v_length)
    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)
    prompts = split_prompts(prompts_text)

    if not prompts:
        yield None, None, "⚠️ Dạ anh nhập giúp em ít nhất 1 dòng kịch bản (prompt) nha!"
        return
    if char_mode != CHAR_MODE_SMOOTH and not char_ref_path:
        yield None, None, ("⚠️ Bạn đã chọn chế độ bám nhân vật nhưng chưa tải 'Ảnh tham khảo nhân vật' — "
                            "em sẽ tự chuyển về chế độ 'Nối cảnh mượt' cho lần chạy này nha!")
        char_mode = CHAR_MODE_SMOOTH

    total_videos = len(prompts)
    yield None, None, f"🔄 Đang kiểm tra / khởi động server để quay {total_videos} phân cảnh (Storyboard LTX-2.5)..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, None, f"❌ {e}"
        return

    base_seed = get_seed(v_seed)
    yield None, None, f"✅ Server đã sẵn sàng. Bắt đầu quay... (Base Seed: {base_seed})"
    os.makedirs(INPUT_DIR, exist_ok=True)

    voice_ref_name = None
    if voice_ref_audio:
        voice_ref_name = f"voice_ref_manual_{int(time.time())}.wav"
        shutil.copy(voice_ref_audio, os.path.join(INPUT_DIR, voice_ref_name))

    # Chuẩn bị sẵn ảnh tham khảo nhân vật cho cơ chế IC-LoRA Ingredients
    # (LTXAddVideoICLoRAGuide) — ĐỘC LẬP với việc ảnh này có được dùng làm
    # ảnh Đầu hay không (xem resolve_scene_first_image). Chỉ copy 1 lần.
    ic_ref_img_name = None
    if char_ref_path:
        ic_ref_img_name = f"ic_ref_flfsb_{int(time.time())}.png"
        shutil.copy(char_ref_path, os.path.join(INPUT_DIR, ic_ref_img_name))

    generated_videos = []
    latest_video = None

    for i in range(total_videos):
        p = prompts[i]
        label = f"phân cảnh {i + 1}/{total_videos}"

        raw_first_path = first_img_inputs[i]
        raw_last_path = last_img_inputs[i]

        current_first_path, current_last_path, first_source_note = resolve_scene_first_image(
            i, raw_first_path, raw_last_path, latest_video, char_ref_path, char_mode, periodic_n, frame_percent)

        if ic_ref_img_name and ic_lora_name and ic_lora_name != NO_LORA_LABEL:
            first_source_note = (first_source_note or "T2V") + " + 🧬 IC-LoRA guide"

        lora_kwargs = dict(lora1_name=lora1_name, lora1_strength=lora1_strength,
                            lora2_name=lora2_name, lora2_strength=lora2_strength,
                            ic_lora_name=ic_lora_name, ic_lora_strength=ic_lora_strength,
                            ic_ref_image_name=ic_ref_img_name, ic_guide_strength=ic_guide_strength,
                            voice_ref_audio_name=voice_ref_name)

        if current_first_path is not None and current_last_path is not None:
            yield generated_videos, None, f"🔄 Đang quay {label} [FLF2V: Đầu→Cuối, {first_source_note}]...\n📝 Nội dung: {p}"
            first_img_name = f"flfsb_first_{i}_{int(time.time())}.png"
            last_img_name = f"flfsb_last_{i}_{int(time.time())}.png"
            shutil.copy(current_first_path, os.path.join(INPUT_DIR, first_img_name))
            shutil.copy(current_last_path, os.path.join(INPUT_DIR, last_img_name))
            wf = build_flf2v_workflow(first_image_name=first_img_name, last_image_name=last_img_name,
                                       prompt_text=p, width=safe_width, height=safe_height, fps=v_fps,
                                       duration=v_length, seed=base_seed,
                                       first_strength=first_strength, last_strength=last_strength, **lora_kwargs)
        elif current_first_path is not None:
            yield generated_videos, None, f"🔄 Đang quay {label} [I2V: chỉ Đầu, {first_source_note}]...\n📝 Nội dung: {p}"
            img_name = f"flfsb_i2v_{i}_{int(time.time())}.png"
            shutil.copy(current_first_path, os.path.join(INPUT_DIR, img_name))
            wf = build_i2v_workflow(image_name=img_name, prompt_text=p, width=safe_width, height=safe_height,
                                     fps=v_fps, duration=v_length, seed=base_seed, image_strength=image_strength,
                                     **lora_kwargs)
        else:
            yield generated_videos, None, f"🔄 Đang quay {label} [T2V: không có ảnh, tự vẽ từ prompt]...\n📝 Nội dung: {p}"
            wf = build_t2v_workflow(prompt_text=p, width=safe_width, height=safe_height, fps=v_fps,
                                     duration=v_length, seed=base_seed, **lora_kwargs)

        try:
            submit_and_wait(wf, scene_label=label)
        except Exception as e:
            yield generated_videos, None, f"❌ {e}"
            return

        scene_video = find_latest_video()
        if not scene_video:
            yield generated_videos, None, f"⚠️ Không tìm thấy file video {i + 1}!"
            return

        latest_video = scene_video
        generated_videos.append(scene_video)
        if voice_ref_name is None and auto_voice_lock and i == 0:
            auto_ref_path = os.path.join(INPUT_DIR, f"voice_ref_auto_{int(time.time())}.wav")
            if extract_audio_track(latest_video, auto_ref_path):
                voice_ref_name = os.path.basename(auto_ref_path)
        yield generated_videos, None, f"🔔 [DING] ✅ Xong {label}."

    if len(generated_videos) > 1:
        yield generated_videos, None, "🔄 Đang tiến hành ghép nối các phân cảnh..."
        try:
            final_output = concat_videos(generated_videos, "final_storyboard_flf_video")
        except Exception as e:
            yield generated_videos, None, f"⚠️ {e}"
            return
        yield generated_videos, final_output, f"🔔 [DING] 🎉 Đã gộp xong phim! Base Seed: {base_seed}"
    elif len(generated_videos) == 1:
        yield generated_videos, generated_videos[0], f"🔔 [DING] 🎉 Render Complete! (Seed: {base_seed})"
    else:
        yield None, None, "❌ Không tạo được video nào."


# ==========================================================================
# GIAO DIỆN GRADIO (CSS + JS BỔ SUNG ÂM THANH NOTIFICATION)
# ==========================================================================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.gradio-container { font-family: 'Inter', sans-serif !important; width: 100%; max-width: 1600px; margin: 0 auto; padding: 0 20px; }

#header-banner { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #a855f7 100%); border-radius: 18px; padding: 22px 28px; margin-bottom: 12px; box-shadow: 0 6px 24px rgba(79, 70, 229, 0.25); }
#header-banner h1 { color: #ffffff !important; margin: 0 !important; font-size: 1.5rem !important; font-weight: 700 !important; }
#header-banner p { color: rgba(255,255,255,0.9) !important; margin: 4px 0 0 0 !important; font-size: 0.92rem !important; }

#restart-row { background: var(--background-fill-secondary); border: 1px solid var(--border-color-primary); border-radius: 12px; padding: 10px 14px; margin-bottom: 14px; }

.settings-card, .output-card { border-radius: 16px !important; }

.info-callout { background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366f1; padding: 10px 16px; border-radius: 8px; font-size: 0.88rem !important; margin-bottom: 8px; }
.info-callout p { margin: 0 !important; }

.scene-counter { display: inline-block; background: rgba(99, 102, 241, 0.12); padding: 6px 14px; border-radius: 999px; font-weight: 600 !important; font-size: 0.85rem !important; margin: 2px 0 6px 0 !important; }
.scene-counter p { margin: 0 !important; color: #4f46e5 !important; }

.status-box textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 0.82rem !important; line-height: 1.45 !important; }

.scroll-row { flex-wrap: nowrap !important; overflow-x: auto !important; padding: 4px 4px 6px 4px; align-items: flex-start; gap: 10px !important; scrollbar-width: thin; }
.scroll-row::-webkit-scrollbar { height: 6px; }
.scroll-row::-webkit-scrollbar-track { background: transparent; }
.scroll-row::-webkit-scrollbar-thumb { background: var(--border-color-accent, #a5a5c0); border-radius: 8px; }

.scroll-item { min-width: 170px !important; max-width: 170px !important; flex: 0 0 auto !important; border-radius: 12px !important; overflow: hidden; transition: transform 0.15s ease, box-shadow 0.15s ease; }
.scroll-item img { height: 120px !important; object-fit: cover; }
.scroll-item:hover { transform: translateY(-3px); box-shadow: 0 8px 18px rgba(0,0,0,0.18); }
.scroll-item-last { opacity: 0.94; }

button.primary { font-weight: 600 !important; border-radius: 10px !important; }
.tab-nav button { font-weight: 600 !important; }

#top-panel { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 60%, #a855f7 100%); border-radius: 18px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 6px 24px rgba(79, 70, 229, 0.25); }
.top-row { margin-bottom: 10px; }
#top-panel textarea { background: rgba(255,255,255,0.15) !important; color: #fff !important; border: none !important; }
#top-panel h1 { color: #fff !important; margin: 0 !important; font-size: 1.4rem !important; }
#top-panel p { color: rgba(255,255,255,0.9) !important; }

.control-col { display: flex; flex-direction: column; justify-content: center; align-items: flex-end; gap: 8px; }
.control-col button { height: 34px !important; font-size: 0.82rem !important; padding: 0 12px !important; border-radius: 999px !important; background: rgba(255,255,255,0.15) !important; color: #fff !important; border: 1px solid rgba(255,255,255,0.25) !important; backdrop-filter: blur(6px); }
.control-col button:hover { background: rgba(255,255,255,0.25) !important; }

.status-pill { font-size: 0.8rem; padding: 6px 12px; border-radius: 999px; background: rgba(0,0,0,0.25); color: #fff; display: inline-block; backdrop-filter: blur(6px); }
"""

# Đoạn JavaScript tự lắng nghe Status Box thay đổi và phát tiếng chuông Web Audio
notification_js = """
function() {
    let lastText = "";
    function playNotificationSound() {
        try {
            let ctx = new (window.AudioContext || window.webkitAudioContext)();
            let osc = ctx.createOscillator();
            let gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime); // Nốt A5 (880Hz) bổng dịu
            osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.15);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.4);
        } catch(e) { console.log(e); }
    }

    const observer = new MutationObserver(() => {
        let textboxes = document.querySelectorAll('.status-box textarea');
        textboxes.forEach(tb => {
            let txt = tb.value || "";
            if (txt.includes('[DING]') && txt !== lastText) {
                lastText = txt;
                playNotificationSound();
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
}
"""

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="violet", neutral_hue="slate"),
    title="LTX-2.5 AI Video Studio",
    css=custom_css,
    js=notification_js,
    fill_width=True,
) as demo:

    with gr.Column(elem_id="top-panel"):
        with gr.Row():
            with gr.Column(scale=3, min_width=400):
                gr.Markdown(
                    """
                    # 🎬 LTX-2.5 AI Video Studio
                    Tạo video AI từ ảnh tĩnh (I2V) · Tự vẽ từ prompt (T2V) · Nối 2 khung Đầu/Cuối (FLF2V)

                    <div style="margin-top:6px; font-size:13px; opacity:0.85;">
                    ⚡ LTX-2.5 chính thức · 🎭 Hỗ trợ LoRA giữ nhân vật + chế độ bám ảnh tham khảo 100% ·
                    🧬 IC-LoRA Ingredients (cơ chế attention chuẩn xác) ở Tab 2 & Tab 3 ·
                    🎯 Chất lượng đầu ra mặc định: chuẩn HD 720p trở lên · v0.5.0
                    </div>
                    """
                )
            with gr.Column(scale=2, min_width=280, elem_classes="control-col"):
                restart_btn = gr.Button("🔄 Restart", size="sm")
                restart_status = gr.Markdown("🟢 Server sẵn sàng", elem_classes="status-pill")
        restart_btn.click(fn=force_restart_server, outputs=[restart_status])

    # Bộ tỉ lệ khung hình: 3 lựa chọn đầu là chuẩn HD 720p (mặc định), 2 lựa chọn
    # sau là các tuỳ chọn độ phân giải thấp hơn để tiết kiệm VRAM / render nhanh
    # khi cần thử nghiệm prompt.
    ratio_choices = [
        "9:16 (720x1280) · HD 720p Dọc",
        "16:9 (1280x720) · HD 720p Ngang",
        "1:1 (720x720) · HD 720p Vuông",
        "9:16 (480x832) · Nhẹ / Tiết kiệm VRAM",
        "16:9 (832x480) · Nhẹ / Tiết kiệm VRAM",
    ]

    def _lora_controls_block(default_lora1):
        """Tạo cụm control LoRA "thẳng" (LoraLoaderModelOnly) dùng chung cho cả
        3 tab (giảm lặp code). LƯU Ý: đây KHÔNG phải cơ chế IC-LoRA Ingredients
        (không đọc ảnh tham khảo) — muốn dùng đúng cơ chế đó, xem cụm
        "🧬 IC-LoRA Ingredients" (chỉ có ở Tab 2/Tab 3, đi kèm ảnh tham khảo)."""
        gr.Markdown("**🎭 LoRA giữ nhân vật / phong cách (nạp thẳng — không đọc ảnh tham khảo)**")
        with gr.Row():
            lora1_dd = gr.Dropdown(label="LoRA #1", choices=list_available_loras(), value=default_lora1, scale=3)
            lora1_str = gr.Slider(label="Cường độ #1", minimum=0.0, maximum=2.0, step=0.05, value=1.0, scale=2)
        with gr.Row():
            lora2_dd = gr.Dropdown(label="LoRA #2 (tuỳ chọn — vd LoRA phong cách/tốc độ)",
                                    choices=list_available_loras(), value=NO_LORA_LABEL, scale=3)
            lora2_str = gr.Slider(label="Cường độ #2", minimum=0.0, maximum=2.0, step=0.05, value=0.6, scale=2)
        refresh_btn = gr.Button("🔄 Refresh danh sách LoRA (models/loras/)", size="sm")
        refresh_btn.click(fn=refresh_lora_dropdowns, outputs=[lora1_dd, lora2_dd])
        return lora1_dd, lora1_str, lora2_dd, lora2_str

    def _ic_lora_controls_block():
        """Cụm control cho IC-LoRA Ingredients — cơ chế CHUẨN XÁC (dùng
        LTXICLoRALoaderModelOnly + LTXAddVideoICLoRAGuide) để model thật sự
        "nhìn thấy" ảnh tham khảo qua attention, thay vì chỉ đổi trọng số như
        LoRA #1/#2 ở trên. CHỈ có tác dụng khi bạn CŨNG đã tải 'Ảnh tham khảo
        nhân vật' — nếu bỏ trống ảnh, control này không làm gì (workflow chạy
        y hệt như không bật)."""
        gr.Markdown("**🧬 IC-LoRA Ingredients (cơ chế chuẩn xác — cần 'Ảnh tham khảo nhân vật' ở trên)**")
        with gr.Row():
            ic_lora_dd = gr.Dropdown(label="File IC-LoRA Ingredients", choices=list_available_loras(),
                                      value=default_ic_lora_choice(), scale=3)
            ic_lora_str = gr.Slider(label="Cường độ LoRA", minimum=0.0, maximum=2.0, step=0.05, value=1.0, scale=2,
                                     info="Khuyến nghị chính chủ: 1.0")
        ic_guide_str = gr.Slider(label="Cường độ bám ảnh tham khảo (guide strength)",
                                  minimum=0.0, maximum=1.0, step=0.05, value=1.0,
                                  info="1.0 = bám sát ảnh tham khảo nhất. Giảm nếu muốn model tự do hơn")
        ic_refresh_btn = gr.Button("🔄 Refresh danh sách IC-LoRA (models/loras/)", size="sm")
        ic_refresh_btn.click(fn=lambda: gr.update(choices=list_available_loras()), outputs=[ic_lora_dd])
        return ic_lora_dd, ic_lora_str, ic_guide_str

    with gr.Tabs():
        # ================================================================
        # TAB 1 — I2V
        # ================================================================
        with gr.Tab("🖼️ PIPE 1: Ảnh → Video"):
            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Group(elem_classes="settings-card"):
                        prompt_i2v = gr.Textbox(label="📝 Câu lệnh (Prompt)", lines=4,
                                                 placeholder="Mô tả hành động của bức ảnh bằng tiếng Anh...")
                        image_i2v = gr.Image(label="🖼️ Upload Khung Hình Gốc", type="filepath")

                    with gr.Accordion("⚙️ Cài đặt nâng cao", open=False):
                        gr.Markdown("**📐 Kích thước**")
                        ratio_i2v = gr.Radio(label="Tỉ lệ khung hình", choices=ratio_choices, value=ratio_choices[0],
                                             info="Mặc định chuẩn HD 720p trở lên. Chọn nhóm 'Nhẹ' nếu GPU yếu / muốn render nhanh")
                        with gr.Row():
                            length_i2v = gr.Slider(label="⏱️ Thời lượng MỖI đoạn (giây)", minimum=1, maximum=10, step=1, value=5)
                            fps_i2v = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24,
                                                 info="Tự động chốt về bội số của 8 để đảm bảo đúng chuẩn khung hình")

                        gr.Markdown("**🎲 Seed & nối đoạn**")
                        with gr.Row():
                            seed_i2v = gr.Number(label="Seed (-1 = ngẫu nhiên)", value=-1, precision=0)
                            num_segments = gr.Slider(label="🔢 Số phân đoạn cần nối", minimum=1, maximum=10, step=1, value=2)
                        with gr.Row():
                            frame_percent_i2v = gr.Slider(label="🎯 Vị trí khung nối (%)", minimum=50, maximum=100, step=1, value=90,
                                                           info="100% = khung cuối cùng")
                            fixed_seed_i2v = gr.Checkbox(label="🔗 Dùng chung 1 Seed cho mọi đoạn", value=False)
                        image_strength_i2v = gr.Slider(label="🔒 Độ bám ảnh gốc (Pass 1)", minimum=0.3, maximum=1.0,
                                                        step=0.05, value=0.7,
                                                        info="Tăng gần 1.0 để giữ nhân vật/bối cảnh sát ảnh gốc hơn xuyên suốt 10s")

                        lora1_i2v, lora1_str_i2v, lora2_i2v, lora2_str_i2v = _lora_controls_block(_DEFAULT_DISTILLED_LORA or NO_LORA_LABEL)

                        gr.Markdown("**🎤 Khoá giọng nói (thử nghiệm)**",
                                    elem_id="voice-lock-i2v")
                        with gr.Row():
                            voice_ref_i2v = gr.Audio(label="Giọng nói tham khảo (.wav/.mp3, tuỳ chọn)", type="filepath")
                            auto_voice_i2v = gr.Checkbox(label="Tự động khoá theo giọng đoạn 1", value=False,
                                                          info="Chỉ áp dụng nếu không tải audio tham khảo ở trên")

                        vram_i2v = gr.Checkbox(label="🧊 Bật chế độ Low VRAM Mode", value=True,
                                                info="Bật nếu GPU có VRAM thấp, giúp tránh tràn bộ nhớ")

                with gr.Column(scale=7):
                    with gr.Group(elem_classes="output-card"):
                        video_out_i2v = gr.Video(label="🎥 Output Video Liền Mạch", height=380)
                        with gr.Row():
                            btn_i2v = gr.Button("🎬 Bắt Đầu Tạo", variant="primary")
                            clear_i2v = gr.Button("🗑️ Clear")
                        status_i2v = gr.Textbox(label="ℹ️ Status", interactive=False, lines=2, elem_classes="status-box")

            btn_i2v.click(
                fn=generate_long_video_gradio,
                inputs=[image_i2v, prompt_i2v, ratio_i2v, length_i2v, fps_i2v, seed_i2v, num_segments, vram_i2v,
                        frame_percent_i2v, fixed_seed_i2v, image_strength_i2v,
                        lora1_i2v, lora1_str_i2v, lora2_i2v, lora2_str_i2v,
                        voice_ref_i2v, auto_voice_i2v],
                outputs=[video_out_i2v, status_i2v],
            )
            clear_i2v.click(fn=lambda: (None, None, ""), outputs=[video_out_i2v, status_i2v, prompt_i2v])

        # ================================================================
        # TAB 2 — Chuỗi kịch bản nối tiếp
        # ================================================================
        with gr.Tab("🎞️ PIPE 2"):
            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Group(elem_classes="settings-card"):
                        prompt_seq = gr.Textbox(label="📝 Kịch bản (mỗi phân cảnh cách nhau 1 dòng trống ~ 2 lần Enter)", lines=5)
                        scene_count_display = gr.Markdown("🔹 **Số phân cảnh nhận diện được:** 0", elem_classes="scene-counter")
                        image_seq = gr.Image(label="🖼️ Tải ảnh gốc (Upload Image)", type="filepath")

                    gr.Markdown(
                        "<div class='info-callout'>🎭 <b>Ảnh tham khảo nhân vật</b> (tuỳ chọn) — 1 ảnh chụp rõ "
                        "toàn bộ nhân vật (mặt + trang phục). Khi bật chế độ bám nhân vật bên dưới, ảnh này sẽ "
                        "được dùng làm ảnh gốc cho các cảnh thay vì khung hình trích từ cảnh trước (vốn dễ trôi "
                        "mặt/lệch trang phục dần qua nhiều đoạn 10s).</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        char_ref_seq = gr.Image(label="🎭 Ảnh tham khảo nhân vật (tuỳ chọn)", type="filepath")
                        char_mode_seq = gr.Radio(label="Chế độ đồng bộ nhân vật giữa các cảnh",
                                                  choices=CHAR_MODE_CHOICES, value=CHAR_MODE_SMOOTH)
                        periodic_n_seq = gr.Slider(label="Bám lại mỗi N cảnh (chỉ dùng cho chế độ Kết hợp)",
                                                    minimum=2, maximum=10, step=1, value=3)

                    gr.Markdown(
                        "<div class='info-callout'>🧬 <b>IC-LoRA Ingredients</b> (tuỳ chọn, khuyến nghị nếu đã tải "
                        "ảnh tham khảo ở trên) — nạp đúng cơ chế attention chuyên dụng để model thực sự 'đọc' được "
                        "ảnh tham khảo, thay vì chỉ đổi trọng số như LoRA #1/#2 thường. Không bắt buộc chọn cùng "
                        "chế độ bám nhân vật ở trên — 2 cơ chế bổ trợ nhau, cứ có ảnh tham khảo + chọn file ở đây "
                        "là mọi cảnh đều được tiêm guide.</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        ic_lora_seq, ic_lora_str_seq, ic_guide_str_seq = _ic_lora_controls_block()

                    gr.Markdown(
                        "<div class='info-callout'>🎤 <b>Giọng nói tham khảo</b> (tuỳ chọn, thử nghiệm) — 1 đoạn "
                        "audio mẫu rõ giọng (.wav/.mp3). Dùng node LTX chính thức LTXVSetAudioRefTokens để cố ép "
                        "model bám theo đúng giọng này ở mọi cảnh, tránh đổi giọng nam/nữ lẫn lộn giữa các lượt tạo "
                        "riêng biệt. LTX xác nhận node này kỹ nhất trong pipeline Dub-It — dùng ngoài luồng đó CHƯA "
                        "được xác nhận chính thức, nên test 1 cảnh trước khi chạy hàng loạt.</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        voice_ref_seq = gr.Audio(label="🎤 Giọng nói tham khảo (tuỳ chọn)", type="filepath")
                        auto_voice_seq = gr.Checkbox(label="🔁 Tự động khoá theo giọng của cảnh 1 (nếu không tải audio ở trên)",
                                                      value=False)

                    with gr.Accordion("⚙️ Cài đặt nâng cao", open=False):
                        gr.Markdown("**📐 Kích thước**")
                        ratio_seq = gr.Radio(label="Tỉ lệ khung hình", choices=ratio_choices, value=ratio_choices[0],
                                              info="Mặc định chuẩn HD 720p trở lên")
                        with gr.Row():
                            length_seq = gr.Slider(label="⏱️ Thời lượng (giây)", minimum=1, maximum=10, step=1, value=5)
                            fps_seq = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24)

                        gr.Markdown("**🎲 Seed & nối cảnh**")
                        with gr.Row():
                            seed_seq = gr.Number(label="Seed (-1 = ngẫu nhiên)", value=-1, precision=0)
                            frame_percent_seq = gr.Slider(label="🎯 Lấy khung nối tiếp (%)", minimum=50, maximum=100, step=1, value=90,
                                                           info="100% = khung hình cuối cùng của clip")
                        image_strength_seq = gr.Slider(label="🔒 Độ bám ảnh gốc (Pass 1)", minimum=0.3, maximum=1.0,
                                                        step=0.05, value=0.7,
                                                        info="Tăng gần 1.0 để mỗi cảnh bám sát ảnh gốc/ảnh tham khảo hơn")

                        lora1_seq, lora1_str_seq, lora2_seq, lora2_str_seq = _lora_controls_block(_DEFAULT_DISTILLED_LORA or NO_LORA_LABEL)

                        vram_seq = gr.Checkbox(label="🧊 Low VRAM Mode", value=True)

                with gr.Column(scale=5):
                    with gr.Group(elem_classes="output-card"):
                        gallery_seq = gr.Gallery(label="🎥 Các Phân Cảnh Lẻ", columns=2, height="auto")
                        video_out_seq = gr.Video(label="🎬 Phim Dài Hoàn Chỉnh")
                        with gr.Row():
                            btn_seq = gr.Button("🎬 Tạo Video", variant="primary")
                            clear_seq = gr.Button("🗑️ Clear")
                        status_seq = gr.Textbox(label="ℹ️ Status", interactive=False, lines=2, elem_classes="status-box")

            prompt_seq.change(fn=count_scenes, inputs=[prompt_seq], outputs=[scene_count_display])
            btn_seq.click(
                fn=generate_sequence_i2v_gradio,
                inputs=[image_seq, prompt_seq, ratio_seq, length_seq, fps_seq, seed_seq, vram_seq, frame_percent_seq,
                        image_strength_seq, lora1_seq, lora1_str_seq, lora2_seq, lora2_str_seq,
                        char_ref_seq, char_mode_seq, periodic_n_seq,
                        ic_lora_seq, ic_lora_str_seq, ic_guide_str_seq,
                        voice_ref_seq, auto_voice_seq],
                outputs=[gallery_seq, video_out_seq, status_seq],
            )
            clear_seq.click(
                fn=lambda: (None, None, None, "", "🔹 **Số phân cảnh nhận diện được:** 0"),
                outputs=[gallery_seq, video_out_seq, status_seq, prompt_seq, scene_count_display],
            )

        # ================================================================
        # TAB 3 — Storyboard (T2V / I2V / FLF2V tự động)
        # ================================================================
        with gr.Tab("🎯 PIPE 3: Storyboard"):
            gr.Markdown(
                "<div class='info-callout'>💡 Cảnh 1 <b>không bắt buộc</b> phải có Ảnh Đầu nữa — bỏ trống cả 2 ô "
                "ảnh thì hệ thống sẽ tự dùng <b>Text-to-Video (T2V)</b> để vẽ cảnh mở đầu thẳng từ prompt (trừ khi "
                "bạn bật chế độ bám nhân vật bên dưới, khi đó ảnh tham khảo nhân vật sẽ tự được dùng thay T2V).</div>"
            )
            with gr.Row(elem_classes="scroll-row"):
                images_flfsb_first = []
                for i in range(MAX_FLF_SB_SCENES):
                    img = gr.Image(label=f"Cảnh {i + 1} · Đầu (tuỳ chọn)", type="filepath", elem_classes="scroll-item", visible=False)
                    images_flfsb_first.append(img)
            with gr.Row(elem_classes="scroll-row"):
                images_flfsb_last = []
                for i in range(MAX_FLF_SB_SCENES):
                    img = gr.Image(label=f"Cảnh {i + 1} · Cuối (tuỳ chọn)", type="filepath",
                                    elem_classes=["scroll-item", "scroll-item-last"], visible=False)
                    images_flfsb_last.append(img)

            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Group(elem_classes="settings-card"):
                        prompt_flfsb = gr.Textbox(label="📝 Kịch bản (mỗi phân cảnh cách nhau 1 dòng trống ~ 2 lần Enter)", lines=5)
                        scene_count_display_flfsb = gr.Markdown("🔹 **Số phân cảnh nhận diện được:** 0", elem_classes="scene-counter")

                    gr.Markdown(
                        "<div class='info-callout'>🎭 <b>Ảnh tham khảo nhân vật</b> (tuỳ chọn) — dùng để tự động "
                        "'neo' nhân vật vào các cảnh KHÔNG có ảnh Đầu upload thủ công, thay vì để trôi theo khung "
                        "hình cảnh trước hoặc vẽ tự do bằng T2V.</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        char_ref_flfsb = gr.Image(label="🎭 Ảnh tham khảo nhân vật (tuỳ chọn)", type="filepath")
                        char_mode_flfsb = gr.Radio(label="Chế độ đồng bộ nhân vật giữa các cảnh",
                                                    choices=CHAR_MODE_CHOICES, value=CHAR_MODE_SMOOTH)
                        periodic_n_flfsb = gr.Slider(label="Bám lại mỗi N cảnh (chỉ dùng cho chế độ Kết hợp)",
                                                      minimum=2, maximum=10, step=1, value=3)

                    gr.Markdown(
                        "<div class='info-callout'>🧬 <b>IC-LoRA Ingredients</b> (tuỳ chọn, khuyến nghị nếu đã tải "
                        "ảnh tham khảo ở trên) — áp dụng cho MỌI phân cảnh trong storyboard (dù cảnh đó render kiểu "
                        "T2V/I2V/FLF2V), độc lập với việc ảnh tham khảo có được dùng làm ảnh Đầu hay không.</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        ic_lora_flfsb, ic_lora_str_flfsb, ic_guide_str_flfsb = _ic_lora_controls_block()

                    gr.Markdown(
                        "<div class='info-callout'>🎤 <b>Giọng nói tham khảo</b> (tuỳ chọn, thử nghiệm) — dùng node "
                        "LTX chính thức LTXVSetAudioRefTokens để cố ép mọi cảnh (T2V/I2V/FLF2V) bám theo cùng 1 "
                        "giọng, tránh đổi giọng nam/nữ lẫn lộn giữa các phân cảnh. Hiệu quả ngoài pipeline Dub-It "
                        "CHƯA được LTX xác nhận chính thức — nên test 1 cảnh trước khi chạy hàng loạt.</div>"
                    )
                    with gr.Group(elem_classes="settings-card"):
                        voice_ref_flfsb = gr.Audio(label="🎤 Giọng nói tham khảo (tuỳ chọn)", type="filepath")
                        auto_voice_flfsb = gr.Checkbox(label="🔁 Tự động khoá theo giọng của cảnh 1 (nếu không tải audio ở trên)",
                                                        value=False)

                    with gr.Accordion("⚙️ Cài đặt nâng cao", open=False):
                        gr.Markdown("**📐 Kích thước**")
                        ratio_flfsb = gr.Radio(label="Tỉ lệ khung hình", choices=ratio_choices, value=ratio_choices[0],
                                                info="Mặc định chuẩn HD 720p trở lên")
                        with gr.Row():
                            length_flfsb = gr.Slider(label="⏱️ Thời lượng mỗi cảnh (giây)", minimum=1, maximum=10, step=1, value=5)
                            fps_flfsb = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24,
                                                   info="Tự động chốt về bội số của 8 — đảm bảo tổng khung hình luôn đúng chuẩn LTX-2.5")

                        gr.Markdown("**🎲 Seed & nối cảnh**")
                        with gr.Row():
                            seed_flfsb = gr.Number(label="Seed (-1 = ngẫu nhiên)", value=-1, precision=0)
                            frame_percent_flfsb = gr.Slider(label="🎯 Lấy khung nối tiếp (%)", minimum=50, maximum=100, step=1, value=100)

                        gr.Markdown("**🔒 Độ bám khung (chỉ áp dụng cho cảnh có cả Ảnh Đầu + Ảnh Cuối)**")
                        with gr.Row():
                            first_strength_flfsb = gr.Slider(
                                label="🔓 Độ bám Ảnh Đầu", minimum=0.1, maximum=1.0, step=0.05, value=0.7,
                                info="Mặc định chính thức của LTX-2.5 là 0.7 — tăng lên gần 1.0 nếu muốn bám nhân vật chặt hơn",
                            )
                            last_strength_flfsb = gr.Slider(
                                label="🔒 Độ bám Ảnh Cuối", minimum=0.1, maximum=1.0, step=0.05, value=0.7,
                                info="Mặc định chính thức của LTX-2.5 là 0.7",
                            )
                        image_strength_flfsb = gr.Slider(label="🔒 Độ bám ảnh gốc I2V (Pass 1)", minimum=0.3, maximum=1.0,
                                                          step=0.05, value=0.7,
                                                          info="Áp dụng cho các cảnh chỉ có Ảnh Đầu (chế độ I2V)")

                        lora1_flfsb, lora1_str_flfsb, lora2_flfsb, lora2_str_flfsb = _lora_controls_block(_DEFAULT_DISTILLED_LORA or NO_LORA_LABEL)

                        vram_flfsb = gr.Checkbox(label="🧊 Low VRAM Mode", value=False)

                with gr.Column(scale=5):
                    with gr.Group(elem_classes="output-card"):
                        gallery_flfsb = gr.Gallery(label="🎥 Các Phân Cảnh Lẻ", columns=2, height="auto")
                        video_out_flfsb = gr.Video(label="🎬 Phim Dài Hoàn Chỉnh")
                        with gr.Row():
                            btn_flfsb = gr.Button("🎬 Tạo Video", variant="primary")
                            clear_flfsb = gr.Button("🗑️ Clear")
                        status_flfsb = gr.Textbox(label="ℹ️ Status", interactive=False, lines=2, elem_classes="status-box")

            prompt_flfsb.change(
                fn=update_storyboard_flf_ui,
                inputs=[prompt_flfsb],
                outputs=[scene_count_display_flfsb] + images_flfsb_first + images_flfsb_last,
            )
            btn_flfsb.click(
                fn=generate_storyboard_flf_gradio,
                inputs=[*images_flfsb_first, *images_flfsb_last, prompt_flfsb, ratio_flfsb, length_flfsb, fps_flfsb,
                        seed_flfsb, vram_flfsb, frame_percent_flfsb, first_strength_flfsb, last_strength_flfsb,
                        image_strength_flfsb, lora1_flfsb, lora1_str_flfsb, lora2_flfsb, lora2_str_flfsb,
                        char_ref_flfsb, char_mode_flfsb, periodic_n_flfsb,
                        ic_lora_flfsb, ic_lora_str_flfsb, ic_guide_str_flfsb,
                        voice_ref_flfsb, auto_voice_flfsb],
                outputs=[gallery_flfsb, video_out_flfsb, status_flfsb],
            )

            def clear_all_flfsb():
                first_clears = [gr.update(value=None, visible=False)] * MAX_FLF_SB_SCENES
                last_clears = [gr.update(value=None, visible=False)] * MAX_FLF_SB_SCENES
                return tuple(first_clears + last_clears + [None, None, "", "", "🔹 **Số phân cảnh nhận diện được:** 0"])

            clear_flfsb.click(
                fn=clear_all_flfsb,
                outputs=[*images_flfsb_first, *images_flfsb_last, gallery_flfsb, video_out_flfsb, status_flfsb,
                         prompt_flfsb, scene_count_display_flfsb],
            )

# Khởi chạy Gradio
demo.queue()
demo.launch(share=True, inline=False, debug=True)