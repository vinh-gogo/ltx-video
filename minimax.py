# @title [Cell Phần 1] Download MiniMax H3 Models
# Chạy cell này TRƯỚC để tải toàn bộ model MiniMax H3 về Colab.
# Yêu cầu: ComfyUI đã cài sẵn (chạy setup cell trước).
#
# Models cần tải (từ Comfy-Org/MiniMax-H3 trên HuggingFace):
#   diffusion_models/ : minimax_h3_ref2va_pruned_int8_convrot.safetensors
#   text_encoders/    : qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
#   vae/              : minimax_h3_video_vae_fp16.safetensors
#                       minimax_h3_audio_vae_fp32.safetensors
#   loras/            : minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors  (tuỳ chọn)
#
# Cấu trúc thư mục sau khi tải:
#   ComfyUI/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
#   ComfyUI/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
#   ComfyUI/models/vae/minimax_h3_video_vae_fp16.safetensors
#   ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors
#   ComfyUI/models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors

# ==========================================================================
# PHAN 1: DOWNLOAD MODELS
# ==========================================================================

import os

COMFYUI_ROOT = "/content/ComfyUI"

# Danh sach model can tai: (url, duong dan dich trong ComfyUI)
MINIMAX_MODELS = [
    # --- Diffusion model (bat buoc) ---
    (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        f"{COMFYUI_ROOT}/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
    ),
    # --- Text encoder / CLIP (bat buoc) ---
    (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        f"{COMFYUI_ROOT}/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    ),
    # --- Video VAE (bat buoc) ---
    (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors",
        f"{COMFYUI_ROOT}/models/vae/minimax_h3_video_vae_fp16.safetensors",
    ),
    # --- Audio VAE (bat buoc --- de sinh audio native) ---
    (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors",
        f"{COMFYUI_ROOT}/models/vae/minimax_h3_audio_vae_fp32.safetensors",
    ),
    # --- Lightning LoRA 4-step (tuy chon --- render nhanh hon ~5x) ---
    (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        f"{COMFYUI_ROOT}/models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
    ),
]


def download_models(models):
    """Tai ve cac model con thieu, ho tro aria2c de tang toc gap 5-10 lan."""
    has_aria2 = os.system("which aria2c > /dev/null 2>&1") == 0
    for url, dest in models:
        if os.path.exists(dest) and os.path.getsize(dest) > 1024 * 1024 * 50:
            size_mb = os.path.getsize(dest) / 1024 / 1024
            print(f"✅ Da co san ({size_mb:.0f} MB): {os.path.basename(dest)}")
            continue
        dest_dir = os.path.dirname(dest)
        dest_name = os.path.basename(dest)
        os.makedirs(dest_dir, exist_ok=True)
        print(f"⬇️  Dang tai: {dest_name} ...")
        if has_aria2:
            cmd = f'aria2c -c -x 16 -s 16 -k 1M -d "{dest_dir}" -o "{dest_name}" "{url}"'
        else:
            cmd = f'wget -q --show-progress -c "{url}" -O "{dest}"'
        exit_code = os.system(cmd)
        if exit_code == 0 and os.path.exists(dest):
            size_mb = os.path.getsize(dest) / 1024 / 1024
            print(f"✅ Xong ({size_mb:.0f} MB): {dest_name}")
        else:
            print(f"❌ Loi khi tai: {dest_name}")


def setup_comfyui(target_dir="/content/ComfyUI"):
    """Cài đặt mã nguồn ComfyUI an toàn kể cả khi thư mục /content/ComfyUI đã chứa models."""
    main_py = os.path.join(target_dir, "main.py")
    if os.path.exists(main_py):
        return True

    print("🔄 Đang thiết lập mã nguồn ComfyUI vào /content/ComfyUI...")
    if not os.path.exists(target_dir):
        os.system(f"git clone https://github.com/comfyanonymous/ComfyUI {target_dir}")
    else:
        # Thư mục /content/ComfyUI đã tồn tại (do tạo folder models trước),
        # git clone trực tiếp sẽ lỗi 'destination path already exists and is not an empty directory'.
        # Giải pháp: clone vào temp rồi copy toàn bộ code sang mà không làm mất models đã tải.
        temp_dir = "/content/temp_comfyui"
        os.system(f"rm -rf {temp_dir}")
        os.system(f"git clone https://github.com/comfyanonymous/ComfyUI {temp_dir}")
        if os.path.exists(temp_dir):
            os.system(f"cp -rn {temp_dir}/* {target_dir}/ 2>/dev/null || true")
            os.system(f"cp -rn {temp_dir}/.* {target_dir}/ 2>/dev/null || true")
            os.system(f"rm -rf {temp_dir}")

    req_path = os.path.join(target_dir, "requirements.txt")
    if os.path.exists(req_path):
        os.system(f"pip install -q -r {req_path}")

    return os.path.exists(main_py)


print("=" * 60)
print("  MiniMax H3 --- Cài Đặt Môi Trường & Tải Model (Cell 1/2)")
print("=" * 60)

# Cài aria2 để tải model nhanh gấp 5-10 lần
os.system("apt-get -y install -qq aria2 > /dev/null 2>&1 || true")

# 1. Đảm bảo mã nguồn ComfyUI đã sẵn sàng
setup_comfyui(COMFYUI_ROOT)

# 2. Cài đặt các thư viện cần thiết cho MiniMax H3 và Gradio
print("📦 Đang kiểm tra & cài đặt thư viện cần thiết...")
os.system("pip install -q uv")
os.system("uv pip install -q --system gradio opencv-python accelerate diffusers einops sentencepiece av spandrel aiohttp || pip install -q gradio opencv-python accelerate diffusers einops sentencepiece av spandrel aiohttp")

# 3. Tải toàn bộ model MiniMax H3
download_models(MINIMAX_MODELS)
print("\n🎉 HOÀN TẤT CELL 1! Tất cả mã nguồn & model MiniMax H3 đã sẵn sàng.")
print("   👉 Bây giờ bạn hãy chạy tiếp CELL 2 bên dưới để mở giao diện.")


# ==========================================================================
# PHAN 2: TAO VIDEO TU ANH THAM KHAO (MiniMax H3 ref2va)
# ==========================================================================
# @title [Cell Phan 2] MiniMax H3 --- Tao Video Tu Anh Tham Khao
#
# Workflow tuong ung: workflow.json (MiniMaxH3ReferenceToVideo)
#
# Pipeline node:
#   UNETLoader                -> minimax_h3_ref2va_pruned_int8_convrot.safetensors
#   CLIPLoader                -> qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors (type=minimax)
#   VAELoader (video)         -> minimax_h3_video_vae_fp16.safetensors
#   VAELoader (audio)         -> minimax_h3_audio_vae_fp32.safetensors
#   LoraLoaderModelOnly       -> minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors
#   ComfySwitchNode (model)   -> bat/tat LoRA
#   ComfySwitchNode (steps)   -> chon so buoc full vs turbo
#   MiniMaxH3ReferenceToVideo -> conditioning + latent (node chinh)
#   BasicGuider               -> guider
#   KSamplerSelect            -> res_multistep
#   BasicScheduler            -> beta/normal/simple
#   SamplerCustomAdvanced     -> sampling
#   VAEDecode                 -> giai ma video frames
#   VAEDecodeAudio            -> giai ma audio
#   CreateVideo               -> mux video + audio -> VIDEO
#   SaveVideo                 -> ghi file mp4

get_ipython().system("pip install -q gradio opencv-python")

import glob
import json
import os
import random
import re
import shutil
import socket
import subprocess
import time
import urllib.request

import gradio as gr

# ------------------------------------------------------------------
# CAU HINH
# ------------------------------------------------------------------
INPUT_DIR  = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"

# Ten file model MiniMax H3
UNET_FILENAME       = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
CLIP_FILENAME       = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
VIDEO_VAE_FILENAME  = "minimax_h3_video_vae_fp16.safetensors"
AUDIO_VAE_FILENAME  = "minimax_h3_audio_vae_fp32.safetensors"
TURBO_LORA_FILENAME = "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"

# ------------------------------------------------------------------
# SERVER HELPERS
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# SERVER HELPERS
# ------------------------------------------------------------------
_SERVER_STATE = {"running_low_vram": None, "custom_nodes_mtime": None}
COMFYUI_DIR = "/content/ComfyUI"
COMFYUI_LOG_PATH = "/content/comfyui.log"


def is_server_running(port=8188):
    """Kiểm tra server qua cả HTTP API và socket."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/system_stats")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def _get_custom_nodes_mtime():
    cn_dir = os.path.join(COMFYUI_DIR, "custom_nodes")
    try:
        mtimes = []
        for entry in os.scandir(cn_dir):
            mtimes.append(entry.stat().st_mtime)
            if entry.is_dir():
                try:
                    for sub in os.scandir(entry.path):
                        if sub.name.endswith(".py"):
                            mtimes.append(sub.stat().st_mtime)
                except OSError:
                    pass
        return max(mtimes) if mtimes else 0.0
    except OSError:
        return 0.0


def ensure_server(low_vram, boot_timeout=120):
    """Đảm bảo ComfyUI server đang chạy với khả năng bắt lỗi tức thì qua log."""
    main_py = os.path.join(COMFYUI_DIR, "main.py")

    # 1. Kiểm tra ComfyUI đã được cài đặt chưa
    if not os.path.exists(main_py):
        print("⚠️ Chưa tìm thấy /content/ComfyUI/main.py! Đang thiết lập ComfyUI...")
        setup_comfyui(COMFYUI_DIR)
        if not os.path.exists(main_py):
            raise RuntimeError(
                "❌ Không tìm thấy file /content/ComfyUI/main.py!\n"
                "Thư mục /content/ComfyUI đã tồn tại sẵn nên không thể git clone trực tiếp.\n"
                "Hãy chạy lệnh sau trong 1 ô Code riêng trên Colab để giải quyết:\n"
                "!git clone https://github.com/comfyanonymous/ComfyUI /content/temp_comfyui && cp -rn /content/temp_comfyui/* /content/ComfyUI/ && rm -rf /content/temp_comfyui\n"
                "!pip install -r /content/ComfyUI/requirements.txt"
            )

    current_mtime = _get_custom_nodes_mtime()

    # 2. Nếu server đã chạy sẵn và không cần đổi low_vram -> giữ nguyên
    if is_server_running():
        if _SERVER_STATE["running_low_vram"] is None or (
            _SERVER_STATE["running_low_vram"] == low_vram
            and _SERVER_STATE["custom_nodes_mtime"] == current_mtime
        ):
            _SERVER_STATE["running_low_vram"] = low_vram
            _SERVER_STATE["custom_nodes_mtime"] = current_mtime
            return

    # 3. Tắt tiến trình cũ triệt để trước khi khởi động lại
    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    time.sleep(2)

    # 4. Thiết lập biến môi trường và file log
    os.chdir(COMFYUI_DIR)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    log_out = open(COMFYUI_LOG_PATH, "w", encoding="utf-8", errors="ignore")

    cmd = ["python", "-u", "main.py", "--listen", "127.0.0.1", "--port", "8188"]
    if low_vram:
        cmd.append("--lowvram")

    # 5. Khởi động ComfyUI
    proc = subprocess.Popen(
        cmd,
        cwd=COMFYUI_DIR,
        stdout=log_out,
        stderr=subprocess.STDOUT,
    )

    waited = 0
    poll_interval = 2
    while not is_server_running():
        time.sleep(poll_interval)
        waited += poll_interval

        # 🚨 BẮT LỖI NGAY NẾU TIẾN TRÌNH CRASH (không bắt người dùng đợi 300s!)
        ret = proc.poll()
        if ret is not None:
            log_out.flush()
            log_out.close()
            tail_lines = ""
            try:
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    tail_lines = "".join(f.readlines()[-35:])
            except Exception:
                tail_lines = "Không đọc được file log."
            raise RuntimeError(
                f"❌ ComfyUI crash ngay khi khởi động (Exit code: {ret})!\n"
                f"Chi tiết nguyên nhân từ log:\n"
                f"--------------------------------------------------\n"
                f"{tail_lines}\n"
                f"--------------------------------------------------"
            )

        if waited > boot_timeout:
            log_out.flush()
            log_out.close()
            tail_lines = ""
            try:
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    tail_lines = "".join(f.readlines()[-35:])
            except Exception:
                tail_lines = "Không đọc được file log."
            raise RuntimeError(
                f"❌ Server không phản hồi sau {boot_timeout}s!\n"
                f"Chi tiết log (/content/comfyui.log):\n"
                f"--------------------------------------------------\n"
                f"{tail_lines}\n"
                f"--------------------------------------------------"
            )

    _SERVER_STATE["running_low_vram"] = low_vram
    _SERVER_STATE["custom_nodes_mtime"] = current_mtime


def force_restart_server():
    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    time.sleep(2)
    _SERVER_STATE["running_low_vram"] = None
    _SERVER_STATE["custom_nodes_mtime"] = None
    return "🟢 Server đã tắt. Lần tạo video tiếp theo sẽ tự khởi động lại."


def read_server_log():
    """Đọc 40 dòng log mới nhất của ComfyUI server."""
    if not os.path.exists(COMFYUI_LOG_PATH):
        return "ℹ️ Chưa có file log (Server chưa từng khởi động)."
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-40:]) if lines else "ℹ️ Log rỗng."
    except Exception as e:
        return f"⚠️ Lỗi đọc log: {e}"


# ------------------------------------------------------------------
# TIEN ICH
# ------------------------------------------------------------------
def get_seed(v_seed):
    try:
        v = int(v_seed)
    except Exception:
        v = -1
    return random.randint(1, 999_999_999) if v == -1 else v


def free_comfyui_memory():
    """Hủy bỏ job đang chạy dở và giải phóng sạch sẽ GPU VRAM và System RAM."""
    # 1. Gửi lệnh ngắt tiến trình render ngay lập tức
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/interrupt",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

    # 2. Xóa sạch hàng đợi
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/queue",
            data=json.dumps({"clear": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

    # 3. Yêu cầu ComfyUI unload model khỏi VRAM và dọn cache
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

    # 4. Thu hồi bộ nhớ PyTorch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass
    return "🟢 Đã hủy job và giải phóng toàn bộ GPU VRAM & System RAM thành công!"


def get_comfyui_progress_line():
    """Trích xuất dòng tiến độ sampling gần nhất từ comfyui.log."""
    if not os.path.exists(COMFYUI_LOG_PATH):
        return ""
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for l in reversed(lines[-20:]):
            l_str = l.strip()
            if "%" in l_str or "it/s" in l_str or "s/it" in l_str:
                clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', l_str)
                return clean[:100]
            if "Executing node" in l_str:
                clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', l_str)
                return clean[:100]
    except Exception:
        pass
    return ""


def parse_resolution(ratio_str):
    """Chuyen chuoi ti le -> (width, height). Tối ưu 864x480 cho Colab."""
    if "864x480" in ratio_str:  return 864,  480
    if "480x864" in ratio_str:  return 480,  864
    if "1344x768" in ratio_str: return 1344, 768
    if "768x1344" in ratio_str: return 768,  1344
    if "1056x1056" in ratio_str: return 1056, 1056
    return 864, 480


def submit_and_wait_gen(workflow, scene_label="", max_wait_seconds=1800, poll_interval=3):
    """Generator theo dõi tiến độ thời gian thực và tự động giải phóng VRAM khi xong/lỗi."""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req  = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        response  = urllib.request.urlopen(req, timeout=30)
        prompt_id = json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        free_comfyui_memory()
        raise RuntimeError(f"ComfyUI từ chối workflow: {body[:800]}")
    except Exception as e:
        free_comfyui_memory()
        raise RuntimeError(f"Lỗi gửi job API: {e}")

    waited = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 15

    while waited < max_wait_seconds:
        try:
            history = json.loads(urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}"),
                timeout=30).read())
            consecutive_errors = 0
            if str(prompt_id) in history:
                yield True, prompt_id, "Hoàn tất"
                return

            queue = json.loads(urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8188/queue"), timeout=30).read())
            is_running = any(
                str(job[1]) == str(prompt_id)
                for job in queue.get("queue_running", []) + queue.get("queue_pending", [])
            )
            if not is_running:
                free_comfyui_memory()
                raise RuntimeError(f"Render thất bại ở {scene_label}")

            p_line = get_comfyui_progress_line()
            elapsed_m = waited // 60
            elapsed_s = waited % 60
            prog_text = f"[{elapsed_m:02d}m{elapsed_s:02d}s] {p_line}" if p_line else f"[{elapsed_m:02d}m{elapsed_s:02d}s] Đang tính toán sampling..."
            yield False, prompt_id, prog_text

        except RuntimeError:
            free_comfyui_memory()
            raise
        except Exception:
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                free_comfyui_memory()
                raise RuntimeError(
                    f"Server không phản hồi sau {consecutive_errors * poll_interval}s "
                    f"liên tiếp ở {scene_label}!"
                )

        time.sleep(poll_interval)
        waited += poll_interval

    # HỦY VÀ GIẢI PHÓNG VRAM NGAY KHI TIMEOUT!
    free_comfyui_memory()
    raise RuntimeError(
        f"Timeout: {scene_label} quá {max_wait_seconds // 60} phút!\n"
        f"🟢 Đã tự động hủy job và giải phóng GPU VRAM / System RAM.\n"
        f"💡 KHUYÊN DÙNG: Bật '⚡ Dùng Lightning LoRA (4 steps)' và chọn độ phân giải '864x480' để render chỉ mất 2-4 phút/cảnh!"
    )


# ------------------------------------------------------------------
# BUILD WORKFLOW  (MiniMax H3 ref2va --- theo workflow.json)
# ------------------------------------------------------------------
def build_minimax_workflow(
    *,
    prompt,
    width=1344,
    height=768,
    duration_s=5.0,
    fps=24,
    seed=None,
    scheduler="beta",
    steps_full=20,
    steps_turbo=4,
    use_turbo_lora=False,
    ref_image_size="match",
    pic1_name=None,
    pic2_name=None,
    pic3_name=None,
):
    """Xay dung ComfyUI API workflow cho MiniMax H3 ref2va.

    Tuong ung voi cac node trong workflow.json:
      - UNETLoader (id 127)                -> diffusion model
      - CLIPLoader (id 128)                -> text encoder (type=minimax)
      - VAELoader video (id 119)           -> video VAE
      - VAELoader audio (id 120)           -> audio VAE
      - LoraLoaderModelOnly (id 145)       -> turbo LoRA (tuy chon)
      - ComfySwitchNode model (id 141)     -> bat/tat LoRA
      - ComfySwitchNode steps (id 142)     -> chon steps full vs turbo
      - MiniMaxH3ReferenceToVideo (id 136) -> conditioning + latent (node chinh)
      - BasicGuider (id 126)               -> guider
      - KSamplerSelect (id 123)            -> res_multistep
      - BasicScheduler (id 124)            -> beta/normal/simple
      - SamplerCustomAdvanced (id 125)     -> sampling
      - VAEDecode (id 122)                 -> giai ma video frames
      - VAEDecodeAudio (id 121)            -> giai ma audio
      - CreateVideo (id 130)               -> mux video + audio
      - SaveVideo (id 92)                  -> ghi file mp4
    """
    if seed is None:
        seed = random.randint(1, 999_999_999)

    length = duration_to_length(duration_s, fps)

    wf = {
        # Loaders
        "unet": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"},
        },
        "clip": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": CLIP_FILENAME,
                "type": "minimax",
                "device": "default",
            },
        },
        "video_vae": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VIDEO_VAE_FILENAME},
        },
        "audio_vae": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": AUDIO_VAE_FILENAME},
        },
        # Lightning LoRA (tuy chon)
        "turbo_lora": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["unet", 0],
                "lora_name": TURBO_LORA_FILENAME,
                "strength_model": 1.0,
            },
        },
        # Switch: dung LoRA hay khong (ComfySwitchNode id 141)
        "model_switch": {
            "class_type": "ComfySwitchNode",
            "inputs": {
                "on_false": ["unet", 0],
                "on_true":  ["turbo_lora", 0],
                "switch":   bool(use_turbo_lora),
            },
        },
        # Switch: so steps full hay turbo (ComfySwitchNode id 142)
        "steps_full_node":  {"class_type": "PrimitiveInt", "inputs": {"value": steps_full}},
        "steps_turbo_node": {"class_type": "PrimitiveInt", "inputs": {"value": steps_turbo}},
        "steps_switch": {
            "class_type": "ComfySwitchNode",
            "inputs": {
                "on_false": ["steps_full_node", 0],
                "on_true":  ["steps_turbo_node", 0],
                "switch":   bool(use_turbo_lora),
            },
        },
        # Noise (RandomNoise id 129)
        "noise": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": int(seed)},
        },
        # MiniMaxH3ReferenceToVideo (node chinh, id 136)
        # Prompt dung tag <Picture 1>, <Picture 2>, <Picture 3>
        # de tham chieu anh theo dung thu tu slot ref_image_0/1/2
        "ref2va": {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {
                "clip":           ["clip", 0],
                "vae":            ["video_vae", 0],
                "audio_vae":      ["audio_vae", 0],
                "prompt":         prompt,
                "width":          int(width),
                "height":         int(height),
                "length":         int(length),
                "ref_image_size": ref_image_size,
            },
        },
        # Sampler chain
        "sampler_sel": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "res_multistep"},
        },
        "scheduler_node": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model":     ["model_switch", 0],
                "scheduler": scheduler,
                "steps":     ["steps_switch", 0],
                "denoise":   1.0,
            },
        },
        "guider": {
            "class_type": "BasicGuider",
            "inputs": {
                "model":        ["model_switch", 0],
                "conditioning": ["ref2va", 0],
            },
        },
        "sampler": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise":        ["noise", 0],
                "guider":       ["guider", 0],
                "sampler":      ["sampler_sel", 0],
                "sigmas":       ["scheduler_node", 0],
                "latent_image": ["ref2va", 1],
            },
        },
        # Decode
        "vae_decode": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["sampler", 0],
                "vae":     ["video_vae", 0],
            },
        },
        "audio_decode": {
            "class_type": "VAEDecodeAudio",
            "inputs": {
                "samples": ["sampler", 0],
                "vae":     ["audio_vae", 0],
            },
        },
        # CreateVideo + SaveVideo
        "create_video": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["vae_decode", 0],
                "audio":  ["audio_decode", 0],
                "fps":    fps,
            },
        },
        "save_video": {
            "class_type": "SaveVideo",
            "inputs": {
                "video":           ["create_video", 0],
                "filename_prefix": "video/MiniMax_H3",
                "format":          "auto",
                "codec":           "auto",
            },
        },
    }

    # Them anh tham khao vao ref2va
    ref_slots = [
        ("ref_images.ref_image_0", pic1_name),
        ("ref_images.ref_image_1", pic2_name),
        ("ref_images.ref_image_2", pic3_name),
    ]
    for slot_key, img_name in ref_slots:
        if img_name:
            node_id = f"load_{slot_key.split('.')[-1]}"
            wf[node_id] = {
                "class_type": "LoadImage",
                "inputs": {"image": img_name},
            }
            wf["ref2va"]["inputs"][slot_key] = [node_id, 0]

    return wf


# ------------------------------------------------------------------
# GENERATE --- HAM GRADIO GENERATOR
# ------------------------------------------------------------------
def generate_minimax_gradio(
    pic1_path, pic2_path, pic3_path,
    prompt_main,
    aspect_ratio, duration_s, fps, seed_val, num_segments, fixed_seed,
    scheduler, use_turbo_lora, ref_image_size,
    low_vram,
):
    if not pic1_path:
        yield None, None, "⚠️ Vui long tai it nhat anh Pic 1 (bat buoc)!"; return

    prompts = split_prompts(prompt_main)
    if not prompts:
        yield None, None, "⚠️ Vui long nhap it nhat 1 prompt!"; return

    width, height = parse_resolution(aspect_ratio)

    yield None, None, "🔄 Dang kiem tra / khoi dong ComfyUI server..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, None, f"❌ {e}"; return

    base_seed = get_seed(seed_val)
    os.makedirs(INPUT_DIR, exist_ok=True)

    def _copy_img(path, slot_name):
        if not path:
            return None
        ext  = os.path.splitext(path)[1].lower() or ".png"
        name = f"minimax_{slot_name}_{int(time.time())}{ext}"
        shutil.copy(path, os.path.join(INPUT_DIR, name))
        return name

    pic1_name = _copy_img(pic1_path, "pic1")
    pic2_name = _copy_img(pic2_path, "pic2")
    pic3_name = _copy_img(pic3_path, "pic3")

    loaded = [s for s in [pic1_name, pic2_name, pic3_name] if s]

    # Quyet dinh danh sach phan canh
    if len(prompts) > 1:
        scene_prompts = prompts
    else:
        num_segments  = max(1, int(num_segments))
        scene_prompts = [prompts[0]] * num_segments

    total_scenes  = len(scene_prompts)
    total_seconds = total_scenes * float(duration_s)
    mode_note     = "Turbo LoRA 4-step" if use_turbo_lora else "Full 20-step"

    yield None, None, (
        f"✅ Server san sang. Bat dau render {total_scenes} phan canh "
        f"(tong ~{total_seconds:.0f}s)...\n"
        f"📸 Anh tham khao: {len(loaded)} slot · Che do: {mode_note} · "
        f"Seed: {base_seed} · Scheduler: {scheduler}"
    )

    generated_videos = []
    for i, p in enumerate(scene_prompts):
        label  = f"phan canh {i + 1}/{total_scenes}"
        seed_i = base_seed if fixed_seed else (base_seed + i)

        yield generated_videos, None, (
            f"🔄 Dang render {label} [{mode_note}]... (Seed: {seed_i})\n"
            f"📝 Noi dung: {p[:120]}..."
        )

        wf = build_minimax_workflow(
            prompt         = p,
            width          = width,
            height         = height,
            duration_s     = float(duration_s),
            fps            = int(fps),
            seed           = seed_i,
            scheduler      = scheduler,
            use_turbo_lora = bool(use_turbo_lora),
            ref_image_size = ref_image_size,
            pic1_name      = pic1_name,
            pic2_name      = pic2_name,
            pic3_name      = pic3_name,
        )

        # Timeout động: Nếu dùng 4-step Turbo thì tối đa 15 phút (thường chạy 2-4 phút), nếu 20-step thì cho phép tới 45 phút!
        if use_turbo_lora:
            scene_timeout = max(900, int(duration_s) * 150)
        else:
            scene_timeout = max(2700, int(duration_s) * 400)

        try:
            for is_done, p_id, prog_msg in submit_and_wait_gen(wf, scene_label=label, max_wait_seconds=scene_timeout):
                if not is_done:
                    yield generated_videos, None, (
                        f"🔄 Đang render {label} [{mode_note}]... (Seed: {seed_i})\n"
                        f"⏳ Tiến độ: {prog_msg}\n"
                        f"📝 Nội dung: {p[:120]}..."
                    )
                else:
                    break
        except RuntimeError as e:
            free_comfyui_memory()
            yield generated_videos, None, f"❌ {e}"; return

        latest_video = find_latest_video()
        if not latest_video:
            yield generated_videos, None, f"⚠️ Khong tim thay file video o {label}!"; return

        generated_videos.append(latest_video)
        yield generated_videos, None, f"🔔 [DING] ✅ Xong {label} ({i + 1}/{total_scenes})!"

    # Ghep noi neu nhieu canh
    if len(generated_videos) > 1:
        yield generated_videos, None, "🔄 Dang ghep noi cac phan canh bang ffmpeg..."
        try:
            final_output = concat_videos(generated_videos, "final_minimax_video")
        except Exception as e:
            yield generated_videos, generated_videos[-1], f"⚠️ {e}"; return
        yield generated_videos, final_output, (
            f"🔔 [DING] 🎉 Hoan tat! "
            f"({total_seconds:.0f}s, {total_scenes} canh) · Seed: {base_seed}"
        )
    elif len(generated_videos) == 1:
        yield generated_videos, generated_videos[0], (
            f"🔔 [DING] 🎉 Render xong! ({duration_s}s) · Seed: {base_seed}"
        )


# ------------------------------------------------------------------
# GRADIO UI
# ------------------------------------------------------------------
ratio_choices = [
    "16:9 (864x480) ⭐ Khuyên dùng trên Colab (Nhanh x3, nhẹ VRAM)",
    "9:16 (480x864) ⭐ Khuyên dùng (Khung dọc TikTok/Reels)",
    "16:9 (1344x768) (HD 720p - Chậm, cần >25 phút/cảnh)",
    "9:16 (768x1344) (HD 720p dọc - Chậm, cần >25 phút/cảnh)",
    "1:1  (1056x1056) (Vuông)",
]

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.gradio-container { font-family: 'Inter', sans-serif !important; max-width: 1560px; margin: 0 auto; }
#mm-header { background: linear-gradient(135deg, #0f4c81 0%, #1a73e8 100%);
             border-radius:16px; padding:20px 26px; margin-bottom:14px;
             box-shadow: 0 6px 20px rgba(15,76,129,.28); }
#mm-header h1, #mm-header p { color:#fff !important; margin:0 !important; }
.info-box { background:rgba(26,115,232,.08); border-left:3px solid #1a73e8;
            padding:10px 14px; border-radius:8px; font-size:.87rem; margin-bottom:8px; }
.scene-counter { display:inline-block; background:rgba(26,115,232,.12); padding:6px 14px;
                 border-radius:999px; font-weight:600 !important; font-size:0.85rem !important;
                 margin:2px 0 6px 0 !important; }
.scene-counter p { margin:0 !important; color:#1a73e8 !important; }
.status-box textarea { font-family:monospace !important; font-size:.82rem !important; }
"""

notification_js = """
function(){
    let last="";
    function ding(){
        try{
            let c=new(window.AudioContext||window.webkitAudioContext)();
            let o=c.createOscillator(),g=c.createGain();
            o.type='sine'; o.frequency.setValueAtTime(880,c.currentTime);
            o.frequency.exponentialRampToValueAtTime(1760,c.currentTime+.15);
            g.gain.setValueAtTime(.3,c.currentTime);
            g.gain.exponentialRampToValueAtTime(.01,c.currentTime+.4);
            o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+.4);
        }catch(e){}
    }
    new MutationObserver(()=>{
        document.querySelectorAll('.status-box textarea').forEach(tb=>{
            let t=tb.value||"";
            if(t.includes('[DING]')&&t!==last){last=t;ding();}
        });
    }).observe(document.body,{childList:true,subtree:true,characterData:true});
}
"""

with gr.Blocks(
    title="MiniMax H3 Studio",
    fill_width=True,
) as demo:

    with gr.Column(elem_id="mm-header"):
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown(
                    """
                    # 🎬 MiniMax H3 Studio --- Reference-to-Video
                    Tao video voi native stereo audio tu anh tham khao
                    Len den 2K * 24fps * ~15 giay/clip

                    <div style="margin-top:4px; opacity:0.9; font-size:0.9rem;">
                    MiniMax H3 * Toi da 3 anh tham khao * Audio sinh native *
                    Ghep noi chuoi canh tu dong
                    </div>
                    """
                )
            with gr.Column(scale=1, min_width=160):
                restart_btn = gr.Button("🔄 Restart Server", size="sm")
                free_btn = gr.Button("🧹 Giải Phóng VRAM", size="sm")
                log_btn = gr.Button("📋 Xem Log Server", size="sm")
                restart_out = gr.Markdown("🟢 San sang")
        restart_btn.click(fn=force_restart_server, outputs=[restart_out])
        free_btn.click(fn=free_comfyui_memory, outputs=[restart_out])

    with gr.Row():
        # COT TRAI: INPUTS
        with gr.Column(scale=5):

            with gr.Group():
                gr.Markdown("### 📸 Anh tham khao")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Tai anh tham khao nhan vat / boi canh. Trong prompt, tham chieu bang "
                    "<code>&lt;Picture 1&gt;</code>, <code>&lt;Picture 2&gt;</code>, "
                    "<code>&lt;Picture 3&gt;</code> theo dung thu tu slot. "
                    "Chi <b>Pic 1</b> bat buoc."
                    "</div>"
                )
                with gr.Row():
                    mm_pic1 = gr.Image(
                        label="🎭 Pic 1 — Nhan vat / boi canh 1 (bat buoc)", type="filepath"
                    )
                    mm_pic2 = gr.Image(label="🎭 Pic 2 — Tuy chon", type="filepath")
                mm_pic3 = gr.Image(label="🎭 Pic 3 — Tuy chon", type="filepath")

            with gr.Group():
                gr.Markdown("### 📝 Prompt")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Dung tag <code>&lt;Picture 1&gt;</code>, <code>&lt;Picture 2&gt;</code> "
                    "de tham chieu anh. "
                    "Moi phan canh cach nhau <b>1 dong trong</b>. "
                    "MiniMax H3 sinh <b>audio native</b> --- mo ta am thanh / giong noi "
                    "truc tiep trong prompt."
                    "</div>"
                )
                scene_count_display = gr.Markdown(
                    "🔹 **So phan canh nhan dien duoc:** 0", elem_classes="scene-counter"
                )
                mm_prompt = gr.Textbox(
                    label="Prompt chinh (moi phan canh cach nhau 1 dong trong)",
                    lines=8,
                    placeholder=(
                        "Use <Picture 1> as the main character.\n\n"
                        "CUT 1: Close-up of <Picture 1> standing on a rooftop at night, "
                        "red cape billowing in the wind. He says 'Get ready to meet your maker!' "
                        "with dramatic echo reverb. City neon lights glitter below.\n\n"
                        "CUT 2: Wide hero shot --- <Picture 1> leaps off the edge toward camera, "
                        "a massive explosion erupts behind him, debris flying outward, "
                        "deep cinematic BOOM sound effect fills the air."
                    ),
                )

            with gr.Accordion("⚙️ Cai dat nang cao", open=False):
                gr.Markdown("**📐 Do phan giai & Thoi luong**")
                ratio_mm = gr.Radio(
                    label="Ti le khung hinh",
                    choices=ratio_choices,
                    value=ratio_choices[0],
                    info="1344x768 = 768p chinh thuc (~1 MP). Dung 864x480 de tiet kiem VRAM.",
                )
                with gr.Row():
                    duration_mm = gr.Slider(
                        label="⏱️ Thoi luong MOI canh (giay)",
                        minimum=2, maximum=15, step=1, value=5,
                        info="MiniMax H3 ho tro toi da ~15 giay/clip",
                    )
                    fps_mm = gr.Number(
                        label="🎞️ FPS (co dinh 24)",
                        value=24, precision=0, interactive=False,
                        info="MiniMax H3 co dinh 24 fps",
                    )

                with gr.Row():
                    seed_mm = gr.Number(
                        label="🎲 Seed (-1 = ngau nhien)", value=-1, precision=0
                    )
                    num_seg_mm = gr.Slider(
                        label="🔢 So phan doan (khi chi co 1 prompt)",
                        minimum=1, maximum=10, step=1, value=1,
                        info="Chi ap dung khi o prompt chi co 1 doan duy nhat",
                    )
                fixed_seed_mm = gr.Checkbox(
                    label="🔗 Dung chung 1 Seed cho moi phan canh", value=False
                )

                gr.Markdown("**🧬 Sampler & LoRA**")
                with gr.Row():
                    scheduler_mm = gr.Radio(
                        label="Scheduler",
                        choices=["beta", "normal", "simple"],
                        value="beta",
                        info="beta / normal thuong tot hon simple cho ref2va",
                    )
                    turbo_mm = gr.Checkbox(
                        label="⚡ Dùng Lightning LoRA (4 steps --- nhanh gấp 5 lần)",
                        value=True,
                        info="BẬT (Khuyên dùng): Chỉ ~2-4 phút/cảnh. TẮT (20 steps): Cần ~25-35 phút/cảnh.",
                    )
                ref_size_mm = gr.Radio(
                    label="ref_image_size",
                    choices=["match", "max"],
                    value="match",
                    info=(
                        "match = scale xuong res output, nhanh hon * "
                        "max = giu chi tiet anh tot hon (2048px), cham hon"
                    ),
                )

                gr.Markdown("**⚙️ Server**")
                low_vram_mm = gr.Checkbox(
                    label="🧊 Low VRAM Mode (--cache-none)", value=True
                )

        # COT PHAI: OUTPUTS
        with gr.Column(scale=5):
            with gr.Group():
                gallery_mm   = gr.Gallery(
                    label="🎥 Cac Phan Canh Le (Shot 1, Shot 2...)",
                    columns=2, height="auto",
                )
                video_out_mm = gr.Video(label="🎬 Video Hoan Chinh (Ghep Noi Lien Mach)")
                with gr.Row():
                    mm_btn   = gr.Button("🎬 Bat Dau Tao Video", variant="primary", scale=3)
                    mm_clear = gr.Button("🗑️ Clear", scale=1)
                mm_status = gr.Textbox(
                    label="ℹ️ Status / Tien trinh",
                    interactive=False,
                    lines=5,
                    elem_classes="status-box",
                )

            gr.Markdown(
                "<div class='info-box'>"
                "<b>💡 Meo dung MiniMax H3:</b><br>"
                "* Tham chieu anh bang <code>&lt;Picture 1&gt;</code>, "
                "<code>&lt;Picture 2&gt;</code> ngay trong prompt.<br>"
                "* Mo ta <b>am thanh / giong noi</b> truc tiep --- model sinh audio native.<br>"
                "* Dung <b>Turbo LoRA 4-step</b> de xem thu truoc, sau do tat de "
                "render full 20-step.<br>"
                "* <b>ref_image_size = max</b> giu nhan vat ro net hon nhung cham hon.<br>"
                "* Moi canh cach nhau 1 dong trong --- he thong tu render tung canh "
                "roi ghep noi thanh phim hoan chinh."
                "</div>"
            )

    mm_prompt.change(fn=count_scenes, inputs=[mm_prompt], outputs=[scene_count_display])

    mm_btn.click(
        fn=generate_minimax_gradio,
        inputs=[
            mm_pic1, mm_pic2, mm_pic3,
            mm_prompt,
            ratio_mm, duration_mm, fps_mm, seed_mm, num_seg_mm, fixed_seed_mm,
            scheduler_mm, turbo_mm, ref_size_mm,
            low_vram_mm,
        ],
        outputs=[gallery_mm, video_out_mm, mm_status],
    )
    def on_clear():
        free_comfyui_memory()
        return None, None, "🟢 Đã dọn dẹp hàng đợi và giải phóng GPU VRAM / System RAM!", "🔹 **Số phân cảnh nhận diện được:** 0"

    mm_clear.click(
        fn=on_clear,
        outputs=[gallery_mm, video_out_mm, mm_status, scene_count_display],
    )
    log_btn.click(fn=read_server_log, outputs=[mm_status])

print("🔄 Đang khởi động ComfyUI server trước khi mở giao diện...")
try:
    ensure_server(low_vram=True)
    print("🟢 ComfyUI server đã sẵn sàng hoạt động!")
except Exception as e:
    print(f"⚠️ {e}")

demo.queue()
demo.launch(
    share=True,
    inline=False,
    debug=True,
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo", neutral_hue="slate"),
    css=custom_css,
    js=notification_js,
)
