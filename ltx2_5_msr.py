# @title [Cell MSR - CẬP NHẬT v3] LTX-2.5 MSR — Multi-Subject Reference Video
# Gan cell nay vao Colab de tao video tu nhieu anh tham khao nhan vat.
# Yeu cau: ComfyUI da cai san + Cell 1 (ban cap nhat v2, co cau hinh VRAM
# that + ghim phien ban custom node) da chay truoc.
#
# --- CẬP NHẬT SO VỚI BẢN TRƯỚC ---
# 1) Prompt Enhancer (tuỳ chọn, mặc định TẮT) — tái sử dụng model Gemma
#    nhẹ (gemma4_e2b_it_bf16) đã tải sẵn ở Cell 1. Khi bật, mỗi phân cảnh
#    sẽ được tự động mở rộng thành mô tả điện ảnh chi tiết hơn trước khi
#    đưa vào PromptRelayEncode, dùng Pic 1 làm ảnh tham chiếu nếu có.
# 2) Hiển thị công khai commit hash hiện tại của 2 custom node BÊN THỨ BA
#    (ComfyUI-LTX2.5-MSR, ComfyUI-PromptRelay), đọc từ
#    /content/ComfyUI/_node_versions.json do Cell 1 ghi ra.
# 3) (SỬA LỖI QUAN TRỌNG — VRAM) Bản trước gọi "Low VRAM Mode" nhưng chỉ
#    bật cờ --cache-none, cờ đó CHỈ tắt cache kết quả node, KHÔNG giảm
#    VRAM model — đây là lý do máy vẫn tràn VRAM dù đã bật, kể cả trên GPU
#    22-40GB. Bản này:
#      a) Đọc /content/ComfyUI/_vram_config.json do Cell 1 (bản cập nhật
#         v2) ghi ra, dùng đúng cờ THẬT của ComfyUI: --lowvram / --novram
#         + --reserve-vram (ép model stream trọng số qua RAM hệ thống
#         theo từng lớp, giảm thật sự VRAM đỉnh, đổi lại chậm hơn).
#      b) Thêm nút gọi API /free có sẵn của ComfyUI để chủ động giải
#         phóng model khỏi VRAM GIỮA MỖI PHÂN CẢNH — quan trọng khi chạy
#         chuỗi dài (vd 10 cảnh liên tiếp) để VRAM không tích tụ/phân
#         mảnh dần theo thời gian.
#      c) Chuyển VAEDecode ở Stage 1 sang VAEDecodeTiled — giảm đỉnh bộ
#         nhớ hoạt động (activation) khi decode nhiều khung hình cùng lúc.
#      d) Thêm tuỳ chọn "Restart server mỗi N cảnh" — khởi động lại hẳn
#         tiến trình ComfyUI định kỳ trong chuỗi dài, để dọn sạch VRAM /
#         tránh rò rỉ tích luỹ qua nhiều job liên tiếp.
#
# Custom nodes cần thiết:
#   - ComfyUI-LTX2.5-MSR   : https://github.com/liconstudio/ComfyUI-LTX2.5-MSR   (BÊN THỨ BA)
#   - ComfyUI-PromptRelay   : https://github.com/kijai/ComfyUI-PromptRelay        (BÊN THỨ BA)
#   - ComfyUI-KJNodes       : https://github.com/kijai/ComfyUI-KJNodes
#
# MSR LoRA đặt tại: /content/ComfyUI/models/loras/ltx2.5/

get_ipython().system("pip install -q gradio opencv-python")

import gc
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
import urllib.parse
import urllib.request
import gradio as gr

# ==========================================================================
# CẤU HÌNH
# ==========================================================================
INPUT_DIR  = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"
LORA_DIR   = "/content/ComfyUI/models/loras/"
MSR_LORA_SUBDIR = "ltx2.5"

UNET_FILENAME             = globals().get("UNET_FILENAME",             "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors")
TEXT_ENCODER_FILENAME     = globals().get("TEXT_ENCODER_FILENAME",     "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors")
VIDEO_VAE_FILENAME        = globals().get("VIDEO_VAE_FILENAME",        "ltx-2.5-video-vae-bf16.safetensors")
AUDIO_VAE_FILENAME        = globals().get("AUDIO_VAE_FILENAME",        "ltx-2.5-audio-vae-bf16.safetensors")
SPATIAL_UPSCALER_FILENAME = globals().get("SPATIAL_UPSCALER_FILENAME", "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors")
_raw_msr_lora             = globals().get("MSR_LORA_FILENAME",         "LTX-2.5-Licon-MSR-V1.safetensors")
MSR_LORA_REL_PATH         = _raw_msr_lora if ("/" in _raw_msr_lora or "\\" in _raw_msr_lora) else f"{MSR_LORA_SUBDIR}/{_raw_msr_lora}"
MSR_LORA_FILENAME         = MSR_LORA_REL_PATH
# Model Gemma nhẹ dùng cho Prompt Enhancer — đã được Cell 1 tải sẵn vào
# models/text_encoders/ (dùng chung với node TextGenerateLTX2Prompt của
# workflow I2V gốc), Cell MSR tái sử dụng, không cần tải thêm.
TEXT_ENHANCER_FILENAME    = globals().get("TEXT_ENCODER_ENHANCER_FILENAME", "gemma4_e2b_it_bf16.safetensors")

PASS2_FIXED_NOISE_SEED = 42
LATENT_GROUP_FRAMES    = 8

SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.85, 0.7250, 0.4219, 0.0"

NEGATIVE_PROMPT_DEFAULT = (
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, glitches, watermark, text, logo, subtitles, "
    "static frame, frozen image, standing still, lack of motion, ignored prompt, "
    "deformed limbs, extra paws, duplicate limbs, distorted face, inconsistent appearance, "
    "mid-shot camera cut, character switching, sudden transition"
)


def read_node_versions():
    """Đọc file version do Cell 1 ghi lại, để hiển thị công khai đang chạy
    commit nào cho 2 custom node BÊN THỨ BA (MSR, PromptRelay)."""
    path = "/content/ComfyUI/_node_versions.json"
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        data = {}
    msr_v = data.get("ComfyUI-LTX2.5-MSR", "?")
    relay_v = data.get("ComfyUI-PromptRelay", "?")
    return msr_v, relay_v


def read_vram_config():
    """(MỚI) Đọc cấu hình VRAM do Cell 1 (bản cập nhật v2) ghi ra, dùng làm
    mặc định khi khởi động ComfyUI server — thay cho cờ --cache-none dùng
    sai (không giảm VRAM model) ở bản trước."""
    path = "/content/ComfyUI/_vram_config.json"
    default = {"gpu_vram_gb": 22, "mode": "lowvram", "reserve_vram_gb": 1.5}
    try:
        with open(path) as f:
            data = json.load(f)
        default.update(data)
    except Exception:
        pass
    return default


def is_server_running(port=8188):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


_SERVER_STATE = {"running_vram_mode": None, "custom_nodes_mtime": None}
_VRAM_CONFIG_DEFAULT = read_vram_config()


def _get_custom_nodes_mtime():
    cn_dir = "/content/ComfyUI/custom_nodes"
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


def ensure_server(vram_mode_ui="auto", reserve_vram_gb=None, boot_timeout=300):
    """Khởi động (hoặc khởi động lại nếu cần) ComfyUI server với đúng cờ VRAM.

    (SỬA LỖI QUAN TRỌNG) Bản trước dùng --cache-none và gọi đó là "Low VRAM
    Mode" — cờ đó chỉ tắt cache KẾT QUẢ NODE, không liên quan tới VRAM
    model. Bản này dùng đúng cờ --lowvram / --novram của ComfyUI, ép model
    stream trọng số qua RAM hệ thống theo từng lớp khi tính toán, giảm
    thật sự VRAM đỉnh (đổi lại chậm hơn).

    vram_mode_ui: "auto" (dùng cấu hình từ Cell 1) | "novram" | "lowvram" | "normal"
    """
    resolved_mode = _VRAM_CONFIG_DEFAULT["mode"] if vram_mode_ui in (None, "auto") else vram_mode_ui
    resolved_reserve = reserve_vram_gb if reserve_vram_gb is not None else _VRAM_CONFIG_DEFAULT.get("reserve_vram_gb", 1.5)

    current_mtime = _get_custom_nodes_mtime()
    need_restart = (
        not is_server_running()
        or _SERVER_STATE["running_vram_mode"] != resolved_mode
        or _SERVER_STATE["custom_nodes_mtime"] != current_mtime
    )
    if not need_restart:
        return
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    os.chdir("/content/ComfyUI")
    
    server_env = os.environ.copy()
    server_env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,garbage_collection_threshold:0.8"

    # --cache-none: tắt cache KẾT QUẢ NODE
    # --preview-method none: tắt preview latent tốn VRAM/RAM khi render hàng loạt
    cmd = ["python", "main.py", "--cache-none", "--preview-method", "none", "--disable-auto-launch"]
    if resolved_mode == "novram":
        cmd.append("--novram")
    elif resolved_mode == "lowvram":
        cmd.append("--lowvram")
    # resolved_mode == "normal" -> không thêm cờ streaming, để ComfyUI tự quyết định
    if resolved_reserve:
        cmd += ["--reserve-vram", str(resolved_reserve)]

    subprocess.Popen(cmd, env=server_env)
    waited = 0
    while not is_server_running():
        time.sleep(2)
        waited += 2
        if waited > boot_timeout:
            raise RuntimeError(f"Server khong khoi dong duoc sau {boot_timeout}s.")
    _SERVER_STATE["running_vram_mode"] = resolved_mode
    _SERVER_STATE["custom_nodes_mtime"] = current_mtime


def force_restart_server():
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    _SERVER_STATE["running_vram_mode"] = None
    _SERVER_STATE["custom_nodes_mtime"] = None
    gc.collect()
    return "Server da tat. Lan tao video tiep theo se tu khoi dong lai."


def free_comfy_memory(unload_models=True, free_memory=True):
    """(MỚI) Gọi endpoint /free có sẵn của ComfyUI (giống nút 'Unload
    Models'/'Free memory' trên UI gốc) để chủ động giải phóng model khỏi
    VRAM giữa các job. Hữu ích khi chạy liên tiếp nhiều phân cảnh (vd 10
    cảnh) để tránh VRAM tích tụ/phân mảnh dần theo thời gian.
    Trả về False (không raise lỗi) nếu server không hỗ trợ endpoint này —
    an toàn để gọi "cho chắc" mà không làm gãy pipeline."""
    gc.collect()
    try:
        data = json.dumps({"unload_models": unload_models, "free_memory": free_memory}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8188/free", data=data, method="POST")
        urllib.request.urlopen(req, timeout=30)
        gc.collect()
        return True
    except Exception:
        return False


def snap_fps_safe(fps):
    try:
        fps = float(fps)
    except (TypeError, ValueError):
        fps = 24.0
    safe = int(round(fps / LATENT_GROUP_FRAMES) * LATENT_GROUP_FRAMES)
    return max(LATENT_GROUP_FRAMES, safe)


def half_dims(width, height):
    def snap_half_up(v):
        v = int(v)
        return max(32, int(math.ceil(v / 2.0 / 32.0)) * 32)
    return snap_half_up(width), snap_half_up(height)


def safe_dims(width, height):
    def snap_up(v):
        return max(256, int(math.ceil(int(v) / 32.0)) * 32)
    return snap_up(width), snap_up(height)


def get_seed(v_seed):
    try:
        v = int(v_seed)
    except Exception:
        v = -1
    return random.randint(1, 999_999_999) if v == -1 else v


def parse_aspect_ratio(ratio_str):
    if "480x832"  in ratio_str: return 480,  832
    if "832x480"  in ratio_str: return 832,  480
    if "1280x720" in ratio_str: return 1280, 720
    if "720x1280" in ratio_str: return 720,  1280
    if "720x720"  in ratio_str: return 720,  720
    return 512, 512


def list_msr_loras():
    msr_dir = os.path.join(LORA_DIR, MSR_LORA_SUBDIR)
    os.makedirs(msr_dir, exist_ok=True)
    files = sorted(
        f"{MSR_LORA_SUBDIR}/{f}"
        for f in os.listdir(msr_dir)
        if f.lower().endswith((".safetensors", ".pt", ".ckpt"))
    )
    return files if files else [MSR_LORA_REL_PATH]


def find_latest_video(output_dir=OUTPUT_DIR, min_mtime=None):
    """Tìm file video mới nhất trong output_dir và tất cả các thư mục con."""
    mp4_files = []
    exts = (".mp4", ".mkv", ".webm", ".mov")
    if os.path.exists(output_dir):
        for root, _, files in os.walk(output_dir):
            for f in files:
                if f.lower().endswith(exts):
                    p = os.path.join(root, f)
                    try:
                        mt = os.path.getmtime(p)
                        if min_mtime is None or mt >= (min_mtime - 10):
                            mp4_files.append((mt, p))
                    except OSError:
                        pass
    if not mp4_files and min_mtime is not None:
        return find_latest_video(output_dir=output_dir, min_mtime=None)
    if not mp4_files:
        return None
    mp4_files.sort(key=lambda x: x[0], reverse=True)
    return mp4_files[0][1]


def split_prompts(text):
    if not text or not text.strip():
        return []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n[ \t]*\n+", normalized.strip())
    return [b.strip() for b in blocks if b.strip()]


def count_scenes(text):
    n = len(split_prompts(text))
    return f"🔹 **Số phân cảnh nhận diện được:** {n}"


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


def submit_and_wait(workflow, scene_label="", max_wait_seconds=1800, poll_interval=2):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req  = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        response  = urllib.request.urlopen(req, timeout=30)
        prompt_id = json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = str(e)
        raise RuntimeError(f"ComfyUI từ chối workflow: {body[:800]}")
    except Exception as e:
        raise RuntimeError(f"Lỗi gửi job API: {e}")

    waited = 0
    history_url = f"http://127.0.0.1:8188/history/{prompt_id}"
    while waited < max_wait_seconds:
        try:
            history_resp = urllib.request.urlopen(urllib.request.Request(history_url), timeout=30)
            history = json.loads(history_resp.read().decode("utf-8"))

            if str(prompt_id) in history:
                job_data = history[str(prompt_id)]
                status_info = job_data.get("status", {})
                status_str = status_info.get("status_str", "")
                completed = status_info.get("completed", False)
                messages = status_info.get("messages", [])

                # Kiểm tra chi tiết lỗi từ các node của ComfyUI
                for msg in messages:
                    if isinstance(msg, (list, tuple)) and len(msg) >= 2 and msg[0] == "execution_error":
                        err_details = msg[1]
                        node_id = err_details.get("node_id", "?")
                        node_type = err_details.get("node_type", "?")
                        exc_msg = err_details.get("exception_message", "Unknown execution error")
                        exc_type = err_details.get("exception_type", "")
                        tb = "".join(err_details.get("traceback", []))
                        raise RuntimeError(
                            f"Render thất bại ở {scene_label} tại node [{node_id}] ({node_type}): {exc_type} - {exc_msg}\n{tb[:300]}"
                        )

                if status_str == "error" or (not completed and "outputs" not in job_data):
                    raise RuntimeError(f"ComfyUI báo lỗi không hoàn thành ở {scene_label}: {status_info}")

                # Tìm trực tiếp đường dẫn file video đầu ra từ outputs của ComfyUI
                outputs = job_data.get("outputs", {})
                for node_id, node_out in outputs.items():
                    for key in ("videos", "gifs", "images"):
                        for item in node_out.get(key, []):
                            fname = item.get("filename")
                            if fname and fname.lower().endswith((".mp4", ".mkv", ".webm", ".mov")):
                                subfolder = item.get("subfolder", "")
                                out_type = item.get("type", "output")
                                base_dir = "/content/ComfyUI/output" if out_type == "output" else "/content/ComfyUI/temp"
                                file_path = os.path.join(base_dir, subfolder, fname) if subfolder else os.path.join(base_dir, fname)
                                if os.path.exists(file_path):
                                    return file_path

                return prompt_id

            queue = json.loads(urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8188/queue"), timeout=30).read())
            is_running = any(
                str(job[1]) == str(prompt_id)
                for job in queue.get("queue_running", []) + queue.get("queue_pending", [])
            )
            if not is_running:
                time.sleep(1)
                hist_check = json.loads(urllib.request.urlopen(
                    urllib.request.Request(history_url), timeout=30).read())
                if str(prompt_id) in hist_check:
                    continue
                raise RuntimeError(f"Render thất bại ở {scene_label} (job không còn trong hàng đợi và không có output)")

        except RuntimeError:
            raise
        except Exception:
            pass

        time.sleep(poll_interval)
        waited += poll_interval

    raise RuntimeError(f"Timeout: {scene_label} quá {max_wait_seconds // 60} phút.")


# ==========================================================================
# BUILD WORKFLOW MSR
# ==========================================================================
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
    msr_strength=0.7,
    reference_frames="33",
    use_tiled_encode=False,
    tile_size=256,
    prompt_enhance=False,
    run_stage2=True,
):
    """Build workflow MSR 2-stage theo LTX2.5-MSR-sample-workflow.json kết hợp
    cơ chế LTXVDualCFGGuider từ ltx2_5.py giúp video tuân thủ cao theo Prompt.

    Stage 1: UNETLoader -> ComfyUILTX25MSRICLoRALoader
             (tuỳ chọn) Prompt Enhancer: CLIPLoader (gemma nhẹ) ->
             TextGenerateLTX2Prompt (dùng Pic 1 làm ảnh tham chiếu nếu có)
             PromptRelayEncode -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide
             LTXVDualCFGGuider (video_cfg / audio_cfg) -> SamplerCustomAdvanced
             -> VAEDecodeTiled (SỬA: trước là VAEDecode thường, giờ tiled để
             giảm đỉnh activation memory khi decode nhiều khung hình) -> SaveVideo (1/2 res)

    Stage 2: LTXVLatentUpsampler -> PromptRelayEncode (dùng lại prompt đã
             enhance ở Stage 1 nếu prompt_enhance=True, không chạy enhancer
             lần 2) -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide -> LTXVDualCFGGuider (video_cfg / audio_cfg)
             SamplerCustomAdvanced -> VAEDecodeTiled -> SaveVideo (full res)

    (GHI CHÚ VRAM) Với --lowvram/--novram bật đúng ở ensure_server(), model
    KHÔNG còn cần nằm trọn trong VRAM nữa (weights được stream theo lớp từ
    RAM), nên việc Prompt Enhancer nạp thêm 1 CLIP nhỏ (gemma4_e2b) song
    song với text encoder chính không còn là vấn đề nghiêm trọng như khi
    chạy --normalvram/--highvram mặc định.
    """
    if negative_text is None:
        negative_text = NEGATIVE_PROMPT_DEFAULT
    if msr_lora_name is None:
        msr_lora_name = MSR_LORA_FILENAME
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps       = snap_fps_safe(fps)
    half_w, half_h = half_dims(width, height)
    total_frames   = int(safe_fps * int(duration) + 1)

    pic_slot_map = [
        ("pic1",       pic1_name),
        ("pic2",       pic2_name),
        ("pic3",       pic3_name),
        ("pic4",       pic4_name),
        ("background", background_name),
    ]

    # ---- Prompt Enhancer — tuỳ chọn ----
    # Tái sử dụng model Gemma nhẹ (TEXT_ENHANCER_FILENAME) đã tải sẵn ở
    # Cell 1 để mở rộng prompt ngắn thành mô tả điện ảnh chi tiết hơn trước
    # khi đưa vào PromptRelayEncode, giống hệt node TextGenerateLTX2Prompt
    # (id 380) của workflow I2V gốc — chỉ khác ảnh tham chiếu dùng Pic 1
    # (nhân vật chính) thay vì first_frame, vì MSR không có 1 ảnh khởi đầu
    # duy nhất.
    enhancer_nodes = {}
    local_prompts_value = prompt_main
    if prompt_enhance:
        enhancer_nodes["S1_enh_clip"] = {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": TEXT_ENHANCER_FILENAME, "type": "ltxv", "device": "default"},
        }
        enh_inputs = {
            "clip":                             ["S1_enh_clip", 0],
            "prompt":                           prompt_main,
            "max_length":                       600,
            "sampling_mode":                    "on",
            "sampling_mode.temperature":        0.7,
            "sampling_mode.top_k":              64,
            "sampling_mode.top_p":              0.95,
            "sampling_mode.min_p":              0.05,
            "sampling_mode.repetition_penalty": 1.15,
            "sampling_mode.seed":               0,
            "temperature":                      0.7,
            "top_k":                            64,
            "top_p":                            0.95,
            "min_p":                            0.05,
            "repetition_penalty":               1.15,
            "seed":                             0,
        }
        if pic1_name:
            enh_inputs["image"] = ["S1_load_pic1", 0]
        enhancer_nodes["S1_enh_gen"] = {"class_type": "TextGenerateLTX2Prompt", "inputs": enh_inputs}
        local_prompts_value = ["S1_enh_gen", 0]

    # ---- Stage 1: Generation (half resolution) ----
    wf = {
        "S1_unet":  {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "S1_clip":  {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "S1_vvae":  {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "S1_avae":  {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},
        "S1_msr_loader": {
            "class_type": "ComfyUILTX25MSRICLoRALoader",
            "inputs": {"model": ["S1_unet", 0], "lora_name": msr_lora_name, "strength_model": float(msr_lora_strength)},
        },
        "S1_neg_enc":     {"class_type": "CLIPTextEncode", "inputs": {"clip": ["S1_clip", 0], "text": negative_text}},
        "S1_empty_vid":   {"class_type": "EmptyLTXVLatentVideo",  "inputs": {"width": int(half_w), "height": int(half_h), "length": int(total_frames), "batch_size": 1}},
        "S1_empty_aud":   {"class_type": "LTXVEmptyLatentAudio",  "inputs": {"audio_vae": ["S1_avae", 0], "frames_number": int(total_frames), "frame_rate": float(safe_fps), "batch_size": 1}},
        "S1_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model":           ["S1_msr_loader", 0],
                "clip":            ["S1_clip", 0],
                "latent":          ["S1_empty_vid", 0],
                "global_prompt":   prompt_relay_desc or "",
                "local_prompts":   local_prompts_value,
                "segment_lengths": "",
                "epsilon":         0.001,
            },
        },
    }
    wf.update(enhancer_nodes)
    wf["S1_ltxv_cond"] = {"class_type": "LTXVConditioning", "inputs": {"positive": ["S1_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": float(safe_fps)}}

    safe_msr_strength = min(1.0, max(0.0, float(msr_strength)))

    msr_s1 = {
        "positive": ["S1_ltxv_cond", 0], "negative": ["S1_ltxv_cond", 1],
        "vae": ["S1_vvae", 0], "latent": ["S1_empty_vid", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": safe_msr_strength, "reference_frames": reference_frames,
        "use_tiled_encode": use_tiled_encode, "tile_size": tile_size, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            wf[f"S1_load_{slot}"] = {"class_type": "LoadImage", "inputs": {"image": img}}
            msr_s1[slot] = [f"S1_load_{slot}", 0]
    wf["S1_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s1}

    wf.update({
        "S1_dual_guider": {"class_type": "LTXVDualCFGGuider",    "inputs": {"model": ["S1_relay", 0], "positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S1_noise":       {"class_type": "RandomNoise",          "inputs": {"noise_seed": int(seed)}},
        "S1_sampler_sel": {"class_type": "KSamplerSelect",       "inputs": {"sampler_name": "euler_ancestral"}},
        "S1_sigmas":      {"class_type": "ManualSigmas",         "inputs": {"sigmas": SIGMAS_PASS1}},
        "S1_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S1_msr_guide", 2], "audio_latent": ["S1_empty_aud", 0]}},
        "S1_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S1_noise", 0], "guider": ["S1_dual_guider", 0], "sampler": ["S1_sampler_sel", 0], "sigmas": ["S1_sigmas", 0], "latent_image": ["S1_concat_av", 0]}},
        "S1_sep_av":      {"class_type": "LTXVSeparateAVLatent",  "inputs": {"av_latent": ["S1_sample", 0]}},
        "S1_crop_guides": {"class_type": "LTXVCropGuides",       "inputs": {"positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "latent": ["S1_sep_av", 0]}},
        # (SỬA — VRAM) VAEDecode thường -> VAEDecodeTiled: giảm đỉnh bộ nhớ
        # hoạt động khi decode toàn bộ total_frames cùng lúc ở nửa độ phân giải.
        "S1_vae_decode":  {"class_type": "VAEDecodeTiled",       "inputs": {"samples": ["S1_crop_guides", 2], "vae": ["S1_vvae", 0], "tile_size": 256, "overlap": 32, "temporal_size": 32, "temporal_overlap": 8}},
        "S1_aud_decode":  {"class_type": "LTXVAudioVAEDecode",   "inputs": {"samples": ["S1_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S1_create_vid":  {"class_type": "CreateVideo",           "inputs": {"images": ["S1_vae_decode", 0], "audio": ["S1_aud_decode", 0], "fps": float(safe_fps)}},
        "S1_save":        {"class_type": "SaveVideo",             "inputs": {"video": ["S1_create_vid", 0], "filename_prefix": "LTX25_MSR_Stage1", "format": "auto", "codec": "auto"}},
    })

    if not run_stage2:
        return wf

    # ---- Stage 2: Latent x2 Upscale + Refinement (full resolution) ----
    wf.update({
        "S2_upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "S2_upsampler":      {"class_type": "LTXVLatentUpsampler",       "inputs": {"samples": ["S1_crop_guides", 2], "upscale_model": ["S2_upscale_loader", 0], "vae": ["S1_vvae", 0]}},
        "S2_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model":           ["S1_msr_loader", 0],
                "clip":            ["S1_clip", 0],
                "latent":          ["S2_upsampler", 0],
                "global_prompt":   prompt_relay_desc or "",
                # Dùng lại đúng prompt (đã enhance nếu prompt_enhance=True)
                # của Stage 1, KHÔNG chạy lại enhancer lần 2 — giữ mô tả
                # chuyển động nhất quán giữa 2 pass và tiết kiệm 1 lượt
                # inference của model Gemma.
                "local_prompts":   local_prompts_value,
                "segment_lengths": "",
                "epsilon":         0.001,
            },
        },
    })

    stage2_seed = (int(seed) + 1000) if seed is not None else 42
    stage2_msr_strength = min(0.6, safe_msr_strength * 0.8)

    msr_s2 = {
        "positive": ["S2_relay", 1], "negative": ["S1_neg_enc", 0],
        "vae": ["S1_vvae", 0], "latent": ["S2_upsampler", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": stage2_msr_strength, "reference_frames": reference_frames,
        "use_tiled_encode": use_tiled_encode, "tile_size": tile_size, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            msr_s2[slot] = [f"S1_load_{slot}", 0]
    wf["S2_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s2}

    wf.update({
        "S2_ltxv_cond":   {"class_type": "LTXVConditioning",      "inputs": {"positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "frame_rate": float(safe_fps)}},
        "S2_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S2_msr_guide", 2], "audio_latent": ["S1_sep_av", 1]}},
        "S2_dual_guider": {"class_type": "LTXVDualCFGGuider",    "inputs": {"model": ["S2_relay", 0], "positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S2_noise":       {"class_type": "RandomNoise",           "inputs": {"noise_seed": stage2_seed}},
        "S2_sampler_sel": {"class_type": "KSamplerSelect",        "inputs": {"sampler_name": "euler_ancestral"}},
        "S2_sigmas":      {"class_type": "ManualSigmas",          "inputs": {"sigmas": SIGMAS_PASS2}},
        "S2_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S2_noise", 0], "guider": ["S2_dual_guider", 0], "sampler": ["S2_sampler_sel", 0], "sigmas": ["S2_sigmas", 0], "latent_image": ["S2_concat_av", 0]}},
        "S2_sep_av":      {"class_type": "LTXVSeparateAVLatent",  "inputs": {"av_latent": ["S2_sample", 0]}},
        "S2_crop_guides": {"class_type": "LTXVCropGuides",        "inputs": {"positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1], "latent": ["S2_sep_av", 0]}},
        "S2_vae_tiled":   {"class_type": "VAEDecodeTiled",        "inputs": {"samples": ["S2_crop_guides", 2], "vae": ["S1_vvae", 0], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "S2_aud_decode":  {"class_type": "LTXVAudioVAEDecode",   "inputs": {"samples": ["S2_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S2_create_vid":  {"class_type": "CreateVideo",           "inputs": {"images": ["S2_vae_tiled", 0], "audio": ["S2_aud_decode", 0], "fps": float(safe_fps)}},
        "S2_save":        {"class_type": "SaveVideo",             "inputs": {"video": ["S2_create_vid", 0], "filename_prefix": "LTX25_MSR_DualStage", "format": "auto", "codec": "auto"}},
    })

    return wf


# ==========================================================================
# GENERATE — HÀM GRADIO GENERATOR
# ==========================================================================
def generate_msr_gradio(
    pic1_path, pic2_path, pic3_path, pic4_path, background_path,
    prompt_relay_desc, prompt_main, negative_text,
    aspect_ratio, v_length, v_fps, v_seed, num_segments, fixed_seed,
    video_cfg, msr_lora_name, msr_lora_strength, msr_strength,
    reference_frames, use_tiled_encode,
    prompt_enhance,
    run_stage2,
    vram_mode_ui, reserve_vram_ui, free_mem_between_scenes, restart_every_n,
):
    if not pic1_path:
        yield None, None, "⚠️ Dạ anh vui lòng tải ít nhất ảnh Pic 1 (bắt buộc) giúp em nha!"; return

    prompts = split_prompts(prompt_main)
    if not prompts:
        yield None, None, "⚠️ Dạ anh nhập giúp em ít nhất 1 dòng kịch bản (prompt) nha!"; return

    v_width, v_height       = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

    yield None, None, "🔄 Đang kiểm tra / khởi động ComfyUI server..."
    try:
        ensure_server(vram_mode_ui, reserve_vram_ui)
    except Exception as e:
        yield None, None, f"❌ {e}"; return

    base_seed = get_seed(v_seed)
    os.makedirs(INPUT_DIR, exist_ok=True)

    def _copy_img(path, slot_name):
        if not path:
            return None
        ext  = os.path.splitext(path)[1].lower() or ".png"
        name = f"msr_{slot_name}_{int(time.time())}{ext}"
        shutil.copy(path, os.path.join(INPUT_DIR, name))
        return name

    pic1_name = _copy_img(pic1_path,       "pic1")
    pic2_name = _copy_img(pic2_path,       "pic2")
    pic3_name = _copy_img(pic3_path,       "pic3")
    pic4_name = _copy_img(pic4_path,       "pic4")
    bg_name   = _copy_img(background_path, "background")

    loaded = [s for s in [pic1_name, pic2_name, pic3_name, pic4_name, bg_name] if s]

    # Quyết định danh sách phân cảnh chạy
    if len(prompts) > 1:
        scene_prompts = prompts
    else:
        num_segments = max(1, int(num_segments))
        scene_prompts = [prompts[0]] * num_segments

    total_scenes = len(scene_prompts)
    total_seconds = total_scenes * int(v_length)
    stage_note = "Stage 1 + Stage 2 (upscale x2)" if run_stage2 else "Stage 1 only (preview)"
    enhance_note = "✨ Prompt Enhancer: BẬT" if prompt_enhance else "Prompt Enhancer: tắt"
    resolved_mode = _VRAM_CONFIG_DEFAULT["mode"] if vram_mode_ui == "auto" else vram_mode_ui
    vram_note = f"🧠 VRAM: --{resolved_mode} (reserve {reserve_vram_ui}GB)"

    yield None, None, (
        f"✅ Server sẵn sàng. Bắt đầu tạo chuỗi {total_scenes} phân cảnh MSR (tổng {total_seconds}s)...\n"
        f"📸 Ảnh tham khảo: {len(loaded)} slot · Chế độ: {stage_note} · {enhance_note} · {vram_note}\n"
        f"Base Seed: {base_seed} · Video CFG: {video_cfg}"
    )

    generated_videos = []
    for i, p in enumerate(scene_prompts):
        label = f"phân cảnh {i + 1}/{total_scenes}"
        seed_i = base_seed if fixed_seed else (base_seed + i)

        # (MỚI) Restart server định kỳ trong chuỗi dài để dọn sạch VRAM /
        # tránh tích luỹ phân mảnh qua nhiều job liên tiếp. Chỉ áp dụng
        # TRƯỚC khi bắt đầu 1 cảnh mới (không cắt ngang cảnh đang chạy).
        if restart_every_n and int(restart_every_n) > 0 and i > 0 and i % int(restart_every_n) == 0:
            yield generated_videos, None, f"🔄 Restart định kỳ ComfyUI server trước {label} (mỗi {int(restart_every_n)} cảnh)..."
            force_restart_server()
            try:
                ensure_server(vram_mode_ui, reserve_vram_ui)
            except Exception as e:
                yield generated_videos, None, f"❌ {e}"; return

        yield generated_videos, None, (
            f"🔄 Đang quay {label} [{stage_note}]... (Seed: {seed_i})\n"
            f"📝 Nội dung: {p[:120]}..."
        )

        wf = build_msr_workflow(
            prompt_relay_desc = prompt_relay_desc or "",
            prompt_main       = p,
            negative_text     = negative_text or NEGATIVE_PROMPT_DEFAULT,
            width             = safe_width,
            height            = safe_height,
            fps               = v_fps,
            duration          = v_length,
            seed              = seed_i,
            video_cfg         = float(video_cfg or 1.5),
            msr_lora_name     = msr_lora_name,
            msr_lora_strength = msr_lora_strength,
            pic1_name         = pic1_name,
            pic2_name         = pic2_name,
            pic3_name         = pic3_name,
            pic4_name         = pic4_name,
            background_name   = bg_name,
            msr_strength      = msr_strength,
            reference_frames  = str(reference_frames),
            use_tiled_encode  = bool(use_tiled_encode),
            prompt_enhance    = bool(prompt_enhance),
            run_stage2        = bool(run_stage2),
        )

        job_t0 = time.time()
        try:
            res_video = submit_and_wait(wf, scene_label=label)
        except Exception as e:
            yield generated_videos, None, f"❌ {e}"; return

        if isinstance(res_video, str) and os.path.exists(res_video) and not res_video.isdigit():
            latest_video = res_video
        else:
            latest_video = find_latest_video(min_mtime=job_t0)

        if not latest_video or not os.path.exists(latest_video):
            yield generated_videos, None, (
                f"⚠️ Không tìm thấy file video ở {label}!\n"
                f"Kiểm tra lại log ComfyUI server trong terminal để xem chi tiết lỗi."
            )
            return

        generated_videos.append(latest_video)

        # (MỚI) Giải phóng VRAM giữa mỗi phân cảnh — quan trọng cho chuỗi
        # dài (vd 10 cảnh) để tránh VRAM tích tụ/phân mảnh dần theo thời gian.
        freed_note = ""
        if free_mem_between_scenes:
            ok = free_comfy_memory()
            freed_note = " · 🧹 đã gọi /free" if ok else " · ⚠️ /free không khả dụng (bỏ qua)"

        yield generated_videos, None, f"🔔 [DING] ✅ Xong {label} ({i + 1}/{total_scenes}){freed_note}!"

    # Ghép nối các phân cảnh thành 1 video dài hoàn chỉnh
    if len(generated_videos) > 1:
        yield generated_videos, None, "🔄 Đang tiến hành ghép nối các phân cảnh bằng ffmpeg..."
        try:
            final_output = concat_videos(generated_videos, "final_long_msr_video")
        except Exception as e:
            yield generated_videos, generated_videos[-1], f"⚠️ {e}"; return
        yield generated_videos, final_output, (
            f"🔔 [DING] 🎉 Hoàn tất toàn bộ phim MSR ({total_seconds}s, {total_scenes} phân cảnh)! Base Seed: {base_seed}"
        )
    elif len(generated_videos) == 1:
        yield generated_videos, generated_videos[0], (
            f"🔔 [DING] 🎉 Render Complete! Đã tạo xong video ({v_length}s). (Seed: {base_seed})"
        )


# ==========================================================================
# GRADIO UI
# ==========================================================================
ratio_choices = [
    "16:9 (1280x720) · HD 720p Ngang",
    "9:16 (720x1280) · HD 720p Dọc",
    "1:1 (720x720) · HD 720p Vuông",
    "16:9 (832x480) · Nhẹ / Tiết kiệm VRAM",
    "9:16 (480x832) · Nhẹ / Tiết kiệm VRAM",
]

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.gradio-container { font-family: 'Inter', sans-serif !important; max-width: 1560px; margin: 0 auto; }
#msr-header { background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
              border-radius:16px; padding:20px 26px; margin-bottom:14px; box-shadow: 0 6px 20px rgba(124,58,237,.28); }
#msr-header h1, #msr-header p { color:#fff !important; margin:0 !important; }
.info-box { background:rgba(99,102,241,.08); border-left:3px solid #6366f1;
            padding:10px 14px; border-radius:8px; font-size:.87rem;
            margin-bottom:8px; }
.scene-counter { display: inline-block; background: rgba(99, 102, 241, 0.12); padding: 6px 14px; border-radius: 999px; font-weight: 600 !important; font-size: 0.85rem !important; margin: 2px 0 6px 0 !important; }
.scene-counter p { margin: 0 !important; color: #4f46e5 !important; }
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

# Đọc phiên bản 2 custom node bên thứ ba (ghi ra bởi Cell 1) để hiển thị
# công khai trên header, cùng cấu hình VRAM đang dùng.
_msr_node_v, _relay_node_v = read_node_versions()
_vram_cfg = read_vram_config()

custom_theme = gr.themes.Soft(primary_hue="violet", secondary_hue="purple", neutral_hue="slate")

with gr.Blocks(
    title="LTX-2.5 MSR Studio",
    fill_width=True,
) as demo:

    with gr.Column(elem_id="msr-header"):
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown(
                    f"""
                    # 🎬 LTX-2.5 MSR Studio (Tạo Video Dài Tự Động)
                    Multi-Subject Reference — Tạo phim dài nhiều phân cảnh từ ảnh tham khảo nhân vật & bối cảnh

                    <div style="margin-top:4px; opacity:0.9; font-size:0.9rem;">
                    ⚡ LTX-2.5 · 🎭 Tối đa 4 nhân vật + 1 bối cảnh · 🎞️ Tự động render chuỗi kịch bản & ghép nối hoàn chỉnh bằng ffmpeg
                    </div>
                    <div style="margin-top:6px; opacity:0.75; font-size:0.78rem;">
                    🔧 Custom node bên thứ ba (chưa phải node lõi ComfyUI/Lightricks) đang chạy:
                    ComfyUI-LTX2.5-MSR@{_msr_node_v} · ComfyUI-PromptRelay@{_relay_node_v}
                    — ghim/cập nhật ở Cell 1 (biến MSR_NODE_PIN / PROMPT_RELAY_PIN).
                    </div>
                    <div style="margin-top:4px; opacity:0.75; font-size:0.78rem;">
                    🧠 VRAM mặc định từ Cell 1: --{_vram_cfg['mode']} cho GPU {_vram_cfg['gpu_vram_gb']}GB
                    (reserve {_vram_cfg['reserve_vram_gb']}GB) — cờ THẬT, khác --cache-none của bản trước.
                    </div>
                    """
                )
            with gr.Column(scale=1, min_width=160):
                restart_btn = gr.Button("🔄 Restart Server", size="sm")
                restart_out = gr.Markdown("🟢 Sẵn sàng")
        restart_btn.click(fn=force_restart_server, outputs=[restart_out])

    with gr.Row():
        # --- CỘT TRÁI: INPUTS ---
        with gr.Column(scale=5):

            with gr.Group():
                gr.Markdown("### 📸 Ảnh tham khảo nhân vật / bối cảnh")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Thứ tự slot cố định: <b>Pic 1 → Pic 2 → Pic 3 → Pic 4 → Background</b>. "
                    "Chỉ <b>Pic 1</b> bắt buộc, các slot còn lại tuỳ chọn. "
                    "Slot ID và learned embeddings được giữ nguyên cho tất cả các phân cảnh."
                    "</div>"
                )
                with gr.Row():
                    msr_pic1 = gr.Image(label="🎭 Pic 1 - Nhân vật 1 (bắt buộc)", type="filepath")
                    msr_pic2 = gr.Image(label="🎭 Pic 2 - Nhân vật 2 (tuỳ chọn)", type="filepath")
                with gr.Row():
                    msr_pic3 = gr.Image(label="🎭 Pic 3 - Nhân vật 3 (tuỳ chọn)", type="filepath")
                    msr_pic4 = gr.Image(label="🎭 Pic 4 - Nhân vật 4 (tuỳ chọn)", type="filepath")
                msr_bg = gr.Image(label="🌄 Background - Bối cảnh (tuỳ chọn)", type="filepath")

            with gr.Group():
                gr.Markdown("### 📝 Kịch bản & Prompt")
                gr.Markdown(
                    "<div class='info-box'>"
                    "① <b>Mô tả nhân vật</b>: mô tả ngoại hình từng nhân vật (<code>Image 1:... Image 2:...</code>)<br>"
                    "② <b>Kịch bản phim</b>: có thể nhập nhiều phân cảnh (mỗi cảnh cách nhau 1 dòng trống ~ 2 lần Enter). "
                    "Hệ thống sẽ tự động quay lần lượt từng cảnh 10s rồi tự ghép nối thành phim dài 30s, 60s!"
                    "</div>"
                )
                msr_relay_desc = gr.Textbox(
                    label="① Mô tả nhân vật (character_description)",
                    lines=4,
                    placeholder=(
                        "Image 1: A real chubby orange tabby cat with fluffy ginger fur, wearing a miniature chef hat...\n\n"
                        "Image 2: A real cute Corgi puppy wearing a red bandana...\n\n"
                        "Image 3: A real curious raccoon holding a small wooden spoon..."
                    ),
                )
                scene_count_display = gr.Markdown("🔹 **Số phân cảnh nhận diện được:** 0", elem_classes="scene-counter")
                msr_prompt = gr.Textbox(
                    label="② Kịch bản / Prompt chính (mỗi phân cảnh cách nhau 1 dòng trống)",
                    lines=6,
                    placeholder=(
                        "[Shot 1] The orange cat gestures with a wooden spoon atop the counter...\n\n"
                        "[Shot 2] The refrigerator door opens, the corgi puppy slips on the floor and slides...\n\n"
                        "[Shot 3] All animals feast on cake, the light clicks on and they freeze staring at camera..."
                    ),
                )
                msr_neg = gr.Textbox(
                    label="🚫 Negative Prompt",
                    lines=2,
                    value=NEGATIVE_PROMPT_DEFAULT,
                )

            with gr.Accordion("⚙️ Cài đặt nâng cao", open=False):
                gr.Markdown("**📐 Kích thước & thời lượng**")
                ratio_msr = gr.Radio(
                    label="Tỉ lệ khung hình",
                    choices=ratio_choices,
                    value=ratio_choices[0],
                    info="Stage 1 chạy ½ res, Stage 2 upscale x2 về full res",
                )
                with gr.Row():
                    length_msr = gr.Slider(label="⏱️ Thời lượng MỖI cảnh (giây)", minimum=1, maximum=10, step=1, value=10)
                    fps_msr    = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24)

                with gr.Row():
                    seed_msr = gr.Number(label="🎲 Seed (-1 = ngẫu nhiên)", value=-1, precision=0)
                    num_segments_msr = gr.Slider(
                        label="🔢 Số phân đoạn (khi chỉ có 1 prompt)",
                        minimum=1, maximum=10, step=1, value=1,
                        info="Chỉ áp dụng nếu ô kịch bản chỉ có 1 prompt đơn"
                    )
                fixed_seed_msr = gr.Checkbox(label="🔗 Dùng chung 1 Seed cho mọi phân cảnh", value=False)

                gr.Markdown("**🧬 MSR LoRA**")
                with gr.Row():
                    _msr_choices = list_msr_loras()
                    _msr_default = _msr_choices[0] if _msr_choices else MSR_LORA_REL_PATH
                    msr_lora_dd = gr.Dropdown(
                        label="MSR LoRA",
                        choices=_msr_choices,
                        value=_msr_default,
                        allow_custom_value=True,
                        scale=3,
                    )
                    msr_lora_str_sl = gr.Slider(
                        label="LoRA strength", minimum=0.0, maximum=2.0, step=0.05, value=0.85, scale=2,
                        info="0.85 = cân bằng hoàn hảo giữa nhận diện nhân vật & độ tự do chuyển động")
                msr_refresh_btn = gr.Button("🔄 Refresh MSR LoRA", size="sm")
                msr_refresh_btn.click(
                    fn=lambda: gr.update(
                        choices=list_msr_loras(),
                        value=list_msr_loras()[0] if list_msr_loras() else MSR_LORA_REL_PATH,
                    ),
                    outputs=[msr_lora_dd],
                )

                gr.Markdown("**🎯 Cài đặt MSR Guide & Độ Tuân Thủ Prompt**")
                with gr.Row():
                    msr_video_cfg = gr.Slider(
                        label="🎯 Video CFG (Độ tuân thủ Prompt)", minimum=1.0, maximum=3.5, step=0.1, value=1.5,
                        info="Khuyến nghị 1.5 – 2.0 để AI bám sát hành động trong kịch bản", scale=1)
                    msr_guide_str_sl = gr.Slider(
                        label="Reference strength", minimum=0.0, maximum=1.0, step=0.05, value=0.7,
                        info="Độ bám ảnh tham khảo — 0.7 chuẩn nhất (giữ nhân vật & chuyển động mượt)", scale=1)
                with gr.Row():
                    msr_ref_frames = gr.Radio(
                        label="Reference frames", choices=["25", "33"], value="33",
                        info="33 = mặc định MSR chính thức")
                    msr_tiled = gr.Checkbox(label="Tiled VAE encode (khuyến nghị BẬT chống tràn VRAM)", value=True)

                gr.Markdown("**⚙️ Pipeline**")
                with gr.Row():
                    msr_stage2   = gr.Checkbox(label="✅ Chạy Stage 2 (upscale x2 + refine)", value=True)
                with gr.Row():
                    msr_prompt_enhance = gr.Checkbox(
                        label="✨ Prompt Enhancer",
                        value=False,
                        info="Dùng model Gemma nhẹ (gemma4_e2b_it_bf16, đã tải sẵn ở Cell 1) để tự mở rộng "
                             "mỗi phân cảnh ngắn thành mô tả điện ảnh chi tiết hơn trước khi render. "
                             "An toàn dùng cùng GPU 22GB MIỄN LÀ chế độ VRAM bên dưới đang là "
                             "'lowvram'/'novram' (model sẽ stream qua RAM thay vì cần full VRAM).",
                    )

                gr.Markdown("**🧠 Quản lý VRAM (cho GPU nhỏ / chạy nhiều cảnh liên tiếp)**")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Đây là cờ VRAM THẬT của ComfyUI (khác <code>--cache-none</code> của bản trước, "
                    "vốn chỉ tắt cache kết quả node chứ không giảm VRAM model)."
                    "</div>"
                )
                with gr.Row():
                    msr_vram_mode = gr.Radio(
                        label="Chế độ VRAM",
                        choices=["auto", "novram", "lowvram", "normal"],
                        value="auto",
                        info=f"'auto' = theo Cell 1 (hiện tại: --{_vram_cfg['mode']}). Với GPU 22GB, khuyến nghị 'lowvram'.",
                    )
                    msr_reserve_vram = gr.Slider(
                        label="Reserve VRAM (GB)", minimum=0.0, maximum=6.0, step=0.5,
                        value=float(_vram_cfg.get("reserve_vram_gb", 2.0)),
                        info="Chừa thêm bộ nhớ đệm cho hoạt động ngoài model — tăng lên nếu vẫn OOM.",
                    )
                with gr.Row():
                    msr_free_between = gr.Checkbox(
                        label="🧹 Giải phóng VRAM giữa mỗi phân cảnh (khuyến nghị BẬT cho ≥5 cảnh)",
                        value=True,
                        info="Gọi API /free của ComfyUI sau mỗi cảnh để tránh VRAM tích tụ/phân mảnh dần.",
                    )
                    msr_restart_every = gr.Slider(
                        label="🔄 Restart server mỗi N cảnh (0 = tắt)",
                        minimum=0, maximum=10, step=1, value=2,
                        info="Khởi động lại ComfyUI định kỳ mỗi 2 cảnh (chỉ mất ~3s) để dọn sạch 100% rác VRAM & RAM khi quay chuỗi 10 cảnh.",
                    )

        # --- CỘT PHẢI: OUTPUTS ---
        with gr.Column(scale=5):
            with gr.Group():
                gallery_msr = gr.Gallery(label="🎥 Các Phân Cảnh Lẻ (Shot 1, Shot 2...)", columns=2, height="auto")
                video_out_msr = gr.Video(label="🎬 Phim Dài Hoàn Chỉnh (Ghép Nối Liền Mạch)")
                with gr.Row():
                    msr_btn   = gr.Button("🎬 Bắt Đầu Tạo Phim MSR", variant="primary", scale=3)
                    msr_clear = gr.Button("🗑️ Clear", scale=1)
                msr_status = gr.Textbox(
                    label="ℹ️ Status / Tiến trình", interactive=False, lines=5, elem_classes="status-box")

            gr.Markdown(
                "<div class='info-box'>"
                "<b>💡 Hướng dẫn tạo phim 30s–60s / chuỗi 10 cảnh:</b><br>"
                "• Bạn dán toàn bộ các phân đoạn trong kịch bản vào ô prompt (cách nhau 2 lần Enter).<br>"
                "• Nhấn <b>Bắt Đầu Tạo Phim MSR</b>: hệ thống tự động chạy lần lượt từng cảnh rồi tự ghép "
                "lại thành 1 video hoàn chỉnh!<br>"
                "• Với GPU 22GB và ≥5 cảnh: giữ 'Chế độ VRAM' = lowvram (hoặc auto nếu Cell 1 đã set 22GB), "
                "bật 'Giải phóng VRAM giữa mỗi phân cảnh', và đặt 'Restart mỗi N cảnh' ~5 để chạy ổn định "
                "cho 10 cảnh liên tiếp — đổi lại tốc độ sẽ chậm hơn GPU 40GB+."
                "</div>"
            )

    msr_prompt.change(fn=count_scenes, inputs=[msr_prompt], outputs=[scene_count_display])

    msr_btn.click(
        fn=generate_msr_gradio,
        inputs=[
            msr_pic1, msr_pic2, msr_pic3, msr_pic4, msr_bg,
            msr_relay_desc, msr_prompt, msr_neg,
            ratio_msr, length_msr, fps_msr, seed_msr, num_segments_msr, fixed_seed_msr,
            msr_video_cfg, msr_lora_dd, msr_lora_str_sl, msr_guide_str_sl,
            msr_ref_frames, msr_tiled,
            msr_prompt_enhance,
            msr_stage2,
            msr_vram_mode, msr_reserve_vram, msr_free_between, msr_restart_every,
        ],
        outputs=[gallery_msr, video_out_msr, msr_status],
    )
    msr_clear.click(
        fn=lambda: (None, None, "", "🔹 **Số phân cảnh nhận diện được:** 0"),
        outputs=[gallery_msr, video_out_msr, msr_status, scene_count_display],
    )

demo.queue()
try:
    demo.launch(
        theme=custom_theme,
        css=custom_css,
        js=notification_js,
        share=True,
        inline=False,
        debug=True,
    )
except TypeError:
    demo.launch(share=True, inline=False, debug=True)