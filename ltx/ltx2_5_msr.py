#@title 🎬 Cell 2: LTX-2.5 Studio — Multi-Subject Reference, Ingredients & Cinema I2V — UPGRADED
# ==============================================================================
# Cell 2: Giao diện Gradio Live tạo video chất lượng điện ảnh với Lightricks LTX-2.5.
# Hỗ trợ 3 chế độ quay phim hàng đầu:
#  1. 🎭 MSR 2-Stage (Multi-Subject Reference: tới 4 nhân vật + bối cảnh + Start Frame)
#  2. 🧪 Ingredients IC-LoRA (Bám nhân vật/đạo cụ theo Reference Sheet chính thức)
#  3. 🎥 Cinema Two-Stage I2V/T2V (Tạo cảnh phim chuẩn nét cao x2 Spatial Upscaler)
#
# Yêu cầu: Cell 1 (download.py) đã chạy thành công trước đó.
# ==============================================================================

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

# ==============================================================================
# CẤU HÌNH HỆ THỐNG
# ==============================================================================
INPUT_DIR  = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"
COMFYUI_DIR = "/content/ComfyUI"
COMFYUI_LOG_PATH = "/content/comfyui.log"

UNET_FILENAME             = globals().get("UNET_FILENAME",             "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors")
TEXT_ENCODER_BF16_FILENAME = "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
TEXT_ENCODER_BF16_URL      = "https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
TEXT_ENCODER_INT8_FILENAME = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
TEXT_ENCODER_INT8_URL      = "https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
TEXT_ENCODER_FILENAME     = globals().get("TEXT_ENCODER_FILENAME",     TEXT_ENCODER_BF16_FILENAME)
VIDEO_VAE_FILENAME        = globals().get("VIDEO_VAE_FILENAME",        "ltx-2.5-video-vae-bf16.safetensors")
AUDIO_VAE_FILENAME        = globals().get("AUDIO_VAE_FILENAME",        "ltx-2.5-audio-vae-bf16.safetensors")
SPATIAL_UPSCALER_FILENAME = globals().get("SPATIAL_UPSCALER_FILENAME", "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors")
SPATIAL_UPSCALER_URL      = "https://huggingface.co/Lightricks/LTX-2.5/resolve/main/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"
MSR_LORA_FILENAME         = globals().get("MSR_LORA_FILENAME",         "ltx2.5/LTX-2.5-Licon-MSR-V1.safetensors")
INGREDIENTS_LORA_FILENAME = globals().get("INGREDIENTS_LORA_FILENAME", "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors")
DISTILLED_LORA_FILENAME   = globals().get("DISTILLED_LORA_FILENAME",   "ltx-2.5-22b-distilled-lora-450-bf16.safetensors")
DISTILLED_LORA_URL        = "https://huggingface.co/Lightricks/LTX-2.5/resolve/main/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors"
REFINE_DETAILS_LORA_FILENAME = globals().get("REFINE_DETAILS_LORA_FILENAME", "ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors")
REFINE_DETAILS_LORA_URL      = "https://huggingface.co/Lightricks/LTX-2.5-22b-IC-LoRA-Refine-Details/resolve/main/ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors"


LATENT_GROUP_FRAMES = 8

# Chuẩn Sigmas chính thức của LTX-2.5 Distilled (8 bước) và Refinement (4 bước)
SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.85, 0.7250, 0.4219, 0.0"

QUALITY_PREFIX = (
    "Cinematic 35mm film footage, soft diffused natural lighting, master cinematography, "
    "sharp organic focus, subtle film grain, authentic texture, "
)
QUALITY_SUFFIX = (
    ", lifelike skin texture, matte finish, smooth cinematic camera movement, highly detailed features, "
    "temporal consistency, synchronized natural sound and acoustics"
)

NEGATIVE_PROMPT_DEFAULT = (
    "oily skin, greasy skin, plastic skin, waxy skin, glossy surface, shiny forehead, "
    "specular reflection, specular bloom, overexposed, blown out highlights, oversharpened, "
    "split screen, collage, grid, multiple panels, photo frame, triple view, character sheet, "
    "lineup, side by side, border, letterbox, white bars, inset image, picture-in-picture, "
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, glitches, watermark, text, logo, subtitles, "
    "static frame, frozen image, lack of motion, deformed limbs, extra paws, duplicate limbs, "
    "distorted face, character switching, wrong character, inconsistent character identity, "
    "temporal inconsistency, jittery motion, flickering texture, strobing, bad anatomy"
)

# ==============================================================================
# HÀM QUẢN LÝ COMFYUI SERVER & GPU
# ==============================================================================
_SERVER_STATE = {"running_low_vram": None, "custom_nodes_mtime": None}


def is_server_running(port=8188):
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


def ensure_server(low_vram=True, boot_timeout=120):
    """Khởi động hoặc khôi phục ComfyUI server nếu chưa chạy."""
    ensure_lora_symlinks()
    current_mtime = _get_custom_nodes_mtime()
    if is_server_running():
        if (_SERVER_STATE["running_low_vram"] == low_vram and
            _SERVER_STATE["custom_nodes_mtime"] == current_mtime):
            return

    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    time.sleep(2)

    os.chdir(COMFYUI_DIR)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
        "expandable_segments:True,"
        "max_split_size_mb:512,"
        "garbage_collection_threshold:0.8"
    )
    log_out = open(COMFYUI_LOG_PATH, "w", encoding="utf-8", errors="ignore")

    cmd = ["python", "-u", "main.py", "--listen", "127.0.0.1", "--port", "8188", "--fast"]
    if low_vram:
        cmd += ["--lowvram", "--cache-none"]

    proc = subprocess.Popen(cmd, cwd=COMFYUI_DIR, stdout=log_out, stderr=subprocess.STDOUT)

    waited = 0
    while not is_server_running():
        time.sleep(2)
        waited += 2
        ret = proc.poll()
        if ret is not None:
            log_out.flush(); log_out.close()
            tail = ""
            try:
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    tail = "".join(f.readlines()[-35:])
            except Exception:
                tail = "Không đọc được log."
            raise RuntimeError(f"❌ ComfyUI crash khi khởi động (Exit: {ret}):\n{tail}")
        if waited > boot_timeout:
            log_out.flush(); log_out.close()
            raise RuntimeError(f"⏰ Server ComfyUI không phản hồi sau {boot_timeout}s!")

    _SERVER_STATE["running_low_vram"] = low_vram
    _SERVER_STATE["custom_nodes_mtime"] = current_mtime


def free_comfyui_memory():
    """Hủy queue hiện tại và giải phóng GPU VRAM."""
    for endpoint, payload in [
        ("interrupt", b"{}"),
        ("queue", json.dumps({"clear": True}).encode()),
        ("free", json.dumps({"unload_models": True, "free_memory": True}).encode()),
    ]:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:8188/{endpoint}", data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass
    return "🟢 Đã dọn dẹp hàng đợi và giải phóng GPU VRAM!"


def read_server_log():
    if not os.path.exists(COMFYUI_LOG_PATH):
        return "ℹ️ Chưa có file log."
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[-40:]) if lines else "ℹ️ Log rỗng."
    except Exception as e:
        return f"⚠️ Lỗi đọc log: {e}"


# ==============================================================================
# HÀM XỬ LÝ VIDEO & HẬU KỲ
# ==============================================================================
def snap_fps_safe(fps):
    try:
        fps = float(fps)
    except (TypeError, ValueError):
        fps = 24.0
    return 24.0 if abs(fps - 24.0) < 1.0 else max(8.0, round(fps))


def half_dims(width, height):
    def snap_half_up(v):
        return max(32, int(math.ceil(int(v) / 2.0 / 32.0)) * 32)
    return snap_half_up(width), snap_half_up(height)


def safe_dims(width, height):
    def snap_up(v):
        return max(256, int(math.ceil(int(v) / 32.0)) * 32)
    return snap_up(width), snap_up(height)


def parse_aspect_ratio(ratio_str):
    if "9:16" in ratio_str:
        return 720, 1280
    if "1:1" in ratio_str:
        return 720, 720
    if "832x480" in ratio_str:
        return 832, 480
    if "480x832" in ratio_str:
        return 480, 832
    if "1536x864" in ratio_str:
        return 1536, 864
    if "864x1536" in ratio_str:
        return 864, 1536
    return 1280, 720


def get_seed(v_seed):
    try:
        if v_seed is None:
            return 0
        s = int(v_seed)
        return s if s >= 0 else random.randint(1, 999_999_999)
    except (TypeError, ValueError):
        return 0


def apply_quality_wrapping(prompt, use_wrap=True):
    if not use_wrap or not prompt or not prompt.strip():
        return prompt
    p = prompt.strip()
    return f"{QUALITY_PREFIX}{p}{QUALITY_SUFFIX}"


def clean_visual_prompt_for_relay(prompt):
    """
    1. Cắt bỏ Audio / Sound / Voiceover / Lời thoại / Speech transcripts ra khỏi prompt thị giác.
    2. Chuyển đổi các cú máy 2 shot (vd: First 4 seconds ... At precisely 4 seconds ...) thành cú pháp nhịp 'Shot 1 | Shot 2' cho PromptRelayEncode.
    """
    if not prompt or not prompt.strip():
        return ""
    p = prompt.strip()

    # Cắt bỏ Audio / Voiceover / Lời thoại / Thuyết minh / 旁白 / 音频
    p = re.split(r"(?i)\b(?:Audio|Sound effects|SFX|Voiceover|Narration|Lời thoại|Thuyết minh)\s*[:：]|(?:旁白|音频|音效)\s*[:：]", p)[0].strip()

    # Xóa các chuỗi lời thoại còn sót: [00:00-00:04] "..."
    p = re.sub(r'\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\][^"\u201c\n]*["\u201c][^"\u201d]*["\u201d]', '', p).strip()

    # Nhận diện điểm chuyển cảnh (Giây thứ 4 hoặc giữa 2 shot)
    split_pattern = r"(?i)(?:[,\.，。\s]+)(?:At precisely (?:4 seconds|00:04)|At 4 seconds|Chuyển cảnh (?:tại |ở |\(|\:)?00:04\)?|后4秒[：:]?|第4秒[：:]?)[,\s:：]*"
    parts = re.split(split_pattern, p, maxsplit=1)

    if len(parts) == 2:
        shot1 = parts[0].strip()
        shot2 = parts[1].strip()
        shot1 = re.sub(r"(?i)\b(?:First 4 seconds|前4秒)\s*[:：]\s*", "", shot1).strip()
        return f"{shot1} | {shot2}"

    return p


def format_msr_actor_descriptions(text, active_slots=None):
    """
    Chuẩn hóa mô tả các Act & Background:
    - Mỗi mô tả cách nhau bằng 1 dòng trống (\\n\\n).
    - Tự động gắn nhãn Image 1:, Image 2:, Image 3:, Image 4:, Background: nếu chưa có.
    - Lọc chỉ giữ lại mô tả của các Act thực sự xuất hiện trong phân cảnh hiện tại.
    """
    if not text or not text.strip():
        return ""
    blocks = [b.strip() for b in re.split(r"\n[ \t]*\n+", text.strip()) if b.strip()]
    formatted = []
    default_tags = ["Image 1: ", "Image 2: ", "Image 3: ", "Image 4: ", "Background: "]
    slot_keys = ["pic1", "pic2", "pic3", "pic4", "bg"]

    for i, b in enumerate(blocks):
        slot_key = slot_keys[i] if i < len(slot_keys) else f"pic{i+1}"
        if active_slots and not active_slots.get(slot_key, True):
            continue
        if re.match(r"^(?:Image\s*\d+|Pic\s*\d+|Background|Act\s*\d+)[\s*:\-]", b, re.IGNORECASE):
            formatted.append(b)
        else:
            tag = default_tags[i] if i < len(default_tags) else f"Image {i+1}: "
            formatted.append(f"{tag}{b}")
    return "\n\n".join(formatted)


def detect_active_actors_for_scene(prompt, relay_desc=""):
    """
    Tự động nhận diện những Act nào xuất hiện trong phân cảnh để chỉ nạp slot ảnh đó.
    Ngăn chặn việc các nhân vật khác bị ép vào sai phân cảnh (vd: Cáo và Sói bị ép vào Cảnh 1).
    """
    p_lower = prompt.lower()
    patterns = {
        "pic1": [r"\bimage\s*1\b", r"\bpic\s*1\b", r"\bact\s*1\b", r"kuro", r"mèo", r"cat", r"lạc phong", r"strategist", r"tom cat", r"tomcat", r"feline", r"黑猫", r"骆峰"],
        "pic2": [r"\bimage\s*2\b", r"\bpic\s*2\b", r"\bact\s*2\b", r"aria", r"cáo", r"fox", r"hồ ly", r"nine-tailed", r"cửu vĩ", r"狐狸", r"阿莉亚", r"九尾"],
        "pic3": [r"\bimage\s*3\b", r"\bpic\s*3\b", r"\bact\s*3\b", r"fenris", r"sói", r"wolf", r"wolves", r"frost wolf", r"cự lang", r"狼", r"芬里斯"],
        "pic4": [r"\bimage\s*4\b", r"\bpic\s*4\b", r"\bact\s*4\b", r"balthazar", r"sư tử", r"lion", r"iron lion", r"magitech lion", r"巴尔萨泽", r"狮子"],
    }

    if relay_desc and relay_desc.strip():
        blocks = [b.strip() for b in re.split(r"\n[ \t]*\n+", relay_desc.strip()) if b.strip()]
        slot_keys = ["pic1", "pic2", "pic3", "pic4"]
        for i, b in enumerate(blocks[:4]):
            words = re.findall(r"[\w\u00C0-\u1EF9]+", b)
            keywords = [w.lower() for w in words if len(w) >= 4 and w.lower() not in ["image", "bối", "cảnh", "nhân", "vật"]]
            patterns[slot_keys[i]].extend([rf"\b{re.escape(k)}\b" for k in keywords[:5]])

    active = {}
    for slot, kws in patterns.items():
        active[slot] = any(re.search(kw, p_lower) for kw in kws)

    # Nếu không match slot nào, mặc định nạp Act 1 (nhân vật chính)
    if not any(active.values()):
        active["pic1"] = True
    active["bg"] = True
    return active


def is_reference_sheet_prompt(text):
    lower = text.lower()
    ref_kw = [
        "master reference sheet", "master model sheet", "character model sheet",
        "turnaround view", "3 turnaround views", "front view, three-quarter",
        "inset callout", "model sheet of", "nạp vào pic", "msr slot: pic",
        "角色设定图", "三视图", "主参考设定图", "三视角", "角色主模型表",
    ]
    if any(k in lower for k in ref_kw):
        if not any(k in lower for k in ["first 4 seconds", "at precisely", "chuyển cảnh", "前4秒", "00:00", "shot 1"]):
            return True
        if lower.startswith(("complete anime character", "anime character master", "动漫角色终极主参考设定图", "角色设定图")):
            return True
    return False


def split_prompts(text):
    """
    Tách các phân cảnh thông minh:
    - Tự động bỏ qua các đoạn Character Reference Sheet / Model Sheet (nếu người dùng copy nhầm cả mô tả tạo ảnh nhân vật).
    - Bỏ qua các vạch chia '---' hoặc '===' và bóc các khối ```text ... ```.
    - Loại bỏ tiêu đề phân cảnh (vd: '### Phân cảnh 1: ...') chỉ giữ lại prompt quay phim thực tế.
    - Làm sạch các tham số Midjourney như '--ar 16:9'.
    """
    if not text or not text.strip():
        return []
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    norm = re.sub(r"```[a-zA-Z0-9_-]*", "", norm)

    raw_blocks = re.split(r"\n[ \t]*\n+", norm.strip())
    all_cleaned = []
    video_prompts = []

    for b in raw_blocks:
        b = b.strip()
        if not b or re.match(r"^[-=*]{3,}$", b):
            continue

        lines = b.split("\n")
        if lines[0].strip().startswith(("#", "**Cảnh", "**Scene", "**Phân cảnh", "**Prompt", "**第")) and len(lines) > 1:
            rest = "\n".join(lines[1:]).strip()
            if len(rest) > 20:
                b = rest

        if b.startswith(("#", ">", "|", "Dùng các prompt", "Để đạt tính", "edge-tts", "Bạn có thể", "*")) or "edge-tts" in b:
            continue

        b_clean = re.sub(r"--(?:ar|v|stylize|s|weird|c|no)\s+[^\s]+", "", b).strip()
        if not b_clean:
            continue

        all_cleaned.append(b_clean)
        if not is_reference_sheet_prompt(b_clean):
            video_prompts.append(b_clean)

    return video_prompts if video_prompts else all_cleaned


def ensure_lora_symlinks():
    """Tự động đồng bộ LoRA giữa models/loras/ và models/loras/ltx2.5/ để ComfyUI nhận diện cả 2 vị trí."""
    try:
        lora_dir = os.path.join(COMFYUI_DIR, "models", "loras")
        sub_dir = os.path.join(lora_dir, "ltx2.5")
        os.makedirs(sub_dir, exist_ok=True)
        sync_files = [
            "LTX-2.5-Licon-MSR-V1.safetensors",
            "ltx-2.5-22b-distilled-lora-450-bf16.safetensors",
            "ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors",
        ]
        for f_name in sync_files:
            src_sub = os.path.join(sub_dir, f_name)
            dst_root = os.path.join(lora_dir, f_name)
            if os.path.exists(src_sub) and not os.path.exists(dst_root):
                try:
                    os.symlink(src_sub, dst_root)
                except Exception:
                    shutil.copy2(src_sub, dst_root)
            elif os.path.exists(dst_root) and not os.path.exists(src_sub):
                try:
                    os.symlink(dst_root, src_sub)
                except Exception:
                    shutil.copy2(dst_root, src_sub)
    except Exception:
        pass


def _get_hf_token():
    """Lấy HF_TOKEN từ biến môi trường hoặc Colab Secrets."""
    tok = os.environ.get("HF_TOKEN", "")
    if not tok:
        try:
            from google.colab import userdata
            tok = userdata.get("HF_TOKEN") or ""
        except Exception:
            pass
    return tok


def ensure_upscaler_symlinks():
    """Đồng bộ symlink giữa models/latent_upscale_models/ và models/upscale_models/."""
    try:
        lu_dir = os.path.join(COMFYUI_DIR, "models", "latent_upscale_models")
        u_dir = os.path.join(COMFYUI_DIR, "models", "upscale_models")
        os.makedirs(lu_dir, exist_ok=True)
        os.makedirs(u_dir, exist_ok=True)
        src = os.path.join(lu_dir, SPATIAL_UPSCALER_FILENAME)
        dst = os.path.join(u_dir, SPATIAL_UPSCALER_FILENAME)
        if os.path.exists(src) and not os.path.exists(dst):
            try: os.symlink(src, dst)
            except Exception: shutil.copy2(src, dst)
        elif os.path.exists(dst) and not os.path.exists(src):
            try: os.symlink(dst, src)
            except Exception: shutil.copy2(dst, src)
    except Exception:
        pass


def ensure_spatial_upscaler():
    """Tự động kiểm tra và tải Spatial Upscaler x2 (ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors) nếu chưa có."""
    upscale_dir = os.path.join(COMFYUI_DIR, "models", "latent_upscale_models")
    os.makedirs(upscale_dir, exist_ok=True)
    target = os.path.join(upscale_dir, SPATIAL_UPSCALER_FILENAME)
    if os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 5:
        ensure_upscaler_symlinks()
        return True

    hf_token = _get_hf_token()
    header = ["--header", f"Authorization: Bearer {hf_token}"] if hf_token else []
    cmd = [
        "aria2c", "--console-log-level=warn", "-c",
        "-x", "8", "-s", "8", "-k", "1M",
        "-d", upscale_dir, "-o", SPATIAL_UPSCALER_FILENAME,
    ] + header + [SPATIAL_UPSCALER_URL]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        pass

    if not (os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 5):
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="Lightricks/LTX-2.5",
                filename=f"latent_upscale_models/{SPATIAL_UPSCALER_FILENAME}",
                local_dir=upscale_dir,
                token=hf_token or None,
            )
            downloaded = os.path.join(upscale_dir, "latent_upscale_models", SPATIAL_UPSCALER_FILENAME)
            if os.path.exists(downloaded) and not os.path.exists(target):
                shutil.move(downloaded, target)
        except Exception:
            try:
                import urllib.request
                req = urllib.request.Request(SPATIAL_UPSCALER_URL, headers={"User-Agent": "Mozilla/5.0"})
                if hf_token:
                    req.add_header("Authorization", f"Bearer {hf_token}")
                with urllib.request.urlopen(req, timeout=120) as resp, open(target, "wb") as f:
                    shutil.copyfileobj(resp, f)
            except Exception:
                pass

    ensure_upscaler_symlinks()
    ok = os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 5
    if not ok:
        print("⚠️ Chú ý: Chưa tải được Spatial Upscaler x2. Vui lòng cấp quyền HuggingFace token!")
    return ok


def ensure_distilled_lora():
    """Tự động tải ltx-2.5-22b-distilled-lora-450-bf16.safetensors nếu chưa có."""
    lora_dir = os.path.join(COMFYUI_DIR, "models", "loras")
    os.makedirs(lora_dir, exist_ok=True)
    target = os.path.join(lora_dir, DISTILLED_LORA_FILENAME)
    if os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10:
        return True

    hf_token = _get_hf_token()
    header = ["--header", f"Authorization: Bearer {hf_token}"] if hf_token else []
    cmd = [
        "aria2c", "--console-log-level=warn", "-c",
        "-x", "8", "-s", "8", "-k", "1M",
        "-d", lora_dir, "-o", DISTILLED_LORA_FILENAME,
    ] + header + [DISTILLED_LORA_URL]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        pass

    if not (os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10):
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="Lightricks/LTX-2.5",
                filename=f"loras/{DISTILLED_LORA_FILENAME}",
                local_dir=lora_dir,
                token=hf_token or None,
            )
            downloaded = os.path.join(lora_dir, "loras", DISTILLED_LORA_FILENAME)
            if os.path.exists(downloaded) and not os.path.exists(target):
                shutil.move(downloaded, target)
        except Exception:
            try:
                import urllib.request
                req = urllib.request.Request(DISTILLED_LORA_URL, headers={"User-Agent": "Mozilla/5.0"})
                if hf_token:
                    req.add_header("Authorization", f"Bearer {hf_token}")
                with urllib.request.urlopen(req, timeout=120) as resp, open(target, "wb") as f:
                    shutil.copyfileobj(resp, f)
            except Exception:
                pass

    ensure_lora_symlinks()
    return os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10


def ensure_refine_details_lora():
    """Tự động tải ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors nếu chưa có."""
    lora_dir = os.path.join(COMFYUI_DIR, "models", "loras")
    os.makedirs(lora_dir, exist_ok=True)
    target = os.path.join(lora_dir, REFINE_DETAILS_LORA_FILENAME)
    if os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10:
        ensure_lora_symlinks()
        return True

    hf_token = _get_hf_token()
    header = ["--header", f"Authorization: Bearer {hf_token}"] if hf_token else []
    cmd = [
        "aria2c", "--console-log-level=warn", "-c",
        "-x", "8", "-s", "8", "-k", "1M",
        "-d", lora_dir, "-o", REFINE_DETAILS_LORA_FILENAME,
    ] + header + [REFINE_DETAILS_LORA_URL]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        pass

    if not (os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10):
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="Lightricks/LTX-2.5-22b-IC-LoRA-Refine-Details",
                filename=REFINE_DETAILS_LORA_FILENAME,
                local_dir=lora_dir,
                token=hf_token or None,
            )
            downloaded = os.path.join(lora_dir, REFINE_DETAILS_LORA_FILENAME)
            if os.path.exists(downloaded) and not os.path.exists(target):
                shutil.move(downloaded, target)
        except Exception:
            try:
                import urllib.request
                req = urllib.request.Request(REFINE_DETAILS_LORA_URL, headers={"User-Agent": "Mozilla/5.0"})
                if hf_token:
                    req.add_header("Authorization", f"Bearer {hf_token}")
                with urllib.request.urlopen(req, timeout=120) as resp, open(target, "wb") as f:
                    shutil.copyfileobj(resp, f)
            except Exception:
                pass

    ensure_lora_symlinks()
    ok = os.path.exists(target) and os.path.getsize(target) > 1024 * 1024 * 10
    if not ok:
        print("⚠️ Chú ý: Chưa tải được Refine Details LoRA. Đảm bảo đã bấm 'Agree' tại https://huggingface.co/Lightricks/LTX-2.5-22b-IC-LoRA-Refine-Details và cấp quyền HF_TOKEN!")
    return ok


def resolve_comfy_lora_name(target_name, class_type="ComfyUILTX25MSRICLoRALoader"):
    """
    Tự động truy vấn ComfyUI /object_info để lấy chính xác tên file LoRA
    (khắc phục lỗi Validation khi file nằm trong subfolder 'ltx2.5/' hoặc thư mục gốc).
    """
    if not target_name:
        return target_name
    ensure_lora_symlinks()
    base_target = os.path.basename(target_name)
    try:
        url = f"http://127.0.0.1:8188/object_info/{class_type}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
        opts = data.get(class_type, {}).get("input", {}).get("required", {}).get("lora_name", [[]])[0]
        if isinstance(opts, list) and opts:
            # 1. Khớp chính xác
            if target_name in opts:
                return target_name
            # 2. Khớp theo base filename (vd: 'ltx2.5/LTX-2.5-Licon-MSR-V1.safetensors')
            for opt in opts:
                if opt == base_target or os.path.basename(opt) == base_target or opt.endswith("/" + base_target) or opt.endswith("\\" + base_target):
                    return opt
            # 3. Khớp không phân biệt hoa thường
            for opt in opts:
                if base_target.lower() in opt.lower():
                    return opt
            # 4. Tìm kiếm từ khóa MSR / Licon
            for opt in opts:
                if "msr" in opt.lower() or "licon" in opt.lower():
                    return opt
    except Exception:
        pass

    # Fallback kiểm tra file system thực tế trên Colab
    lora_dir = os.path.join(COMFYUI_DIR, "models", "loras")
    if os.path.exists(os.path.join(lora_dir, "ltx2.5", base_target)):
        return f"ltx2.5/{base_target}"
    if os.path.exists(os.path.join(lora_dir, base_target)):
        return base_target
    return target_name


def ensure_clip_symlinks():
    """Đồng bộ symlink giữa models/text_encoders/ và models/clip/ để CLIPLoader luôn nhận diện được."""
    try:
        te_dir = os.path.join(COMFYUI_DIR, "models", "text_encoders")
        clip_dir = os.path.join(COMFYUI_DIR, "models", "clip")
        os.makedirs(te_dir, exist_ok=True)
        os.makedirs(clip_dir, exist_ok=True)
        sync_files = [
            TEXT_ENCODER_BF16_FILENAME,
            TEXT_ENCODER_INT8_FILENAME,
        ]
        for f_name in sync_files:
            te_path = os.path.join(te_dir, f_name)
            clip_path = os.path.join(clip_dir, f_name)
            if os.path.exists(te_path) and not os.path.exists(clip_path):
                try:
                    os.symlink(te_path, clip_path)
                except Exception:
                    shutil.copy2(te_path, clip_path)
            elif os.path.exists(clip_path) and not os.path.exists(te_path):
                try:
                    os.symlink(clip_path, te_path)
                except Exception:
                    shutil.copy2(clip_path, te_path)
    except Exception:
        pass


def ensure_text_encoder(filename=None):
    """Kiểm tra và tự động tải Text Encoder (gemma4 bf16 hoặc int8) nếu chưa có."""
    if not filename:
        filename = TEXT_ENCODER_FILENAME

    clean_filename = (
        TEXT_ENCODER_INT8_FILENAME
        if "int8" in str(filename).lower()
        else TEXT_ENCODER_BF16_FILENAME
    )

    te_dir = os.path.join(COMFYUI_DIR, "models", "text_encoders")
    clip_dir = os.path.join(COMFYUI_DIR, "models", "clip")
    os.makedirs(te_dir, exist_ok=True)
    os.makedirs(clip_dir, exist_ok=True)

    target_te = os.path.join(te_dir, clean_filename)
    target_clip = os.path.join(clip_dir, clean_filename)

    if (os.path.exists(target_te) and os.path.getsize(target_te) > 1024 * 1024 * 10) or \
       (os.path.exists(target_clip) and os.path.getsize(target_clip) > 1024 * 1024 * 10):
        ensure_clip_symlinks()
        return clean_filename

    url = (
        TEXT_ENCODER_BF16_URL
        if clean_filename == TEXT_ENCODER_BF16_FILENAME
        else TEXT_ENCODER_INT8_URL
    )

    hf_token = _get_hf_token()
    header = ["--header", f"Authorization: Bearer {hf_token}"] if hf_token else []
    cmd = [
        "aria2c", "--console-log-level=warn", "-c",
        "-x", "8", "-s", "8", "-k", "1M",
        "-d", te_dir, "-o", clean_filename,
    ] + header + [url]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        pass

    if not (os.path.exists(target_te) and os.path.getsize(target_te) > 1024 * 1024 * 10):
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="Lightricks/LTX-2.5",
                filename=f"text_encoders/{clean_filename}",
                local_dir=te_dir,
                token=hf_token or None,
            )
            downloaded = os.path.join(te_dir, "text_encoders", clean_filename)
            if os.path.exists(downloaded) and not os.path.exists(target_te):
                shutil.move(downloaded, target_te)
        except Exception:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                if hf_token:
                    req.add_header("Authorization", f"Bearer {hf_token}")
                with urllib.request.urlopen(req, timeout=300) as resp, open(target_te, "wb") as f:
                    shutil.copyfileobj(resp, f)
            except Exception:
                pass

    ensure_clip_symlinks()
    return clean_filename


def resolve_comfy_clip_name(target_name=None):
    """
    Tự động truy vấn ComfyUI /object_info/CLIPLoader để lấy chính xác tên file CLIP/Text Encoder
    (khắc phục lỗi Validation khi file nằm trong text_encoders/ hoặc clip/).
    """
    if not target_name:
        target_name = TEXT_ENCODER_FILENAME

    clean_target = (
        TEXT_ENCODER_INT8_FILENAME
        if "int8" in str(target_name).lower()
        else TEXT_ENCODER_BF16_FILENAME
    )
    base_target = os.path.basename(clean_target)
    ensure_clip_symlinks()

    try:
        url = "http://127.0.0.1:8188/object_info/CLIPLoader"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
        opts = data.get("CLIPLoader", {}).get("input", {}).get("required", {}).get("clip_name", [[]])[0]
        if isinstance(opts, list) and opts:
            if clean_target in opts:
                return clean_target
            for opt in opts:
                if opt == base_target or os.path.basename(opt) == base_target:
                    return opt
            for opt in opts:
                if base_target.lower() in opt.lower():
                    return opt
    except Exception:
        pass

    for d in [os.path.join(COMFYUI_DIR, "models", "text_encoders"), os.path.join(COMFYUI_DIR, "models", "clip")]:
        if os.path.exists(os.path.join(d, base_target)):
            return base_target
    return clean_target


def find_latest_video(preferred_prefix=None):
    if preferred_prefix:
        mp4_files = glob.glob(f"{OUTPUT_DIR}**/*{preferred_prefix}*.mp4", recursive=True)
        if mp4_files:
            return max(mp4_files, key=os.path.getmtime)
    mp4_files = glob.glob(f"{OUTPUT_DIR}**/*.mp4", recursive=True)
    if not mp4_files:
        return None
    return max(mp4_files, key=os.path.getmtime)


def trim_ref_frames(video_path, target_duration_s, fps):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        actual = float(res.stdout.strip())
    except Exception:
        return video_path
    if actual <= target_duration_s + 0.1:
        return video_path
    trim_start = actual - target_duration_s
    trimmed_path = video_path.rsplit(".", 1)[0] + "_trimmed.mp4"
    cmd_trim = ["ffmpeg", "-y", "-ss", f"{trim_start:.4f}", "-i", video_path,
                "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", trimmed_path]
    if subprocess.run(cmd_trim, capture_output=True).returncode == 0 and os.path.exists(trimmed_path):
        return trimmed_path
    return video_path


def concat_videos(video_list, out_name):
    concat_file = os.path.join(OUTPUT_DIR, f"concat_{out_name}.txt")
    with open(concat_file, "w") as f:
        for vid in video_list:
            f.write(f"file '{os.path.abspath(vid)}'\n")
    final_output = os.path.join(OUTPUT_DIR, f"{out_name}_{int(time.time())}.mp4")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", final_output]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(final_output):
        try: os.remove(concat_file)
        except OSError: pass
        return final_output
    return video_list[-1]


# ==============================================================================
# HÀM GỬI PROMPT & THEO DÕI TIẾN TRÌNH COMFYUI
# ==============================================================================
def submit_and_wait_gen(workflow, scene_label="", max_wait_seconds=1800, poll_interval=2):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req  = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        response  = urllib.request.urlopen(req, timeout=30)
        prompt_id = json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        free_comfyui_memory()
        raise RuntimeError(f"❌ ComfyUI từ chối workflow: {body[:600]}")
    except Exception as e:
        free_comfyui_memory()
        raise RuntimeError(f"❌ Lỗi gửi API tới ComfyUI: {e}")

    waited = 0
    while waited < max_wait_seconds:
        try:
            req_history = urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}")
            with urllib.request.urlopen(req_history, timeout=10) as resp:
                hist_data = json.loads(resp.read().decode("utf-8"))
            if prompt_id in hist_data:
                free_comfyui_memory()
                yield True, prompt_id, "Hoàn tất!"
                return

            # Đọc log tiến trình
            prog_text = "Đang chạy sampling..."
            if os.path.exists(COMFYUI_LOG_PATH):
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    for line in reversed(f.readlines()[-20:]):
                        s = line.strip()
                        if "%" in s or "it/s" in s or "Executing node" in s:
                            prog_text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)[:100]
                            break
            yield False, prompt_id, prog_text
        except Exception:
            pass
        time.sleep(poll_interval)
        waited += poll_interval

    free_comfyui_memory()
    raise RuntimeError(f"⏰ Timeout {scene_label} quá {max_wait_seconds // 60} phút!")


# ==============================================================================
# WORKFLOW BUILDER 1: MSR 2-STAGE (ĐÃ FIX TOÀN DIỆN & THÊM START FRAME)
# ==============================================================================
def build_msr_workflow(
    *,
    prompt_relay_desc,
    prompt_main,
    negative_text=None,
    width=1280,
    height=720,
    fps=24,
    duration=10,
    seed=0,
    video_cfg=1.1,
    audio_cfg=1.0,
    msr_lora_name=None,
    msr_lora_strength=0.85,
    pic1_name=None,
    pic2_name=None,
    pic3_name=None,
    pic4_name=None,
    background_name=None,
    start_frame_name=None,
    msr_strength=0.7,
    reference_frames="33",
    run_stage2=True,
    use_distilled_lora=False,
    distilled_lora_strength=1.0,
    text_encoder_name=None,
    use_refine_lora=True,
    refine_lora_strength=0.6,
):
    if negative_text is None:
        negative_text = NEGATIVE_PROMPT_DEFAULT
    target_lora = msr_lora_name or MSR_LORA_FILENAME or "LTX-2.5-Licon-MSR-V1.safetensors"
    actual_msr_lora = resolve_comfy_lora_name(target_lora, "ComfyUILTX25MSRICLoRALoader")
    actual_clip_name = resolve_comfy_clip_name(text_encoder_name or TEXT_ENCODER_FILENAME)
    if seed is None:
        seed = 0

    safe_fps = snap_fps_safe(fps)
    half_w, half_h = half_dims(width, height)

    pic_slot_map = [
        ("pic1", pic1_name),
        ("pic2", pic2_name),
        ("pic3", pic3_name),
        ("pic4", pic4_name),
        ("background", background_name),
    ]

    # ---- Stage 1: Half Resolution ----
    wf = {
        "S1_unet":  {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "S1_clip":  {"class_type": "CLIPLoader",  "inputs": {"clip_name": actual_clip_name, "type": "ltxv", "device": "default"}},
        "S1_vvae":  {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "S1_avae":  {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
    }

    model_s1_ref = ["S1_unet", 0]
    if use_distilled_lora:
        actual_distilled = resolve_comfy_lora_name(DISTILLED_LORA_FILENAME, "LoraLoaderModelOnly")
        wf["S1_distilled_lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["S1_unet", 0], "lora_name": actual_distilled, "strength_model": float(distilled_lora_strength)},
        }
        model_s1_ref = ["S1_distilled_lora", 0]

    wf.update({
        "S1_msr_loader": {
            "class_type": "ComfyUILTX25MSRICLoRALoader",
            "inputs": {"model": model_s1_ref, "lora_name": actual_msr_lora, "strength_model": float(msr_lora_strength)},
        },
        "S1_neg_enc":     {"class_type": "CLIPTextEncode", "inputs": {"clip": ["S1_clip", 0], "text": negative_text}},
        "S1_width":       {"class_type": "INTConstant",    "inputs": {"value": half_w}},
        "S1_height":      {"class_type": "INTConstant",    "inputs": {"value": half_h}},
        "S1_fps":         {"class_type": "FloatConstant",  "inputs": {"value": float(safe_fps)}},
        "S1_frames_expr": {"class_type": "ComfyMathExpression", "inputs": {"expression": "a*b+1", "values.a": ["S1_fps", 0], "values.b": int(duration)}},
        "S1_empty_vid":   {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": ["S1_width", 0], "height": ["S1_height", 0], "length": ["S1_frames_expr", 1], "batch_size": 1}},
        "S1_empty_aud":   {"class_type": "LTXVEmptyLatentAudio", "inputs": {"audio_vae": ["S1_avae", 0], "frames_number": ["S1_frames_expr", 1], "frame_rate": ["S1_fps", 0], "batch_size": 1}},
        "S1_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model": ["S1_msr_loader", 0], "clip": ["S1_clip", 0], "latent": ["S1_empty_vid", 0],
                "global_prompt": prompt_relay_desc or "", "local_prompts": prompt_main,
                "segment_lengths": "", "epsilon": 0.001,
            },
        },
        "S1_ltxv_cond": {"class_type": "LTXVConditioning", "inputs": {"positive": ["S1_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": ["S1_fps", 0]}},
    })

    # MSR Guide Node
    msr_s1 = {
        "positive": ["S1_ltxv_cond", 0], "negative": ["S1_ltxv_cond", 1],
        "vae": ["S1_vvae", 0], "latent": ["S1_empty_vid", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": float(msr_strength), "reference_frames": str(reference_frames),
        "use_tiled_encode": False, "tile_size": 256, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            wf[f"S1_load_{slot}"] = {"class_type": "LoadImage", "inputs": {"image": img}}
            msr_s1[slot] = [f"S1_load_{slot}", 0]
    wf["S1_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s1}

    # Sampler & Stage 1 Decode
    wf.update({
        "S1_guider":      {"class_type": "LTXVDualCFGGuider",  "inputs": {"model": ["S1_relay", 0], "positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S1_noise":       {"class_type": "RandomNoise",         "inputs": {"noise_seed": int(seed)}},
        "S1_sampler_sel": {"class_type": "KSamplerSelect",      "inputs": {"sampler_name": "euler_ancestral"}},
        "S1_sigmas":      {"class_type": "ManualSigmas",        "inputs": {"sigmas": SIGMAS_PASS1}},
        "S1_concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["S1_msr_guide", 2], "audio_latent": ["S1_empty_aud", 0]}},
        "S1_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S1_noise", 0], "guider": ["S1_guider", 0], "sampler": ["S1_sampler_sel", 0], "sigmas": ["S1_sigmas", 0], "latent_image": ["S1_concat_av", 0]}},
        "S1_sep_av":      {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["S1_sample", 0]}},
        "S1_crop_guides": {"class_type": "LTXVCropGuides",      "inputs": {"positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "latent": ["S1_sep_av", 0]}},
        "S1_vae_decode":  {"class_type": "VAEDecode",           "inputs": {"samples": ["S1_crop_guides", 2], "vae": ["S1_vvae", 0]}},
        "S1_aud_decode":  {"class_type": "LTXVAudioVAEDecode",  "inputs": {"samples": ["S1_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S1_create_vid":  {"class_type": "CreateVideo",         "inputs": {"images": ["S1_vae_decode", 0], "audio": ["S1_aud_decode", 0], "fps": float(safe_fps)}},
        "S1_save":        {"class_type": "SaveVideo",           "inputs": {"video": ["S1_create_vid", 0], "filename_prefix": "output/LTX25_MSR_Stage1", "format": "auto", "codec": "auto"}},
    })

    if not run_stage2:
        return wf

    # ---- Stage 2: Spatial Upscale x2 + Refiner ----
    s2_model = ["S1_msr_loader", 0]
    if use_refine_lora:
        actual_refine = resolve_comfy_lora_name(REFINE_DETAILS_LORA_FILENAME, "LoraLoaderModelOnly")
        wf["S2_refine_lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["S1_msr_loader", 0], "lora_name": actual_refine, "strength_model": float(refine_lora_strength)},
        }
        s2_model = ["S2_refine_lora", 0]

    wf.update({
        "S2_upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "S2_upsampler":      {"class_type": "LTXVLatentUpsampler",       "inputs": {"samples": ["S1_crop_guides", 2], "upscale_model": ["S2_upscale_loader", 0], "vae": ["S1_vvae", 0]}},
        "S2_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model": s2_model, "clip": ["S1_clip", 0], "latent": ["S2_upsampler", 0],
                "global_prompt": prompt_relay_desc or "", "local_prompts": prompt_main,
                "segment_lengths": "", "epsilon": 0.001,
            },
        },
        "S2_ltxv_cond": {
            "class_type": "LTXVConditioning",
            "inputs": {"positive": ["S2_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": ["S1_fps", 0]},
        },
    })

    msr_s2 = {
        "positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1],
        "vae": ["S1_vvae", 0], "latent": ["S2_upsampler", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": float(msr_strength), "reference_frames": str(reference_frames),
        "use_tiled_encode": False, "tile_size": 256, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            msr_s2[slot] = [f"S1_load_{slot}", 0]
    wf["S2_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s2}

    # Stage 2 Sampling & Decode: S2_crop_guides nhận trực tiếp conditioning từ S2_msr_guide để cắt sạch reference frames
    wf.update({
        "S2_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S2_msr_guide", 2], "audio_latent": ["S1_sep_av", 1]}},
        "S2_dual_guider": {"class_type": "LTXVDualCFGGuider",    "inputs": {"model": ["S2_relay", 0], "positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S2_noise":       {"class_type": "RandomNoise",           "inputs": {"noise_seed": int(seed)}},
        "S2_sampler_sel": {"class_type": "KSamplerSelect",        "inputs": {"sampler_name": "euler"}},
        "S2_sigmas":      {"class_type": "ManualSigmas",          "inputs": {"sigmas": SIGMAS_PASS2}},
        "S2_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S2_noise", 0], "guider": ["S2_dual_guider", 0], "sampler": ["S2_sampler_sel", 0], "sigmas": ["S2_sigmas", 0], "latent_image": ["S2_concat_av", 0]}},
        "S2_sep_av":      {"class_type": "LTXVSeparateAVLatent",  "inputs": {"av_latent": ["S2_sample", 0]}},
        "S2_crop_guides": {"class_type": "LTXVCropGuides",        "inputs": {"positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "latent": ["S2_sep_av", 0]}},
        "S2_vae_tiled":   {"class_type": "VAEDecodeTiled",        "inputs": {"samples": ["S2_crop_guides", 2], "vae": ["S1_vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "S2_aud_decode":  {"class_type": "LTXVAudioVAEDecode",   "inputs": {"samples": ["S2_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S2_create_vid":  {"class_type": "CreateVideo",           "inputs": {"images": ["S2_vae_tiled", 0], "audio": ["S2_aud_decode", 0], "fps": float(safe_fps)}},
        "S2_save":        {"class_type": "SaveVideo",             "inputs": {"video": ["S2_create_vid", 0], "filename_prefix": "output/LTX25_MSR_DualStage", "format": "auto", "codec": "auto"}},
    })

    return wf


# ==============================================================================
# WORKFLOW BUILDER 2: INGREDIENTS IC-LORA (OFFICIAL REFERENCE SHEET)
# ==============================================================================
def build_ingredients_workflow(
    *,
    sheet_image_name,
    positive_prompt,
    negative_prompt=None,
    width=960,
    height=544,
    fps=24,
    duration=5,
    seed=0,
    video_cfg=1.1,
    use_distilled_lora=False,
    distilled_lora_strength=1.0,
    text_encoder_name=None,
):
    if negative_prompt is None:
        negative_prompt = NEGATIVE_PROMPT_DEFAULT
    if seed is None:
        seed = 0

    safe_fps = snap_fps_safe(fps)
    w, h = safe_dims(width, height)
    actual_ing_lora = resolve_comfy_lora_name(INGREDIENTS_LORA_FILENAME, "LTXICLoRALoaderModelOnly")
    actual_clip_name = resolve_comfy_clip_name(text_encoder_name or TEXT_ENCODER_FILENAME)

    wf = {
        "unet":   {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "clip":   {"class_type": "CLIPLoader",  "inputs": {"clip_name": actual_clip_name, "type": "ltxv", "device": "default"}},
        "vvae":   {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "avae":   {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
    }

    ing_model = ["unet", 0]
    if use_distilled_lora:
        actual_distilled = resolve_comfy_lora_name(DISTILLED_LORA_FILENAME, "LoraLoaderModelOnly")
        wf["distilled_lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["unet", 0], "lora_name": actual_distilled, "strength_model": float(distilled_lora_strength)},
        }
        ing_model = ["distilled_lora", 0]

    wf.update({
        "ic_lora": {
            "class_type": "LTXICLoRALoaderModelOnly",
            "inputs": {"model": ing_model, "lora_name": actual_ing_lora, "strength_model": 1.0},
        },
        "pos_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": positive_prompt}},
        "neg_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": negative_prompt}},
        "cond":    {"class_type": "LTXVConditioning", "inputs": {"positive": ["pos_enc", 0], "negative": ["neg_enc", 0], "frame_rate": float(safe_fps)}},
        "load_sheet": {"class_type": "LoadImage", "inputs": {"image": sheet_image_name}},
        "fps_const":   {"class_type": "FloatConstant", "inputs": {"value": float(safe_fps)}},
        "frames_expr": {"class_type": "ComfyMathExpression", "inputs": {"expression": "1 + floor(a*b/8)*8", "values.a": ["fps_const", 0], "values.b": int(duration)}},
        "empty_vid":   {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": w, "height": h, "length": ["frames_expr", 1], "batch_size": 1}},
        "empty_aud":   {"class_type": "LTXVEmptyLatentAudio", "inputs": {"audio_vae": ["avae", 0], "frames_number": ["frames_expr", 1], "frame_rate": ["fps_const", 0], "batch_size": 1}},
        "repeat_sheet": {"class_type": "RepeatImageBatch", "inputs": {"image": ["load_sheet", 0], "amount": ["frames_expr", 1]}},
        "ic_guide": {
            "class_type": "LTXAddVideoICLoRAGuide",
            "inputs": {
                "positive": ["cond", 0], "negative": ["cond", 1], "vae": ["vvae", 0],
                "latent": ["empty_vid", 0], "images": ["repeat_sheet", 0],
                "lora_strength": 1.0, "img_compression": 0.0, "bypass": True,
            },
        },
        "concat_av": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["ic_guide", 2], "audio_latent": ["empty_aud", 0]}},
        "guider":    {"class_type": "CFGGuider", "inputs": {"model": ["ic_lora", 0], "positive": ["ic_guide", 0], "negative": ["ic_guide", 1], "cfg": float(video_cfg)}},
        "noise":     {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "sigmas":    {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "sample":    {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_sel", 0], "sigmas": ["sigmas", 0], "latent_image": ["concat_av", 0]}},
        "sep_av":    {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["sample", 0]}},
        "crop":      {"class_type": "LTXVCropGuides", "inputs": {"positive": ["ic_guide", 0], "negative": ["ic_guide", 1], "latent": ["sep_av", 0]}},
        "vdecode":   {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["crop", 2], "vae": ["vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}},
        "adecode":   {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["sep_av", 1], "audio_vae": ["avae", 0]}},
        "make_vid":  {"class_type": "CreateVideo", "inputs": {"images": ["vdecode", 0], "audio": ["adecode", 0], "fps": float(safe_fps)}},
        "save":      {"class_type": "SaveVideo", "inputs": {"video": ["make_vid", 0], "filename_prefix": "output/LTX25_Ingredients", "format": "auto", "codec": "auto"}},
    })
    return wf


# ==============================================================================
# WORKFLOW BUILDER 3: CINEMA TWO-STAGE I2V / T2V
# ==============================================================================
def build_cinema_workflow(
    *,
    start_frame_name=None,
    positive_prompt,
    negative_prompt=None,
    width=1280,
    height=720,
    fps=24,
    duration=5,
    seed=0,
    video_cfg=1.1,
    use_distilled_lora=False,
    distilled_lora_strength=1.0,
    text_encoder_name=None,
    use_refine_lora=True,
    refine_lora_strength=0.6,
):
    if negative_prompt is None:
        negative_prompt = NEGATIVE_PROMPT_DEFAULT
    if seed is None:
        seed = 0

    safe_fps = snap_fps_safe(fps)
    half_w, half_h = half_dims(width, height)
    actual_clip_name = resolve_comfy_clip_name(text_encoder_name or TEXT_ENCODER_FILENAME)

    wf = {
        "unet":   {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "clip":   {"class_type": "CLIPLoader",  "inputs": {"clip_name": actual_clip_name, "type": "ltxv", "device": "default"}},
        "vvae":   {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "avae":   {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "pos_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": positive_prompt}},
        "neg_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": negative_prompt}},
        "fps_c":  {"class_type": "FloatConstant",  "inputs": {"value": float(safe_fps)}},
        "frames_expr": {"class_type": "ComfyMathExpression", "inputs": {"expression": "1 + floor(a*b/8)*8", "values.a": ["fps_c", 0], "values.b": int(duration)}},
        "cond":   {"class_type": "LTXVConditioning", "inputs": {"positive": ["pos_enc", 0], "negative": ["neg_enc", 0], "frame_rate": ["fps_c", 0]}},
        "empty_vid": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": half_w, "height": half_h, "length": ["frames_expr", 1], "batch_size": 1}},
        "empty_aud": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"audio_vae": ["avae", 0], "frames_number": ["frames_expr", 1], "frame_rate": ["fps_c", 0], "batch_size": 1}},
    }

    cinema_model = ["unet", 0]
    if use_distilled_lora:
        actual_distilled = resolve_comfy_lora_name(DISTILLED_LORA_FILENAME, "LoraLoaderModelOnly")
        wf["distilled_lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["unet", 0], "lora_name": actual_distilled, "strength_model": float(distilled_lora_strength)},
        }
        cinema_model = ["distilled_lora", 0]

    # Start Frame (I2V)
    vid_latent_node = ["empty_vid", 0]
    if start_frame_name:
        wf["start_img"] = {"class_type": "LoadImage", "inputs": {"image": start_frame_name}}
        wf["i2v_inject"] = {"class_type": "LTXVImgToVideoInplace", "inputs": {"latent": ["empty_vid", 0], "image": ["start_img", 0], "vae": ["vvae", 0], "strength": 0.7, "bypass": False}}
        vid_latent_node = ["i2v_inject", 0]

    wf.update({
        "concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": vid_latent_node, "audio_latent": ["empty_aud", 0]}},
        "guider":      {"class_type": "CFGGuider", "inputs": {"model": cinema_model, "positive": ["cond", 0], "negative": ["cond", 1], "cfg": float(video_cfg)}},
        "noise":       {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "sigmas":      {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_sel", 0], "sigmas": ["sigmas", 0], "latent_image": ["concat_av", 0]}},
        "sep_av":      {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["sample", 0]}},
    })

    s2_guider = ["guider", 0]
    if use_refine_lora:
        actual_refine = resolve_comfy_lora_name(REFINE_DETAILS_LORA_FILENAME, "LoraLoaderModelOnly")
        wf["s2_refine_lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": cinema_model, "lora_name": actual_refine, "strength_model": float(refine_lora_strength)},
        }
        wf["s2_guider"] = {
            "class_type": "CFGGuider",
            "inputs": {"model": ["s2_refine_lora", 0], "positive": ["cond", 0], "negative": ["cond", 1], "cfg": float(video_cfg)},
        }
        s2_guider = ["s2_guider", 0]

    wf.update({
        # Stage 2: Spatial Upscale x2
        "upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "upsampler":      {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["sep_av", 0], "upscale_model": ["upscale_loader", 0], "vae": ["vvae", 0]}},
        "s2_concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["upsampler", 0], "audio_latent": ["sep_av", 1]}},
        "s2_noise":       {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "s2_sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "s2_sigmas":      {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS2}},
        "s2_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["s2_noise", 0], "guider": s2_guider, "sampler": ["s2_sampler_sel", 0], "sigmas": ["s2_sigmas", 0], "latent_image": ["s2_concat_av", 0]}},
        "s2_sep_av":      {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["s2_sample", 0]}},
        "vdecode":        {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["s2_sep_av", 0], "vae": ["vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "adecode":        {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["s2_sep_av", 1], "audio_vae": ["avae", 0]}},
        "make_vid":       {"class_type": "CreateVideo", "inputs": {"images": ["vdecode", 0], "audio": ["adecode", 0], "fps": float(safe_fps)}},
        "save":           {"class_type": "SaveVideo", "inputs": {"video": ["make_vid", 0], "filename_prefix": "output/LTX25_Cinema2Stage", "format": "auto", "codec": "auto"}},
    })
    return wf


# ==============================================================================
# HÀM ĐIỀU PHỐI GENERATE (GRADIO DISPATCHER)
# ==============================================================================
def studio_generate_gradio(
    studio_mode,
    act1_path, act2_path, act3_path, act4_path, bg_path,
    prompt_relay_desc, prompt_main, negative_text,
    aspect_ratio, v_length, v_fps, v_seed=0, num_segments=1, fixed_seed=True,
    video_cfg=1.1, msr_strength=0.7, reference_frames="33", run_stage2=True, low_vram=True, use_quality_wrap=True,
    use_distilled_lora=False, distilled_lora_strength=1.0,
    text_encoder_choice="gemma4-12b-with-proj-ltx-2.5-bf16.safetensors (BF16 Chuẩn cao cấp)",
    use_refine_lora=True, refine_lora_strength=0.6,
    smart_actor_filter=True,
):
    prompts = split_prompts(prompt_main)
    if not prompts:
        yield None, None, "⚠️ Vui lòng nhập ít nhất một dòng kịch bản / prompt!"
        return

    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

    yield None, None, f"⬇️ Đang kiểm tra / nạp Text Encoder ({text_encoder_choice.split()[0]})..."
    active_clip = ensure_text_encoder(text_encoder_choice)

    if run_stage2:
        yield None, None, "⬇️ Đang kiểm tra / nạp Spatial Upscaler x2 (ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0)..."
        ensure_spatial_upscaler()
        if use_refine_lora:
            yield None, None, "⬇️ Đang kiểm tra / nạp Refine Details LoRA (ltx-2.5-22b-ic-lora-refine-details-1.0)..."
            ensure_refine_details_lora()

    if use_distilled_lora:
        yield None, None, "⬇️ Đang kiểm tra / tải Official Distilled LoRA 450 (ltx-2.5-22b-distilled-lora-450-bf16)..."
        ensure_distilled_lora()

    yield None, None, "🔄 Đang kiểm tra / đánh thức ComfyUI server..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, None, f"❌ {e}"; return

    base_seed = get_seed(v_seed)
    os.makedirs(INPUT_DIR, exist_ok=True)

    def _copy_in(path, prefix):
        if not path: return None
        ext = os.path.splitext(path)[1].lower() or ".png"
        fname = f"{prefix}_{int(time.time())}_{random.randint(100, 999)}{ext}"
        shutil.copy(path, os.path.join(INPUT_DIR, fname))
        return fname

    pic1_name = _copy_in(act1_path, "act1")
    pic2_name = _copy_in(act2_path, "act2")
    pic3_name = _copy_in(act3_path, "act3")
    pic4_name = _copy_in(act4_path, "act4")
    bg_name   = _copy_in(bg_path,   "bg")

    scene_prompts = prompts if len(prompts) > 1 else [prompts[0]] * max(1, int(num_segments))
    total_scenes  = len(scene_prompts)
    total_secs    = total_scenes * int(v_length)

    stage2_desc = f"Bật (x2 Spatial Upscale + Refine Details LoRA {refine_lora_strength})" if (run_stage2 and use_refine_lora) else ("Bật (x2 Spatial Upscale)" if run_stage2 else "Tắt (Stage 1 Only)")
    yield None, None, (
        f"✅ Server sẵn sàng. Bắt đầu sản xuất {total_scenes} phân cảnh ({total_secs}s tổng).\n"
        f"🎬 Chế độ: {studio_mode}\n"
        f"🔤 Text Encoder: {active_clip}\n"
        f"✨ Stage 2 Refiner: {stage2_desc}\n"
        f"⚡ Distilled LoRA: {'Bật' if use_distilled_lora else 'Tắt'}"
    )

    generated_videos = []
    for i, p in enumerate(scene_prompts):
        label  = f"phân cảnh {i + 1}/{total_scenes}"
        seed_i = base_seed if fixed_seed else (base_seed + i)

        # 1. Làm sạch prompt: loại bỏ audio / speech transcript, tách 2 shot 4s+4s thành nhịp 'Shot 1 | Shot 2' cho PromptRelay
        p_clean = clean_visual_prompt_for_relay(p)
        p_wrap  = apply_quality_wrapping(p_clean, use_wrap=bool(use_quality_wrap))

        # 2. Nhận diện các Act có mặt trong phân cảnh này để chỉ nạp slot ảnh của Act đó
        if smart_actor_filter and (pic2_name or pic3_name or pic4_name):
            active_map = detect_active_actors_for_scene(p, prompt_relay_desc or "")
        else:
            active_map = {"pic1": True, "pic2": True, "pic3": True, "pic4": True, "bg": True}

        cur_pic1 = pic1_name if active_map.get("pic1", True) else None
        cur_pic2 = pic2_name if active_map.get("pic2", False) else None
        cur_pic3 = pic3_name if active_map.get("pic3", False) else None
        cur_pic4 = pic4_name if active_map.get("pic4", False) else None
        cur_bg   = bg_name   if active_map.get("bg", True)   else None

        # 3. Chuẩn hóa mô tả Act & Background: phân cách bằng \n\n, chỉ giữ Act xuất hiện trong cảnh
        scene_relay_desc = format_msr_actor_descriptions(prompt_relay_desc, active_slots=active_map)

        active_tags = []
        if cur_pic1: active_tags.append("Act 1")
        if cur_pic2: active_tags.append("Act 2")
        if cur_pic3: active_tags.append("Act 3")
        if cur_pic4: active_tags.append("Act 4")
        if cur_bg:   active_tags.append("BG")
        active_str = ", ".join(active_tags) if active_tags else "Prompt-only"

        yield generated_videos, None, (
            f"🔄 Đang thực hiện {label}... (Seed: {seed_i})\n"
            f"👥 Slots nhân vật: [{active_str}]\n"
            f"🎬 Visual Prompt: {p_clean[:120]}..."
        )

        wf = build_msr_workflow(
            prompt_relay_desc = scene_relay_desc,
            prompt_main       = p_wrap,
            negative_text     = negative_text or NEGATIVE_PROMPT_DEFAULT,
            width             = safe_width,
            height            = safe_height,
            fps               = v_fps,
            duration          = v_length,
            seed              = seed_i,
            video_cfg         = float(video_cfg or 1.1),
            pic1_name         = cur_pic1,
            pic2_name         = cur_pic2,
            pic3_name         = cur_pic3,
            pic4_name         = cur_pic4,
            background_name   = cur_bg,
            start_frame_name  = None,
            msr_strength      = msr_strength,
            reference_frames  = str(reference_frames),
            run_stage2        = bool(run_stage2),
            use_distilled_lora = bool(use_distilled_lora),
            distilled_lora_strength = float(distilled_lora_strength or 1.0),
            text_encoder_name = active_clip,
            use_refine_lora   = bool(use_refine_lora),
            refine_lora_strength = float(refine_lora_strength or 0.6),
        )

        timeout = max(600, int(v_length) * 200)
        try:
            for is_done, p_id, prog_msg in submit_and_wait_gen(wf, scene_label=label, max_wait_seconds=timeout):
                if not is_done:
                    yield generated_videos, None, (
                        f"🔄 Đang quay {label} ({i + 1}/{total_scenes})...\n"
                        f"⏳ Tiến độ: {prog_msg}\n📝 Prompt: {p[:120]}..."
                    )
                else:
                    break
        except Exception as e:
            yield generated_videos, None, f"❌ {e}"; return

        pref = "LTX25_MSR_DualStage" if run_stage2 else "LTX25_MSR_Stage1"
        latest = find_latest_video(preferred_prefix=pref)
        if not latest:
            yield generated_videos, None, f"⚠️ Không tìm thấy file video đầu ra ở {label}!"; return

        latest = trim_ref_frames(latest, target_duration_s=int(v_length), fps=v_fps)
        generated_videos.append(latest)
        yield generated_videos, None, f"🔔 [DING] ✅ Đã hoàn tất {label}!"

    if len(generated_videos) > 1:
        yield generated_videos, None, "🔄 Đang tự động ghép nối các phân cảnh thành phim hoàn chỉnh..."
        final_mp4 = concat_videos(generated_videos, "LTX_Studio_Movie")
        yield generated_videos, final_mp4, f"🔔 [DING] 🎉 Xuất phim thành công ({total_scenes} cảnh, {total_secs}s)! Base Seed: {base_seed}"
    else:
        yield generated_videos, generated_videos[0], f"🔔 [DING] 🎉 Video hoàn tất ({v_length}s)! Seed: {base_seed}"


# ==============================================================================
# GRADIO INTERFACE (LIVE DEPLOYMENT CHUẨN MINIMAX STYLE)
# ==============================================================================
custom_css = """
.gradio-container { max-width: 1560px !important; margin: 0 auto !important; font-family: 'Inter', sans-serif !important; }
#ltx-header { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
              border-radius:16px; padding:22px 28px; margin-bottom:14px; color:#fff;
              box-shadow: 0 6px 20px rgba(99,102,241,0.25); }
#ltx-header h1, #ltx-header p { margin:0 !important; color:#fff !important; }
.status-box textarea { font-family: monospace !important; font-size: 0.85rem !important; }
.scene-counter { display: inline-block; background: rgba(99, 102, 241, 0.12); padding: 4px 12px; border-radius: 999px; font-weight: 600 !important; font-size: 0.85rem !important; margin: 2px 0 6px 0 !important; }
.scene-counter p { margin: 0 !important; color: #4f46e5 !important; }
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

with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet", secondary_hue="purple", neutral_hue="slate"), css=custom_css, js=notification_js, title="LTX-2.5 Cinema Studio") as demo:
    with gr.Row(elem_id="ltx-header"):
        gr.Markdown(
            "# 🎬 LTX-2.5 MSR Studio — 4 Act & 1 Bối Cảnh Multi-Subject Cinema\n"
            "Sản xuất phim AI chuẩn điện ảnh: **Stage 2 (x2 Spatial Upscale + Refiner)** · **Refine Details LoRA 1.0** · **Gemma 4 12B BF16** · **4 Act + 1 Background MSR**."
        )

    with gr.Row():
        # --- CỘT ĐIỀU KHIỂN BÊN TRÁI ---
        with gr.Column(scale=6):
            mode_select = gr.Dropdown(
                choices=[
                    "🎭 MSR Multi-Subject Reference (4 Act + 1 BG)",
                    "🎥 Cinema Two-Stage (Không dùng ảnh ref)",
                ],
                value="🎭 MSR Multi-Subject Reference (4 Act + 1 BG)",
                label="🎬 Chế độ Pipeline (Workflow Mode)",
                interactive=True
            )

            # KHỐI 4 ACT & 1 BACKGROUND
            with gr.Group() as msr_img_group:
                gr.Markdown("#### 👥 4 Act Nhân vật & 1 Bối cảnh (MSR Reference Slots)")
                with gr.Row():
                    act1_in = gr.Image(label="🎭 Act 1 (Nhân vật 1 / Pic 1 - Bắt buộc)", type="filepath")
                    act2_in = gr.Image(label="🎭 Act 2 (Nhân vật 2 / Pic 2 - Tuỳ chọn)", type="filepath")
                with gr.Row():
                    act3_in = gr.Image(label="🎭 Act 3 (Nhân vật 3 / Pic 3 - Tuỳ chọn)", type="filepath")
                    act4_in = gr.Image(label="🎭 Act 4 (Nhân vật 4 / Pic 4 - Tuỳ chọn)", type="filepath")
                with gr.Row():
                    bg_in   = gr.Image(label="🏞️ Background (Bối cảnh không gian - Tuỳ chọn)", type="filepath")

            # KHỐI PROMPT
            with gr.Group():
                prompt_relay_in = gr.Textbox(
                    label="📋 Mô tả từng Act & Bối cảnh (Mỗi mô tả cách nhau bằng 1 dòng trống \\n\\n)",
                    lines=5,
                    placeholder=(
                        "Mô tả cho Act 1:\nImage 1: Chàng trai quân sư Lạc Phong và mèo đen Kuro mắt hổ phách phát sáng...\n\n"
                        "Mô tả cho Act 2:\nImage 2: Công chúa Cáo tuyết chín đuôi Aria lông trắng muốt, mắt ngọc bích...\n\n"
                        "Mô tả cho Act 3:\nImage 3: Đại tướng cự lang Fenris khổng lồ, giáp sắt phù văn phong băng...\n\n"
                        "Mô tả cho Act 4:\nImage 4: Đại nguyên soái sư tử Balthazar chân cơ giới ma đạo đồng thau...\n\n"
                        "Mô tả cho Background:\nBackground: Thánh địa cổ thụ Sylvanheim rừng ma thuật..."
                    )
                )
                scene_counter = gr.Markdown("🔹 **Số phân cảnh:** 0", elem_classes="scene-counter")
                prompt_main_in = gr.Textbox(
                    label="📝 Kịch bản phân cảnh (Mỗi đoạn cách nhau 1 dòng trống là 1 phân cảnh)",
                    lines=6,
                    placeholder=(
                        "Dán toàn bộ kịch bản các phân cảnh vào đây.\n"
                        "Hệ thống sẽ tự động làm sạch Audio/Voiceover, chia nhịp cú máy (0s-4s | 4s-8s), và tự động nạp đúng Act xuất hiện trong từng cảnh."
                    )
                )
                neg_prompt_in = gr.Textbox(
                    label="🚫 Negative Prompt",
                    lines=2,
                    value=NEGATIVE_PROMPT_DEFAULT
                )

            # THÔNG SỐ QUAY PHIM
            with gr.Row():
                aspect_in = gr.Dropdown(
                    choices=[
                        "16:9 (1280x720) · HD 720p Ngang",
                        "9:16 (720x1280) · HD 720p Dọc",
                        "1:1 (720x720) · HD Vuông",
                        "16:9 (832x480) · Nhẹ / Tiết kiệm VRAM",
                        "16:9 (1536x864) · 1.5K Cinema (Cần GPU L4/A100)"
                    ],
                    value="16:9 (1280x720) · HD 720p Ngang",
                    label="Tỷ lệ khung hình"
                )
                duration_in = gr.Slider(minimum=3, maximum=15, value=8, step=1, label="Thời lượng mỗi cảnh (giây)")
                fps_in      = gr.Slider(minimum=24, maximum=30, value=24, step=6, label="Tốc độ khung hình (24fps chuẩn điện ảnh)")

            with gr.Row():
                seed_in     = gr.Number(value=0, label="Seed (Mặc định: 0, -1 để ngẫu nhiên)", precision=0)
                segments_in = gr.Slider(minimum=1, maximum=10, value=1, step=1, label="Số phân cảnh lặp (nếu chỉ 1 prompt)")
                fixed_seed_in = gr.Checkbox(label="Cố định Seed cho mọi cảnh", value=True)

            # KHỐI CẤU HÌNH ĐIỆN ẢNH CAO CẤP (STAGE 2 REFINER + REFINE DETAILS LORA + GEMMA BF16)
            with gr.Group():
                gr.Markdown("#### ✨ Cấu hình Siêu Nét & Điện Ảnh (Stage 2 Refiner & Gemma BF16)")
                with gr.Row():
                    stage2_in = gr.Checkbox(
                        label="🚀 Chạy Stage 2 (x2 Spatial Upscale + Refiner)",
                        value=True,
                        info="Tự động nhân đôi độ phân giải không gian và tinh chỉnh nét từng khung hình."
                    )
                    refine_lora_in = gr.Checkbox(
                        label="✨ Dùng Refine Details LoRA ở Stage 2 (ltx-2.5-22b-ic-lora-refine-details-1.0)",
                        value=True,
                        info="LoRA chính thức tinh chỉnh siêu nét chi tiết da mặt, sợi tóc/lông, texture cho Stage 2 Refiner."
                    )
                with gr.Row():
                    text_encoder_in = gr.Dropdown(
                        choices=[
                            "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors (BF16 Chuẩn cao cấp)",
                            "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors (INT8 Tiết kiệm VRAM)",
                        ],
                        value="gemma4-12b-with-proj-ltx-2.5-bf16.safetensors (BF16 Chuẩn cao cấp)",
                        label="🔤 Text Encoder (Gemma 4 12B with Projection)",
                        info="BF16: Khả năng diễn giải prompt và chi tiết tối đa | INT8: Tiết kiệm ~12GB VRAM/RAM cho GPU ≤16GB"
                    )
                    refine_lora_str_in = gr.Slider(
                        minimum=0.1, maximum=1.0, value=0.6, step=0.05,
                        label="Độ mạnh Refine Details LoRA (Khuyên dùng 0.5 - 0.6)"
                    )

            with gr.Accordion("⚙️ Tùy chỉnh nâng cao & Bộ nhớ", open=False):
                cfg_in = gr.Slider(minimum=1.0, maximum=3.0, value=1.1, step=0.1, label="Video CFG Scale", info="Khuyên dùng 1.0 - 1.2 cho model Distilled để tránh cháy sáng / bóng dầu")
                msr_str_in = gr.Slider(minimum=0.1, maximum=1.0, value=0.7, step=0.05, label="MSR Reference Strength")
                ref_frames_in = gr.Dropdown(choices=["17", "33", "49"], value="33", label="Số Frame tham chiếu MSR")
                lowvram_in = gr.Checkbox(label="Low VRAM Mode (Bật khi dùng GPU ≤16GB)", value=True)
                wrap_in    = gr.Checkbox(label="Tự động thêm tiền tố/hậu tố chất lượng điện ảnh (Matte Film Look)", value=True)
                with gr.Row():
                    distilled_lora_in = gr.Checkbox(
                        label="⚡ Dùng Official Distilled LoRA 450 (ltx-2.5-22b-distilled-lora-450-bf16)",
                        value=False,
                        info="LoRA gia tốc chính thức từ Lightricks (450 steps). Tự động tải nếu chưa có."
                    )
                    distilled_lora_str_in = gr.Slider(
                        minimum=0.1, maximum=1.0, value=1.0, step=0.05,
                        label="Độ mạnh Distilled LoRA (Strength)"
                    )
                with gr.Row():
                    smart_filter_in = gr.Checkbox(
                        label="🎯 Tự động phân bổ Act theo phân cảnh (Smart Scene Actor Mapping)",
                        value=True,
                        info="Tự động chỉ nạp ảnh của nhân vật xuất hiện trong cảnh, ngăn ngừa các nhân vật khác bị ép vào sai cảnh."
                    )

            with gr.Row():
                generate_btn = gr.Button("🎬 Bắt đầu sản xuất phim", variant="primary", scale=3, size="lg")
                clr_btn = gr.Button("🗑️ Xóa & Dọn VRAM", scale=1)

        # --- CỘT HIỂN THỊ KẾT QUẢ BÊN PHẢI ---
        with gr.Column(scale=5):
            status_box = gr.Textbox(label="📊 Tiến độ sản xuất", lines=5, interactive=False, elem_classes=["status-box"])
            final_video_out = gr.Video(label="🎥 Phim thành phẩm (Full Hoàn thiện)", interactive=False)
            gallery_out = gr.Gallery(label="🎞️ Các phân cảnh riêng lẻ", columns=2, height="auto")
            with gr.Accordion("📜 Server Logs & Quản lý", open=False):
                log_box = gr.Textbox(label="ComfyUI Log", lines=12, interactive=False)
                refresh_log_btn = gr.Button("🔄 Cập nhật log", size="sm")
                refresh_log_btn.click(read_server_log, outputs=log_box)

    # Sự kiện đếm phân cảnh thời gian thực
    def _update_scene_count(txt):
        return f"🔹 **Số phân cảnh:** {len(split_prompts(txt))}"
    prompt_main_in.change(_update_scene_count, inputs=prompt_main_in, outputs=scene_counter)

    # Sự kiện tạo video
    generate_btn.click(
        studio_generate_gradio,
        inputs=[
            mode_select,
            act1_in, act2_in, act3_in, act4_in, bg_in,
            prompt_relay_in, prompt_main_in, neg_prompt_in,
            aspect_in, duration_in, fps_in, seed_in, segments_in, fixed_seed_in,
            cfg_in, msr_str_in, ref_frames_in, stage2_in, lowvram_in, wrap_in,
            distilled_lora_in, distilled_lora_str_in,
            text_encoder_in,
            refine_lora_in, refine_lora_str_in,
            smart_filter_in,
        ],
        outputs=[gallery_out, final_video_out, status_box]
    )

    # Sự kiện Clear
    def on_clear():
        free_comfyui_memory()
        return None, None, "🟢 Đã dọn dẹp hàng đợi và giải phóng GPU VRAM!", "🔹 **Số phân cảnh:** 0"
    clr_btn.click(fn=on_clear, outputs=[gallery_out, final_video_out, status_box, scene_counter])

# ==============================================================================
# KHỞI CHẠY LIVE (TỰ ĐỘNG KẾT NỐI VÀ MỞ LINK GRADIO.LIVE)
# ==============================================================================
if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("🔄 Khởi động ComfyUI server (LTX-2.5 Cinema Studio)...")
    try:
        ensure_server(low_vram=True)
        print("🟢 ComfyUI server sẵn sàng!")
    except Exception as e:
        print(f"⚠️ {e}")

    demo.queue()
    demo.launch(
        share=True,
        inline=False,
        debug=True,
        theme=gr.themes.Soft(primary_hue="violet", secondary_hue="purple", neutral_hue="slate"),
        css=custom_css,
        js=notification_js,
    )

