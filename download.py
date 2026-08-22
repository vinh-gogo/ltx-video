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
DOWNLOAD_CHARACTER_LORA = True
DOWNLOAD_MSR_LORA = True  # LoRA Multi-Subject Reference (LiconStudio MSR V1) cho Cell MSR (ltx2_5_msr.py)

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
# ComfyUI-LTX2.5-MSR + ComfyUI-PromptRelay: cần cho Cell MSR (ltx2_5_msr.py)
# — MSR Multi-Subject Reference, cho phép dùng tới 4 ảnh tham khảo nhân vật.
log("[2/4] Cloning/updating custom nodes...")
get_ipython().run_line_magic("cd", "-q /content/ComfyUI/custom_nodes")

CUSTOM_NODES = [
    "https://github.com/kijai/ComfyUI-KJNodes",
    "https://github.com/city96/ComfyUI-GGUF",
    "https://github.com/Lightricks/ComfyUI-LTXVideo/",
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite",
    "https://github.com/kijai/ComfyUI-MelBandRoFormer",
    # --- MSR (Multi-Subject Reference — dùng cho Cell MSR ltx2_5_msr.py) ---
    "https://github.com/liconstudio/ComfyUI-LTX2.5-MSR",
    "https://github.com/kijai/ComfyUI-PromptRelay",
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

# LoRA MSR (Multi-Subject Reference — dùng cho Cell MSR ltx2_5_msr.py).
# Repo: LiconStudio/LTX-2.5-Multiple-Subject-Reference (hỗ trợ 1-5 ảnh tham khảo).
MSR_LORA_REPO = "LiconStudio/LTX-2.5-Multiple-Subject-Reference"
MSR_LORA_FILENAME = "LTX-2.5-Licon-MSR-V1.safetensors"


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
            if gated and "401" in (result.stderr or "") or gated and "403" in (result.stderr or ""):
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

if DOWNLOAD_MSR_LORA:
    DOWNLOAD_JOBS.append((
        f"https://huggingface.co/{MSR_LORA_REPO}/resolve/main/{MSR_LORA_FILENAME}",
        "/content/ComfyUI/models/loras/ltx2.5", MSR_LORA_FILENAME, False,
    ))
else:
    log("ℹ️ DOWNLOAD_MSR_LORA=False -> bỏ qua tải LoRA MSR.", color="#90caf9")

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
    msr_note = (
        "<br>🧬 LoRA MSR (Licon MSR V1) đã sẵn sàng trong <code>models/loras/ltx2.5/</code> "
        "— dùng cho Cell MSR (<code>ltx2_5_msr.py</code>)."
        if DOWNLOAD_MSR_LORA else
        ""
    )
    display(HTML(
        "<div style='padding:15px;background-color:#e8f5e9;border-left:5px solid #4caf50;"
        "border-radius:4px;color:#2e7d32;font-family:sans-serif;'>"
        "<b>✨ Initialization Complete!</b> Môi trường LTX-2.5 đã sẵn sàng."
        f"{lora_note}"
        f"{msr_note}"
        "<br><small>⚠️ Nhắc lại: transformer + text encoder chính ~37GB VRAM/weights — "
        "cần GPU 24GB+ (L4/A100). Trên T4 16GB nhiều khả năng sẽ OOM dù bật Low VRAM Mode.</small>"
        "<br><small>⚠️ LoRA Ingredients được train trên LTX-2.3; Lightricks xác nhận đa số "
        "LoRA/IC-LoRA 2.3 chạy được trên 2.5 nhưng khuyến cáo tự kiểm chứng chất lượng trước khi "
        "dùng cho công việc quan trọng.</small>"
        "</div>"
    ))