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
TEXT_ENCODER_FILENAME     = globals().get("TEXT_ENCODER_FILENAME",     "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors")
VIDEO_VAE_FILENAME        = globals().get("VIDEO_VAE_FILENAME",        "ltx-2.5-video-vae-bf16.safetensors")
AUDIO_VAE_FILENAME        = globals().get("AUDIO_VAE_FILENAME",        "ltx-2.5-audio-vae-bf16.safetensors")
SPATIAL_UPSCALER_FILENAME = globals().get("SPATIAL_UPSCALER_FILENAME", "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors")
MSR_LORA_FILENAME         = globals().get("MSR_LORA_FILENAME",         "ltx2.5/LTX-2.5-Licon-MSR-V1.safetensors")
INGREDIENTS_LORA_FILENAME = globals().get("INGREDIENTS_LORA_FILENAME", "ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors")

LATENT_GROUP_FRAMES = 8

# Chuẩn Sigmas chính thức của LTX-2.5 Distilled (8 bước) và Refinement (4 bước)
SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.85, 0.7250, 0.4219, 0.0"

QUALITY_PREFIX = (
    "Cinematic photorealistic 4K ultra-detailed footage, master cinematography, "
    "sharp focus, professional lighting, natural film grain, "
)
QUALITY_SUFFIX = (
    ", lifelike textures, smooth cinematic camera movement, highly detailed faces, "
    "temporal consistency, synchronized natural sound and acoustics"
)

NEGATIVE_PROMPT_DEFAULT = (
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
        s = int(v_seed)
        return s if s > 0 else random.randint(1, 999_999_999)
    except (TypeError, ValueError):
        return random.randint(1, 999_999_999)


def apply_quality_wrapping(prompt, use_wrap=True):
    if not use_wrap or not prompt or not prompt.strip():
        return prompt
    p = prompt.strip()
    return f"{QUALITY_PREFIX}{p}{QUALITY_SUFFIX}"


def split_prompts(text):
    if not text or not text.strip():
        return []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n[ \t]*\n+", normalized.strip())
    return [b.strip() for b in blocks if b.strip()]


def ensure_lora_symlinks():
    """Tự động đồng bộ LoRA giữa models/loras/ và models/loras/ltx2.5/ để ComfyUI nhận diện cả 2 vị trí."""
    try:
        lora_dir = os.path.join(COMFYUI_DIR, "models", "loras")
        sub_dir = os.path.join(lora_dir, "ltx2.5")
        os.makedirs(sub_dir, exist_ok=True)
        msr_file = "LTX-2.5-Licon-MSR-V1.safetensors"
        src_sub = os.path.join(sub_dir, msr_file)
        dst_root = os.path.join(lora_dir, msr_file)
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


def find_latest_video():
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
    seed=None,
    video_cfg=1.5,
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
):
    if negative_text is None:
        negative_text = NEGATIVE_PROMPT_DEFAULT
    target_lora = msr_lora_name or MSR_LORA_FILENAME or "LTX-2.5-Licon-MSR-V1.safetensors"
    actual_msr_lora = resolve_comfy_lora_name(target_lora, "ComfyUILTX25MSRICLoRALoader")
    if seed is None:
        seed = random.randint(1, 999_999_999)

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
        "S1_clip":  {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "S1_vvae":  {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "S1_avae":  {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "S1_msr_loader": {
            "class_type": "ComfyUILTX25MSRICLoRALoader",
            "inputs": {"model": ["S1_unet", 0], "lora_name": actual_msr_lora, "strength_model": float(msr_lora_strength)},
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
    }

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
    wf.update({
        "S2_upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "S2_upsampler":      {"class_type": "LTXVLatentUpsampler",       "inputs": {"samples": ["S1_crop_guides", 2], "upscale_model": ["S2_upscale_loader", 0], "vae": ["S1_vvae", 0]}},
        "S2_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model": ["S1_msr_loader", 0], "clip": ["S1_clip", 0], "latent": ["S2_upsampler", 0],
                "global_prompt": prompt_relay_desc or "", "local_prompts": prompt_main,
                "segment_lengths": "", "epsilon": 0.001,
            },
        },
    })

    msr_s2 = {
        "positive": ["S2_relay", 1], "negative": ["S1_neg_enc", 0],
        "vae": ["S1_vvae", 0], "latent": ["S2_upsampler", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": float(msr_strength), "reference_frames": str(reference_frames),
        "use_tiled_encode": False, "tile_size": 256, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            msr_s2[slot] = [f"S1_load_{slot}", 0]
    wf["S2_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s2}

    # Sửa logic Stage 2: Conditioning đúng chuẩn để guider nhận diện token chính xác
    wf.update({
        "S2_ltxv_cond":   {"class_type": "LTXVConditioning",      "inputs": {"positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "frame_rate": ["S1_fps", 0]}},
        "S2_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S2_msr_guide", 2], "audio_latent": ["S1_sep_av", 1]}},
        "S2_dual_guider": {"class_type": "LTXVDualCFGGuider",    "inputs": {"model": ["S2_relay", 0], "positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S2_noise":       {"class_type": "RandomNoise",           "inputs": {"noise_seed": int(seed) + 1000}},
        "S2_sampler_sel": {"class_type": "KSamplerSelect",        "inputs": {"sampler_name": "euler_ancestral"}},
        "S2_sigmas":      {"class_type": "ManualSigmas",          "inputs": {"sigmas": SIGMAS_PASS2}},
        "S2_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S2_noise", 0], "guider": ["S2_dual_guider", 0], "sampler": ["S2_sampler_sel", 0], "sigmas": ["S2_sigmas", 0], "latent_image": ["S2_concat_av", 0]}},
        "S2_sep_av":      {"class_type": "LTXVSeparateAVLatent",  "inputs": {"av_latent": ["S2_sample", 0]}},
        "S2_crop_guides": {"class_type": "LTXVCropGuides",        "inputs": {"positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1], "latent": ["S2_sep_av", 0]}},
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
    seed=None,
    video_cfg=1.5,
):
    if negative_prompt is None:
        negative_prompt = NEGATIVE_PROMPT_DEFAULT
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps = snap_fps_safe(fps)
    w, h = safe_dims(width, height)
    actual_ing_lora = resolve_comfy_lora_name(INGREDIENTS_LORA_FILENAME, "LTXICLoRALoaderModelOnly")

    wf = {
        "unet":   {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "clip":   {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "vvae":   {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "avae":   {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "ic_lora": {
            "class_type": "LTXICLoRALoaderModelOnly",
            "inputs": {"model": ["unet", 0], "lora_name": actual_ing_lora, "strength_model": 1.0},
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
    }
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
    seed=None,
    video_cfg=1.5,
):
    if negative_prompt is None:
        negative_prompt = NEGATIVE_PROMPT_DEFAULT
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps = snap_fps_safe(fps)
    half_w, half_h = half_dims(width, height)

    wf = {
        "unet":   {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "clip":   {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
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

    # Start Frame (I2V)
    vid_latent_node = ["empty_vid", 0]
    if start_frame_name:
        wf["start_img"] = {"class_type": "LoadImage", "inputs": {"image": start_frame_name}}
        wf["i2v_inject"] = {"class_type": "LTXVImgToVideoInplace", "inputs": {"latent": ["empty_vid", 0], "image": ["start_img", 0], "vae": ["vvae", 0], "strength": 0.7, "bypass": False}}
        vid_latent_node = ["i2v_inject", 0]

    wf.update({
        "concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": vid_latent_node, "audio_latent": ["empty_aud", 0]}},
        "guider":      {"class_type": "CFGGuider", "inputs": {"model": ["unet", 0], "positive": ["cond", 0], "negative": ["cond", 1], "cfg": float(video_cfg)}},
        "noise":       {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "sigmas":      {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_sel", 0], "sigmas": ["sigmas", 0], "latent_image": ["concat_av", 0]}},
        "sep_av":      {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["sample", 0]}},

        # Stage 2: Spatial Upscale x2
        "upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "upsampler":      {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["sep_av", 0], "upscale_model": ["upscale_loader", 0], "vae": ["vvae", 0]}},
        "s2_concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["upsampler", 0], "audio_latent": ["sep_av", 1]}},
        "s2_noise":       {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed) + 1000}},
        "s2_sigmas":      {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS2}},
        "s2_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["s2_noise", 0], "guider": ["guider", 0], "sampler": ["sampler_sel", 0], "sigmas": ["s2_sigmas", 0], "latent_image": ["s2_concat_av", 0]}},
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
    pic1_path, pic2_path, pic3_path, pic4_path, bg_path, start_frame_path, ingredients_sheet_path,
    prompt_relay_desc, prompt_main, negative_text,
    aspect_ratio, v_length, v_fps, v_seed, num_segments, fixed_seed,
    video_cfg, msr_strength, reference_frames, run_stage2, low_vram, use_quality_wrap,
):
    prompts = split_prompts(prompt_main)
    if not prompts:
        yield None, None, "⚠️ Vui lòng nhập ít nhất một dòng kịch bản / prompt!"
        return

    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

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

    pic1_name  = _copy_in(pic1_path, "pic1")
    pic2_name  = _copy_in(pic2_path, "pic2")
    pic3_name  = _copy_in(pic3_path, "pic3")
    pic4_name  = _copy_in(pic4_path, "pic4")
    bg_name    = _copy_in(bg_path, "bg")
    start_name = _copy_in(start_frame_path, "start_frame")
    sheet_name = _copy_in(ingredients_sheet_path, "sheet")

    scene_prompts = prompts if len(prompts) > 1 else [prompts[0]] * max(1, int(num_segments))
    total_scenes  = len(scene_prompts)
    total_secs    = total_scenes * int(v_length)

    yield None, None, (
        f"✅ Server sẵn sàng. Bắt đầu sản xuất {total_scenes} phân cảnh ({total_secs}s tổng).\n"
        f"🎬 Chế độ: {studio_mode} · Seed gốc: {base_seed} · CFG: {video_cfg}"
    )

    generated_videos = []
    for i, p in enumerate(scene_prompts):
        label  = f"phân cảnh {i + 1}/{total_scenes}"
        seed_i = base_seed if fixed_seed else (base_seed + i)
        p_wrap = apply_quality_wrapping(p, use_wrap=bool(use_quality_wrap))

        yield generated_videos, None, f"🔄 Đang thực hiện {label}... (Seed: {seed_i})\n📝 Prompt: {p[:120]}..."

        if "MSR" in studio_mode:
            wf = build_msr_workflow(
                prompt_relay_desc = prompt_relay_desc or "",
                prompt_main       = p_wrap,
                negative_text     = negative_text or NEGATIVE_PROMPT_DEFAULT,
                width             = safe_width,
                height            = safe_height,
                fps               = v_fps,
                duration          = v_length,
                seed              = seed_i,
                video_cfg         = float(video_cfg or 1.5),
                pic1_name         = pic1_name,
                pic2_name         = pic2_name,
                pic3_name         = pic3_name,
                pic4_name         = pic4_name,
                background_name   = bg_name,
                start_frame_name  = start_name,
                msr_strength      = msr_strength,
                reference_frames  = str(reference_frames),
                run_stage2        = bool(run_stage2),
            )
        elif "Ingredients" in studio_mode:
            if not sheet_name:
                yield generated_videos, None, "⚠️ Chế độ Ingredients yêu cầu tải lên Reference Sheet!"
                return
            wf = build_ingredients_workflow(
                sheet_image_name = sheet_name,
                positive_prompt  = p_wrap,
                negative_prompt  = negative_text or NEGATIVE_PROMPT_DEFAULT,
                width            = safe_width,
                height           = safe_height,
                fps              = v_fps,
                duration         = v_length,
                seed             = seed_i,
                video_cfg        = float(video_cfg or 1.5),
            )
        else: # Cinema Two-Stage
            wf = build_cinema_workflow(
                start_frame_name = start_name,
                positive_prompt  = p_wrap,
                negative_prompt  = negative_text or NEGATIVE_PROMPT_DEFAULT,
                width            = safe_width,
                height           = safe_height,
                fps              = v_fps,
                duration         = v_length,
                seed             = seed_i,
                video_cfg        = float(video_cfg or 1.5),
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

        latest = find_latest_video()
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
            "# 🎬 LTX-2.5 Cinema Studio — Multi-Subject & Consistency Studio\n"
            "Sản xuất phim AI chuyên nghiệp với tính nhất quán nhân vật cao: "
            "MSR 2-Stage (Fixed), Ingredients Reference Sheet & Two-Stage Cinema."
        )

    with gr.Row():
        # --- CỘT ĐIỀU KHIỂN BÊN TRÁI ---
        with gr.Column(scale=6):
            mode_select = gr.Dropdown(
                choices=[
                    "🎭 MSR Multi-Subject Reference (2-Stage Upscale)",
                    "🧪 Ingredients IC-LoRA (Official Reference Sheet)",
                    "🎥 Cinema Two-Stage I2V/T2V (Start Frame to 2-Stage Refine)"
                ],
                value="🎭 MSR Multi-Subject Reference (2-Stage Upscale)",
                label="🎬 Chế độ Pipeline (Workflow Mode)",
                interactive=True
            )

            # KHỐI ẢNH MSR
            with gr.Group() as msr_img_group:
                gr.Markdown("#### 👥 Ảnh tham khảo nhân vật & Bối cảnh (MSR Slots)")
                with gr.Row():
                    pic1_in = gr.Image(label="Ảnh 1 (Pic 1 - Chính)", type="filepath")
                    pic2_in = gr.Image(label="Ảnh 2 (Pic 2)", type="filepath")
                with gr.Row():
                    pic3_in = gr.Image(label="Ảnh 3 (Pic 3)", type="filepath")
                    pic4_in = gr.Image(label="Ảnh 4 (Pic 4)", type="filepath")
                with gr.Row():
                    bg_in   = gr.Image(label="Ảnh Bối cảnh (Background)", type="filepath")
                    start_frame_in = gr.Image(label="Ảnh Khung hình đầu (Start Frame - Tuỳ chọn)", type="filepath")

            # KHỐI ẢNH INGREDIENTS SHEET
            with gr.Group(visible=False) as ingredients_img_group:
                gr.Markdown("#### 🧪 Reference Sheet (Tất cả nhân vật, trang phục, bối cảnh trên 1 ảnh)")
                sheet_in = gr.Image(label="Tải lên bảng Reference Sheet", type="filepath")

            def _switch_mode(m):
                is_msr = "MSR" in m
                is_ing = "Ingredients" in m
                return (
                    gr.update(visible=is_msr),
                    gr.update(visible=is_ing),
                )
            mode_select.change(_switch_mode, inputs=mode_select, outputs=[msr_img_group, ingredients_img_group])

            # KHỐI PROMPT
            with gr.Group():
                prompt_relay_in = gr.Textbox(
                    label="📋 Mô tả nhân vật (Prompt Relay Tagging - Image 1, Image 2...)",
                    lines=3,
                    placeholder="Image 1 - Chàng trai áo denim đen...\nImage 2 - Cô gái áo len trắng...\nImage 4 - Scene, quán cafe cổ kính..."
                )
                scene_counter = gr.Markdown("🔹 **Số phân cảnh:** 0", elem_classes="scene-counter")
                prompt_main_in = gr.Textbox(
                    label="📝 Kịch bản phân cảnh (Mỗi đoạn cách nhau 1 dòng trống là 1 phân cảnh)",
                    lines=6,
                    placeholder="Cảnh quay toàn phòng khách, chàng trai ngồi giữa hai cô gái...\n\nCận cảnh cô gái bên trái bật cười và nói: 'Kể lại chuyện đó đi!'..."
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
                duration_in = gr.Slider(minimum=3, maximum=15, value=5, step=1, label="Thời lượng mỗi cảnh (giây)")
                fps_in      = gr.Slider(minimum=24, maximum=30, value=24, step=6, label="Tốc độ khung hình (24fps chuẩn điện ảnh)")

            with gr.Row():
                seed_in     = gr.Number(value=-1, label="Seed (-1 để ngẫu nhiên)", precision=0)
                segments_in = gr.Slider(minimum=1, maximum=10, value=1, step=1, label="Số phân cảnh lặp (nếu chỉ 1 prompt)")
                fixed_seed_in = gr.Checkbox(label="Cố định Seed cho mọi cảnh", value=False)

            with gr.Accordion("⚙️ Tùy chỉnh nâng cao & Bộ nhớ", open=False):
                cfg_in = gr.Slider(minimum=1.0, maximum=3.0, value=1.5, step=0.1, label="Video CFG Scale")
                msr_str_in = gr.Slider(minimum=0.1, maximum=1.0, value=0.7, step=0.05, label="MSR Reference Strength")
                ref_frames_in = gr.Dropdown(choices=["17", "33", "49"], value="33", label="Số Frame tham chiếu MSR")
                stage2_in  = gr.Checkbox(label="Chạy Stage 2 (x2 Spatial Upscale + Refiner)", value=True)
                lowvram_in = gr.Checkbox(label="Low VRAM Mode (Bật khi dùng GPU ≤16GB)", value=True)
                wrap_in    = gr.Checkbox(label="Tự động thêm tiền tố/hậu tố chất lượng điện ảnh", value=True)

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
            pic1_in, pic2_in, pic3_in, pic4_in, bg_in, start_frame_in, sheet_in,
            prompt_relay_in, prompt_main_in, neg_prompt_in,
            aspect_in, duration_in, fps_in, seed_in, segments_in, fixed_seed_in,
            cfg_in, msr_str_in, ref_frames_in, stage2_in, lowvram_in, wrap_in,
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

