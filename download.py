# @title [Cell 1 - CẬP NHẬT v2] Cài đặt môi trường ComfyUI + LTX-2.5
#
# --- CẬP NHẬT SO VỚI BẢN TRƯỚC ---
# 1) Ghim phiên bản (commit hash) cho 2 custom node BÊN THỨ BA dùng riêng
#    cho Cell MSR: ComfyUI-LTX2.5-MSR (liconstudio) và ComfyUI-PromptRelay
#    (kijai). Mặc định vẫn để None (tự "git pull" bản mới nhất, y như hành
#    vi cũ) nhưng giờ sẽ CẢNH BÁO rõ ràng mỗi lần chạy, và in ra + lưu lại
#    commit hash hiện tại để bạn dễ dàng ghim lại sau khi đã test ổn định.
# 2) Ghi danh sách commit hash của mọi custom node ra
#    /content/ComfyUI/_node_versions.json — Cell MSR (bản cập nhật) sẽ tự
#    đọc file này để hiển thị công khai trên giao diện Gradio đang chạy
#    node bản nào, thay vì "giấu" hoàn toàn sự phụ thuộc bên thứ ba.
# 3) (MỚI) Cấu hình VRAM THẬT cho ComfyUI. Bản Cell MSR trước đây gọi
#    "Low VRAM Mode" nhưng thực chất chỉ bật cờ --cache-none — cờ đó CHỈ
#    tắt cache kết quả node (để không tính lại node giống hệt lần trước),
#    KHÔNG liên quan gì tới việc giảm VRAM của model (UNET 22B, text
#    encoder 12B...). Đây là lý do máy vẫn tràn VRAM dù đã bật "Low VRAM
#    Mode" kể cả trên GPU 22GB-40GB. Cell này giờ khai báo đúng
#    GPU_VRAM_GB của bạn, tự chọn cờ THẬT (--lowvram / --novram /
#    --reserve-vram) và ghi ra /content/ComfyUI/_vram_config.json để
#    Cell MSR (bản cập nhật) đọc lại khi khởi động server.
#
# Custom nodes cần thiết:
#   - ComfyUI-LTX2.5-MSR   : https://github.com/liconstudio/ComfyUI-LTX2.5-MSR   (BÊN THỨ BA)
#   - ComfyUI-PromptRelay   : https://github.com/kijai/ComfyUI-PromptRelay        (BÊN THỨ BA)
#   - ComfyUI-KJNodes       : https://github.com/kijai/ComfyUI-KJNodes
#
# MSR LoRA đặt tại: /content/ComfyUI/models/loras/ltx2.5/

import concurrent.futures
import json
import os
import shutil
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
        "repository' tại: https://huggingface.co/Lightricks/LTX-2.5 trước khi chạy tiếp.",
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

# Kiểm tra quyền truy cập repo Lightricks/LTX-2.5 ngay tại bước này
try:
    from huggingface_hub import HfApi
    api = HfApi(token=HF_TOKEN)
    api.model_info("Lightricks/LTX-2.5")
    log("✅ Đã xác thực thành công quyền truy cập repo Lightricks/LTX-2.5!", color="#00e676")
except Exception as _e:
    _err_str = str(_e)
    if "403" in _err_str or "gated" in _err_str.lower() or "access" in _err_str.lower():
        log(
            "⚠️ <b>TÀI KHOẢN CHƯA BẤM ACCEPT LICENSE!</b><br>"
            "Repo <code>Lightricks/LTX-2.5</code> yêu cầu bạn phải bấm 'Agree and access repository' bằng tài khoản Hugging Face của token này:<br>"
            "👉 <b>Mở link:</b> <a href='https://huggingface.co/Lightricks/LTX-2.5' target='_blank' style='color:#00e676;font-size:1.1rem;font-weight:bold;'>https://huggingface.co/Lightricks/LTX-2.5</a> và bấm nút <b>'Agree and access repository'</b>.<br>"
            "Sau khi bấm xong, chạy lại Cell 1 là sẽ tải được ngay!",
            color="#ff5252",
        )
    elif "401" in _err_str or "invalid" in _err_str.lower() or "token" in _err_str.lower():
        log(
            "⚠️ <b>HF_TOKEN KHÔNG HỢP LỆ HOẶC HẾT HẠN!</b><br>"
            "Vui lòng tạo token mới tại: <a href='https://huggingface.co/settings/tokens' target='_blank'>https://huggingface.co/settings/tokens</a> (chọn quyền 'Read').",
            color="#ff5252",
        )
    else:
        print(f"Xác thực HF Token: {_err_str}")

# Tải LoRA MSR (Multi-Subject Reference — LiconStudio MSR V1) cho Cell MSR (ltx2_5_msr.py)
DOWNLOAD_MSR_LORA = True

# --------------------------------------------------------------------------
# (Ghim phiên bản node bên thứ ba) — xem giải thích ở [2/4] bên dưới
# --------------------------------------------------------------------------
# ComfyUI-LTX2.5-MSR (liconstudio) và ComfyUI-PromptRelay (kijai) KHÔNG phải
# node chính chủ Lightricks/ComfyUI. Mặc định để None -> mỗi lần chạy cell
# này sẽ tự "git pull" lấy commit mới nhất của 2 repo đó, tiện khi mới thử
# nghiệm nhưng có rủi ro: nếu tác giả đổi tên input/class_type, Cell MSR có
# thể gãy đột ngột mà không báo trước.
#
# Cách ghim lại sau khi đã test workflow chạy ổn định:
#   1) Chạy Cell 1 một lần, đọc commit hash được in ra trong log (dòng
#      "commit hiện tại: xxxxxxx") hoặc mở file
#      /content/ComfyUI/_node_versions.json.
#   2) Dán commit hash đó vào 2 biến bên dưới, ví dụ MSR_NODE_PIN = "a1b2c3d".
#   3) Chạy lại Cell 1 -> từ giờ luôn checkout đúng commit đã ghim, không tự
#      đổi version nữa cho tới khi bạn chủ động sửa lại 2 biến này.
MSR_NODE_PIN     = None  # vd: "a1b2c3d"  (ComfyUI-LTX2.5-MSR)
PROMPT_RELAY_PIN = None  # vd: "9f8e7d6"  (ComfyUI-PromptRelay)

# Khai báo đúng dung lượng VRAM GPU bạn đang chạy (xem ở Colab: Runtime >
# Change runtime type, hoặc chạy !nvidia-smi ở 1 cell riêng) để cell tự
# chọn cờ khởi động phù hợp cho ComfyUI: 16, 22, 24, 40, 80...
GPU_VRAM_GB = 22

def cleanup_and_optimize_disk():
    """Giải phóng tối đa dung lượng ổ đĩa Colab (xóa swapfile cũ 28GB nếu có, dọn cache pip/tmp).
    Vì GPU 22GB đã chạy chế độ 'normal' trực tiếp trên VRAM nên KHÔNG cần swapfile chiếm dung lượng đĩa."""
    try:
        sh("swapoff /content/swapfile > /dev/null 2>&1")
        if os.path.exists("/content/swapfile"):
            os.remove("/content/swapfile")
            log("🧹 Đã xóa /content/swapfile cũ để giải phóng 28GB ổ đĩa cho việc chứa Models!", color="#00e676")
    except Exception:
        pass
    sh("rm -rf /root/.cache/pip /root/.cache/uv /tmp/pip-* /tmp/huggingface* > /dev/null 2>&1")
    total, used, free = shutil.disk_usage("/")
    log(f"💾 Dung lượng ổ đĩa Colab khả dụng: {free / (1024**3):.1f} GB trống / {total / (1024**3):.1f} GB", color="#90caf9")

# --------------------------------------------------------------------------
# [1/4] Cài thư viện lõi + clone/cập nhật ComfyUI
# --------------------------------------------------------------------------
log("[1/4] Installing core dependencies & optimizing disk space...")
cleanup_and_optimize_disk()
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
# [VRAM] Cấu hình chế độ bộ nhớ GPU THẬT cho ComfyUI (ghi sau khi ComfyUI đã clone)
# --------------------------------------------------------------------------
# Với model LTX-2.5 INT8 (UNET ~14GB, Gemma ~8GB), ComfyUI nạp tuần tự từng
# model nên card ≥20GB (22GB, 24GB, 40GB, 80GB) chạy chế độ 'normal' ở TỐC ĐỘ TỐI ĐA
# (~60-90s/cảnh). Chỉ card ≤16GB mới cần 'lowvram' / 'novram' (stream layer qua RAM).
if GPU_VRAM_GB <= 12:
    _vram_mode = "novram"       # GPU ≤12GB: stream triệt để qua RAM
    _reserve_vram_gb = 1.0
elif GPU_VRAM_GB <= 18:
    _vram_mode = "lowvram"      # GPU 16GB: stream nhẹ
    _reserve_vram_gb = 1.5
else:
    _vram_mode = "normal"       # GPU ≥20GB (như 22GB, 24GB, A10G, 4090): TỐC ĐỘ TỐI ĐA TRÊN GPU
    _reserve_vram_gb = 1.5

os.makedirs("/content/ComfyUI", exist_ok=True)
with open("/content/ComfyUI/_vram_config.json", "w") as _vf:
    json.dump(
        {"gpu_vram_gb": GPU_VRAM_GB, "mode": _vram_mode, "reserve_vram_gb": _reserve_vram_gb},
        _vf, indent=2,
    )

log(
    f"🧠 Chế độ VRAM: GPU khai báo {GPU_VRAM_GB}GB → chọn '--{_vram_mode}' "
    f"(reserve {_reserve_vram_gb}GB). Đã ghi vào "
    f"/content/ComfyUI/_vram_config.json.",
    color="#90caf9",
)

# --------------------------------------------------------------------------
# [2/4] Clone/cập nhật custom nodes (ghim phiên bản node bên thứ ba)
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
#
# ComfyUI-LTX2.5-MSR + ComfyUI-PromptRelay: cần cho Cell MSR (ltx2_5_msr.py)
# — MSR Multi-Subject Reference, cho phép dùng tới 4 ảnh tham khảo nhân vật.
# Đây là 2 node BÊN THỨ BA (không phải Lightricks/ComfyUI chính thức) nên
# được xử lý riêng bên dưới: ghim phiên bản qua MSR_NODE_PIN/PROMPT_RELAY_PIN
# nếu đã set, cảnh báo rõ ràng nếu chưa ghim.


def get_git_commit(path):
    """Lấy short commit hash hiện tại của 1 thư mục git — dùng để hiển thị
    minh bạch đang chạy custom node bản nào, đặc biệt hữu ích với 2 node bên
    thứ ba MSR/PromptRelay mà Cell MSR sẽ đọc lại và show lên UI."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "?"
    except Exception:
        return "?"


def checkout_node(repo_url, pinned_ref, is_thirdparty):
    """Clone (nếu chưa có) rồi đưa custom node về đúng trạng thái mong muốn.

    - pinned_ref được set (khác None) -> luôn checkout đúng commit/tag đó,
      KHÔNG tự động đổi version dù chạy lại cell bao nhiêu lần. An toàn cho
      pipeline đã test ổn định.
    - pinned_ref = None -> giữ hành vi cũ: git pull lấy bản mới nhất mỗi lần
      chạy cell. Nếu đây là node bên thứ ba (is_thirdparty=True), in cảnh
      báo rõ ràng vì rủi ro tác giả đổi API làm gãy Cell MSR mà không báo
      trước.
    """
    node_name = repo_url.rstrip("/").split("/")[-1]
    exists = os.path.exists(node_name)

    if not exists:
        sh(f"git clone -q {repo_url}")

    if pinned_ref:
        sh(f"cd {node_name} && git fetch -q --all && git checkout -q {pinned_ref} && cd ..")
        status = f"📌 ghim tại {pinned_ref}"
    else:
        if exists:
            sh(f"cd {node_name} && git pull -q && cd ..")
        status = "🔄 luôn lấy bản mới nhất (main, CHƯA ghim)"
        if is_thirdparty:
            log(
                f"⚠️ {node_name} là custom node BÊN THỨ BA (không phải Lightricks/ComfyUI "
                f"chính thức) và CHƯA được ghim phiên bản -> mỗi lần chạy lại Cell 1 có thể "
                f"tự đổi sang commit mới, có rủi ro gãy Cell MSR nếu tác giả đổi API. Sau khi "
                f"đã test workflow chạy ổn định, khuyến nghị ghim lại bằng commit hash in ra "
                f"ngay bên dưới (điền vào MSR_NODE_PIN / PROMPT_RELAY_PIN ở đầu cell này).",
                color="#ffb300",
            )

    commit = get_git_commit(node_name)
    print(f"   → {node_name}: {status}  (commit hiện tại: {commit})")

    req_file = f"{node_name}/requirements.txt"
    if os.path.exists(req_file):
        pip_install(f"-r {req_file}")

    return node_name, commit


log("[2/4] Cloning/updating custom nodes...")
get_ipython().run_line_magic("cd", "-q /content/ComfyUI/custom_nodes")

CUSTOM_NODES = [
    # (url, pinned_ref, is_thirdparty)
    ("https://github.com/kijai/ComfyUI-KJNodes", None, False),
    ("https://github.com/city96/ComfyUI-GGUF", None, False),
    ("https://github.com/Lightricks/ComfyUI-LTXVideo/", None, False),
    ("https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite", None, False),
    ("https://github.com/kijai/ComfyUI-MelBandRoFormer", None, False),
    # --- MSR (Multi-Subject Reference — dùng cho Cell MSR) — BÊN THỨ BA ---
    ("https://github.com/liconstudio/ComfyUI-LTX2.5-MSR", MSR_NODE_PIN, True),
    ("https://github.com/kijai/ComfyUI-PromptRelay", PROMPT_RELAY_PIN, True),
]

NODE_COMMITS = {}
for repo_url, pinned_ref, is_thirdparty in CUSTOM_NODES:
    node_name, commit = checkout_node(repo_url, pinned_ref, is_thirdparty)
    NODE_COMMITS[node_name] = commit

with open("/content/ComfyUI/_node_versions.json", "w") as _vf:
    json.dump(NODE_COMMITS, _vf, indent=2)
log(
    "📄 Đã ghi lại phiên bản các custom node vào "
    "/content/ComfyUI/_node_versions.json — Cell MSR (bản cập nhật) sẽ tự "
    "đọc file này và hiển thị công khai trên giao diện.",
    color="#90caf9",
)

# --------------------------------------------------------------------------
# [3/4] Tải model weights cho LTX-2.5 + LoRA giữ nhân vật (song song, có log tiến trình)
# --------------------------------------------------------------------------
log("[3/4] Fetching LTX-2.5 model weights (this may take a while — tổng ~40GB)...")

_FAILED_DOWNLOADS = []
_print_lock = threading.Lock()

# Tên file dùng chung cho toàn bộ notebook — Cell 2 / Cell MSR đọc lại các
# biến này.
# Cấu hình mặc định: bản "distilled" (đã tối ưu số bước, KHÔNG cần LoRA
# distill riêng như pipeline LTX-2.3 cũ) — đây là cấu hình ComfyUI chính
# thức khuyến nghị cho cả 3 workflow T2V/I2V/FLF2V.
UNET_FILENAME = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
TEXT_ENCODER_FILENAME = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
# Dùng riêng cho Prompt Enhancer (node TextGenerateLTX2Prompt trong workflow
# I2V gốc, VÀ giờ cũng được Cell MSR bản cập nhật tái sử dụng cho tính năng
# Prompt Enhancer tuỳ chọn của nó — không cần tải thêm gì).
TEXT_ENCODER_ENHANCER_FILENAME = "gemma4_e2b_it_bf16.safetensors"
VIDEO_VAE_FILENAME = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

# LoRA MSR (Multi-Subject Reference — dùng cho Cell MSR ltx2_5_msr.py).
# Repo: LiconStudio/LTX-2.5-Multiple-Subject-Reference (hỗ trợ 1-5 ảnh tham khảo).
MSR_LORA_REPO = "LiconStudio/LTX-2.5-Multiple-Subject-Reference"
MSR_LORA_FILENAME = "LTX-2.5-Licon-MSR-V1.safetensors"


def dl(url, dest, fname, connections=8, gated=False, min_size_mb=100):
    """Tải 1 file bằng aria2c nếu chưa có. An toàn để gọi song song từ nhiều thread.
    Tự động kiểm tra tính toàn vẹn (dung lượng tối thiểu) để phát hiện file hỏng/HTML error."""
    Path(dest).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(dest, fname)
    if os.path.exists(file_path):
        curr_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if curr_size_mb >= min_size_mb:
            with _print_lock:
                print(f"⏭️  Đã có sẵn & hợp lệ ({curr_size_mb:.0f}MB), bỏ qua: {fname}")
            return True
        else:
            with _print_lock:
                print(f"⚠️ Phát hiện file {fname} bị hỏng / tải dở ({curr_size_mb:.2f}MB < {min_size_mb}MB) -> Xóa để tải lại chuẩn...")
            try:
                os.remove(file_path)
            except Exception:
                pass

    with _print_lock:
        print(f"⬇️  Bắt đầu tải: {fname}")

    # Lượt 1: Tải bằng aria2c
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
    ok = result.returncode == 0 and os.path.exists(file_path) and (os.path.getsize(file_path) / (1024 * 1024)) >= min_size_mb

    # Lượt 2: Fallback sang huggingface_hub nếu aria2c không tải được
    if not ok and "huggingface.co" in url:
        try:
            parts = url.split("huggingface.co/")[1].split("/resolve/main/")
            repo_id = parts[0]
            subpath = parts[1]
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id=repo_id,
                filename=subpath,
                local_dir=dest,
                token=HF_TOKEN if gated else None,
            )
            if os.path.exists(downloaded) and downloaded != file_path:
                shutil.move(downloaded, file_path)
            ok = os.path.exists(file_path) and (os.path.getsize(file_path) / (1024 * 1024)) >= min_size_mb
        except Exception as _e:
            pass

    with _print_lock:
        if ok:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✅ Xong: {fname}  ({size_mb:.0f}MB trong {elapsed:.0f}s, ~{size_mb / elapsed:.1f}MB/s)")
        else:
            _FAILED_DOWNLOADS.append(fname)
            print(f"⚠️ Tải thất bại: {fname} -> Kiểm tra quyền Accept License tại https://huggingface.co/Lightricks/LTX-2.5")
    return ok


# Danh sách file cần tải: (url, thư mục đích, tên file, có bị gate hay không, dung lượng tối thiểu MB)
DOWNLOAD_JOBS = [
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/{UNET_FILENAME}",
     "/content/ComfyUI/models/diffusion_models", UNET_FILENAME, True, 5000),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/{TEXT_ENCODER_FILENAME}",
     "/content/ComfyUI/models/text_encoders", TEXT_ENCODER_FILENAME, True, 3000),
    (f"https://huggingface.co/Comfy-Org/gemma-4/resolve/main/text_encoders/{TEXT_ENCODER_ENHANCER_FILENAME}",
     "/content/ComfyUI/models/text_encoders", TEXT_ENCODER_ENHANCER_FILENAME, False, 3000),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{VIDEO_VAE_FILENAME}",
     "/content/ComfyUI/models/vae", VIDEO_VAE_FILENAME, True, 500),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/{AUDIO_VAE_FILENAME}",
     "/content/ComfyUI/models/vae", AUDIO_VAE_FILENAME, True, 100),
    (f"https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/{SPATIAL_UPSCALER_FILENAME}",
     "/content/ComfyUI/models/latent_upscale_models", SPATIAL_UPSCALER_FILENAME, True, 400),
]

if DOWNLOAD_MSR_LORA:
    DOWNLOAD_JOBS.append((
        f"https://huggingface.co/{MSR_LORA_REPO}/resolve/main/{MSR_LORA_FILENAME}",
        "/content/ComfyUI/models/loras/ltx2.5", MSR_LORA_FILENAME, False, 500,
    ))
else:
    log("ℹ️ DOWNLOAD_MSR_LORA=False -> bỏ qua tải LoRA MSR.", color="#90caf9")

# Tải tối đa 3 file cùng lúc, 8 luồng/file.
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(dl, url, dest, fname, 8, gated, min_size) for url, dest, fname, gated, min_size in DOWNLOAD_JOBS]
    concurrent.futures.wait(futures)

# --------------------------------------------------------------------------
# [4/4] Tổng kết
# --------------------------------------------------------------------------
if _FAILED_DOWNLOADS:
    log(f"⚠️ {len(_FAILED_DOWNLOADS)} file tải lỗi: {', '.join(_FAILED_DOWNLOADS)}. "
        f"Kiểm tra HF_TOKEN + đã accept license repo chưa, rồi chạy lại cell này "
        f"(file đã tải xong sẽ tự bỏ qua) trước khi qua Cell 2.",
        color="#ff5252")
else:
    msr_note = (
        "<br>🧬 LoRA MSR (Licon MSR V1) đã sẵn sàng trong <code>models/loras/ltx2.5/</code> "
        "— dùng cho Cell MSR (<code>ltx2_5_msr.py</code>)."
        if DOWNLOAD_MSR_LORA else
        ""
    )
    pin_note = (
        "<br>📌 Phiên bản 2 custom node bên thứ ba (MSR/PromptRelay) đã được ghi vào "
        "<code>_node_versions.json</code> — nếu Cell MSR đột nhiên báo lỗi node sau này, "
        "kiểm tra file này trước, rồi cân nhắc ghim lại (MSR_NODE_PIN / PROMPT_RELAY_PIN) "
        "về commit đang chạy ổn định."
    )
    vram_note = (
        f"<br>🧠 Chế độ VRAM đã ghi vào <code>_vram_config.json</code>: "
        f"<code>--{_vram_mode}</code> cho GPU {GPU_VRAM_GB}GB (reserve {_reserve_vram_gb}GB). "
        f"Cell MSR sẽ tự dùng cấu hình này khi chọn 'auto' trong ô Chế độ VRAM."
    )
    display(HTML(
        "<div style='padding:15px;background-color:#e8f5e9;border-left:5px solid #4caf50;"
        "border-radius:4px;color:#2e7d32;font-family:sans-serif;'>"
        "<b>✨ Initialization Complete!</b> Môi trường LTX-2.5 MSR đã sẵn sàng 100%."
        f"{msr_note}"
        f"{pin_note}"
        f"{vram_note}"
        "<br><br>👉 <b>Bước tiếp theo:</b> Chạy <b>Cell 2 (ltx2_5_msr.py)</b> để mở giao diện WebUI tạo phim MSR!"
        "</div>"
    ))