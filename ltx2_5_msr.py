# @title [Cell MSR] LTX-2.5 MSR — Multi-Subject Reference Video
# Gan cell nay vao Colab de tao video tu nhieu anh tham khao nhan vat.
# Yeu cau: ComfyUI da cai san + Cell 1 (setup model) da chay truoc.
#
# Custom nodes can thiet:
#   - ComfyUI-LTX2.5-MSR   : https://github.com/liconstudio/ComfyUI-LTX2.5-MSR
#   - ComfyUI-PromptRelay   : https://github.com/kijai/ComfyUI-PromptRelay
#   - ComfyUI-KJNodes       : https://github.com/kijai/ComfyUI-KJNodes
#
# MSR LoRA dat tai: /content/ComfyUI/models/loras/ltx2.5/

get_ipython().system("pip install -q gradio opencv-python")

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
import json

# ==========================================================================
# CAU HINH
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
MSR_LORA_FILENAME         = globals().get("MSR_LORA_FILENAME",         "ltx2.5/LTX-2.5-Licon-MSR-V1.safetensors")

PASS2_FIXED_NOISE_SEED = 42
LATENT_GROUP_FRAMES    = 8

# Stage 1: 9 bước — thêm trung gian 0.80 & 0.65 giúp texture và chuyển động mượt hơn
SIGMAS_PASS1 = "1.0, 0.994, 0.985, 0.975, 0.95, 0.90, 0.80, 0.65, 0.421875, 0.0"
# Stage 2: 4 bước refine — thêm 0.55 cho vùng mid-frequency tốt hơn
SIGMAS_PASS2 = "0.85, 0.72, 0.55, 0.30, 0.0"

# Quality prefix & suffix tự động thêm vào prompt (bật/tắt qua UI)
QUALITY_PREFIX = (
    "Cinematic 4K ultra-detailed, sharp focus, professional cinematography, "
    "high dynamic range lighting, photorealistic texture, "
)
QUALITY_SUFFIX = (
    ", natural fluid motion, temporal coherence, consistent character identity, "
    "smooth camera movement, fine detail preservation"
)

NEGATIVE_PROMPT_DEFAULT = (
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, glitches, watermark, text, logo, subtitles, "
    "static frame, frozen image, standing still, lack of motion, "
    "deformed limbs, extra paws, duplicate limbs, distorted face, "
    "character switching, sudden character change, wrong character, inconsistent character identity, "
    "different person, different animal, character replacement, morphing face, "
    "mid-shot camera cut, sudden transition, ignored prompt, "
    "temporal inconsistency, jittery motion, flickering texture, strobing, "
    "bad anatomy, clipping, floating limbs, melting body"
)


def is_server_running(port=8188):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


COMFYUI_LOG_PATH = "/content/comfyui.log"
_SERVER_STATE = {"running_low_vram": None, "custom_nodes_mtime": None}


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


def ensure_server(low_vram, boot_timeout=120):
    """Đảm bảo ComfyUI server đang chạy. Bắt crash ngay qua log thay vì đợi timeout."""
    current_mtime = _get_custom_nodes_mtime()
    need_restart = (
        not is_server_running()
        or _SERVER_STATE["running_low_vram"] != low_vram
        or _SERVER_STATE["custom_nodes_mtime"] != current_mtime
    )
    if not need_restart:
        return

    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    import time as _time; _time.sleep(2)

    os.chdir("/content/ComfyUI")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
        "expandable_segments:True,"
        "max_split_size_mb:512,"
        "garbage_collection_threshold:0.8"
    )
    log_out = open(COMFYUI_LOG_PATH, "w", encoding="utf-8", errors="ignore")

    cmd = ["python", "-u", "main.py", "--listen", "127.0.0.1", "--port", "8188", "--fast"]
    if low_vram:
        cmd += ["--lowvram", "--cache-none"]

    import subprocess as _sp
    proc = _sp.Popen(cmd, cwd="/content/ComfyUI", stdout=log_out, stderr=_sp.STDOUT)

    waited = 0
    poll_interval = 2
    while not is_server_running():
        _time.sleep(poll_interval)
        waited += poll_interval
        # Bắt crash ngay — không chờ timeout!
        ret = proc.poll()
        if ret is not None:
            log_out.flush(); log_out.close()
            tail = ""
            try:
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    tail = "".join(f.readlines()[-35:])
            except Exception:
                tail = "Không đọc được log."
            raise RuntimeError(
                f"❌ ComfyUI crash khi khởi động (Exit code: {ret})!\n"
                f"Chi tiết log:\n{'-'*50}\n{tail}\n{'-'*50}"
            )
        if waited > boot_timeout:
            log_out.flush(); log_out.close()
            tail = ""
            try:
                with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    tail = "".join(f.readlines()[-35:])
            except Exception:
                tail = "Không đọc được log."
            raise RuntimeError(
                f"❌ Server không phản hồi sau {boot_timeout}s!\n"
                f"Chi tiết log:\n{'-'*50}\n{tail}\n{'-'*50}"
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


def free_comfyui_memory():
    """Hủy job đang chạy, xóa queue và giải phóng toàn bộ GPU VRAM / System RAM."""
    # 1. Ngắt job đang render
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/interrupt", data=b"{}",
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
    # 2. Xóa hàng đợi
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/queue",
            data=json.dumps({"clear": True}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
    # 3. Yêu cầu ComfyUI unload model khỏi VRAM
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
            headers={"Content-Type": "application/json"})
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
    return "🟢 Đã hủy job và giải phóng toàn bộ GPU VRAM & System RAM!"


def get_comfyui_progress_line():
    """Trích dòng tiến độ sampling gần nhất từ comfyui.log (%, it/s, Executing node)."""
    if not os.path.exists(COMFYUI_LOG_PATH):
        return ""
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in reversed(lines[-20:]):
            s = line.strip()
            if "%" in s or "it/s" in s or "s/it" in s:
                return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)[:120]
            if "Executing node" in s:
                return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)[:120]
    except Exception:
        pass
    return ""


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


def apply_quality_wrapping(prompt: str, use_quality_wrap: bool = True) -> str:
    """Tự động thêm prefix/suffix chất lượng điện ảnh vào prompt.
    Tránh thêm trùng nếu prompt đã chứa từ khóa quality.
    """
    if not use_quality_wrap or not prompt or not prompt.strip():
        return prompt
    p = prompt.strip()
    # Không thêm nếu đã có từ khóa chất lượng
    already_has_quality = any(kw in p.lower() for kw in (
        "cinematic", "4k", "ultra-detailed", "photorealistic", "sharp focus"
    ))
    if not already_has_quality:
        p = QUALITY_PREFIX + p
    if "temporal coherence" not in p.lower():
        p = p + QUALITY_SUFFIX
    return p


def enhance_video(video_path: str, sharpen: bool = True, denoise: bool = True,
                  output_dir: str = OUTPUT_DIR) -> str:
    """Hậu kỳ ffmpeg: khử nhiễu (hqdn3d) + tăng nét (unsharp) sau khi render xong.
    Chỉ chạy nếu cả hai flag đều False thì trả về video gốc.
    """
    if not sharpen and not denoise:
        return video_path
    filters = []
    if denoise:
        filters.append("hqdn3d=3:2:4:3")       # nhẹ tay — không mờ chuyển động
    if sharpen:
        filters.append("unsharp=5:5:0.6:3:3:0.3")  # tăng nét vừa phải
    vf = ",".join(filters)
    out_path = video_path.rsplit(".", 1)[0] + "_enhanced.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(out_path):
        print(f"✨ Đã enhance video: {os.path.basename(out_path)}")
        return out_path
    print(f"⚠️ enhance_video thất bại, giữ nguyên bản gốc.\n{result.stderr[:300]}")
    return video_path


def auto_detect_low_vram() -> bool:
    """Tự động phát hiện VRAM và đề xuất low_vram mode.
    <12 GB VRAM → True (low_vram), >=12 GB → False.
    """
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return vram_gb < 12.0
    except Exception:
        pass
    return True  # Mặc định bật low_vram nếu không detect được


def get_seed(v_seed):
    try:
        v = int(v_seed)
    except Exception:
        v = -1
    return random.randint(1, 999_999_999) if v == -1 else v


def parse_aspect_ratio(ratio_str):
    if "480x832"   in ratio_str: return 480,  832
    if "832x480"   in ratio_str: return 832,  480
    if "1280x720"  in ratio_str: return 1280, 720
    if "720x1280"  in ratio_str: return 720,  1280
    if "720x720"   in ratio_str: return 720,  720
    if "1536x864"  in ratio_str: return 1536, 864   # 1.5K Wide — cần A100/L4
    if "864x1536"  in ratio_str: return 864,  1536  # 1.5K Dọc — cần A100/L4
    return 512, 512


def list_msr_loras():
    msr_dir = os.path.join(LORA_DIR, MSR_LORA_SUBDIR)
    os.makedirs(msr_dir, exist_ok=True)
    files = sorted(
        f"{MSR_LORA_SUBDIR}/{f}"
        for f in os.listdir(msr_dir)
        if f.lower().endswith((".safetensors", ".pt", ".ckpt"))
    )
    return files if files else [MSR_LORA_FILENAME]


def find_latest_video(output_dir=OUTPUT_DIR):
    mp4_files = (
        glob.glob(f"{output_dir}*.mp4")
        + glob.glob(f"{output_dir}output/*.mp4")
        + glob.glob(f"{output_dir}video/*.mp4")
    )
    if not mp4_files:
        return None
    return max(mp4_files, key=os.path.getmtime)


def get_video_duration(video_path):
    """Lấy thời lượng thực tế của video (giây) bằng ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return None


def trim_ref_frames(video_path, target_duration_s, fps, output_dir=OUTPUT_DIR):
    """Cắt bỏ phần reference frames ở đầu video nếu LTXVCropGuides không crop đúng.

    Nguyên lý: video output = [ref_frames] + [generated_frames]
    Nếu tổng thời lượng thực tế > target_duration (prompt duration) thì phần
    dư ở đầu chính là reference frames — dùng ffmpeg -ss để cắt đi.

    Returns: đường dẫn video đã trim (hoặc video gốc nếu không cần trim).
    """
    actual = get_video_duration(video_path)
    if actual is None:
        return video_path  # không đọc được duration → trả gốc

    margin = 1.0 / max(fps, 1)  # cho phép lệch ±1 frame
    if actual <= target_duration_s + margin:
        return video_path  # thời lượng đã đúng, không cần trim

    # Thời điểm bắt đầu cần cắt (bỏ phần đầu reference)
    trim_start = actual - target_duration_s
    trimmed_path = video_path.rsplit(".", 1)[0] + "_trimmed.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{trim_start:.4f}",
        "-i", video_path,
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        trimmed_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.exists(trimmed_path):
        print(f"✂️  Đã trim {trim_start:.2f}s reference frames khỏi đầu video: {os.path.basename(trimmed_path)}")
        return trimmed_path
    # ffmpeg lỗi → trả gốc, không crash
    print(f"⚠️  trim_ref_frames: ffmpeg lỗi, giữ nguyên video gốc.\n{result.stderr[:400]}")
    return video_path


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
    """Ghép nhiều video thành 1. Thử stream-copy trước (nhanh, lossless),
    fallback re-encode CRF18 nếu codec lệch nhau."""
    safe_video_list = [ensure_audio_track(v) for v in video_list]
    concat_file_path = os.path.join(output_dir, f"concat_{out_name}.txt")
    with open(concat_file_path, "w") as f:
        for vid in safe_video_list:
            f.write(f"file '{os.path.abspath(vid)}'\n")

    final_output = os.path.join(output_dir, f"{out_name}_{int(time.time())}.mp4")

    # Bước 1: Stream-copy (nhanh, không mất chất lượng)
    cmd_copy = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file_path,
        "-c", "copy", final_output
    ]
    result = subprocess.run(cmd_copy, capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(final_output):
        os.remove(concat_file_path)
        return final_output

    # Bước 2: Fallback re-encode CRF18 (chất lượng cao, tương thích mọi codec)
    cmd_reencode = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file_path,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        final_output,
    ]
    result2 = subprocess.run(cmd_reencode, capture_output=True, text=True)
    if result2.returncode != 0 or not os.path.exists(final_output):
        raise RuntimeError(
            f"ffmpeg concat thất bại:\n{result.stderr[-400:]}\n{result2.stderr[-400:]}"
        )
    os.remove(concat_file_path)
    return final_output


def submit_and_wait_gen(workflow, scene_label="", max_wait_seconds=1800, poll_interval=2):
    """Generator theo dõi tiến độ thời gian thực, tự giải phóng VRAM khi xong/lỗi.
    Yield: (is_done: bool, prompt_id: str, progress_msg: str)
    """
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req  = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        response  = urllib.request.urlopen(req, timeout=30)
        prompt_id = json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        free_comfyui_memory()
        raise RuntimeError(f"❌ ComfyUI từ chối workflow: {body[:800]}")
    except Exception as e:
        free_comfyui_memory()
        raise RuntimeError(f"❌ Lỗi gửi job API: {e}")

    waited = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 15
    # Grace period: bỏ qua check "not is_running" vài vòng đầu
    # Tránh false "Render thất bại" ngay sau khi submit
    GRACE_POLLS = 3
    poll_count  = 0

    while waited < max_wait_seconds:
        try:
            history = json.loads(urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}"),
                timeout=30).read())
            consecutive_errors = 0
            if str(prompt_id) in history:
                free_comfyui_memory()
                yield True, prompt_id, "Hoàn tất"
                return

            queue = json.loads(urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8188/queue"), timeout=30).read())
            is_running = any(
                str(job[1]) == str(prompt_id)
                for job in queue.get("queue_running", []) + queue.get("queue_pending", [])
            )
            poll_count += 1
            if not is_running and poll_count > GRACE_POLLS:
                free_comfyui_memory()
                raise RuntimeError(f"❌ Render thất bại ở {scene_label}")

            p_line = get_comfyui_progress_line()
            elapsed_m = waited // 60
            elapsed_s = waited % 60
            prog_text = (
                f"[{elapsed_m:02d}m{elapsed_s:02d}s] {p_line}"
                if p_line else
                f"[{elapsed_m:02d}m{elapsed_s:02d}s] Đang tính toán sampling..."
            )
            yield False, prompt_id, prog_text

        except RuntimeError:
            raise
        except Exception:
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                free_comfyui_memory()
                raise RuntimeError(
                    f"❌ Server không phản hồi sau {consecutive_errors * poll_interval}s "
                    f"liên tiếp ở {scene_label}!"
                )

        time.sleep(poll_interval)
        waited += poll_interval

    free_comfyui_memory()
    raise RuntimeError(
        f"⏰ Timeout: {scene_label} quá {max_wait_seconds // 60} phút!\n"
        f"🟢 Đã tự động hủy job và giải phóng GPU VRAM / System RAM.\n"
        f"💡 Thử tắt Stage 2 hoặc giảm độ phân giải để rút ngắn thời gian render."
    )


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
    run_stage2=True,
):
    """Build workflow MSR 2-stage theo LTX2.5-MSR-sample-workflow.json kết hợp
    cơ chế LTXVDualCFGGuider từ ltx2_5.py giúp video tuân thủ cao theo Prompt.

    Stage 1: UNETLoader -> ComfyUILTX25MSRICLoRALoader
             PromptRelayEncode -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide
             LTXVDualCFGGuider (video_cfg / audio_cfg) -> SamplerCustomAdvanced -> SaveVideo (1/2 res)

    Stage 2: LTXVLatentUpsampler -> PromptRelayEncode -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide -> LTXVDualCFGGuider (video_cfg / audio_cfg)
             SamplerCustomAdvanced -> VAEDecodeTiled -> SaveVideo (full res)
    """
    if negative_text is None:
        negative_text = NEGATIVE_PROMPT_DEFAULT
    if msr_lora_name is None:
        msr_lora_name = MSR_LORA_FILENAME
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps       = snap_fps_safe(fps)
    half_w, half_h = half_dims(width, height)

    pic_slot_map = [
        ("pic1",       pic1_name),
        ("pic2",       pic2_name),
        ("pic3",       pic3_name),
        ("pic4",       pic4_name),
        ("background", background_name),
    ]

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
        "S1_width":       {"class_type": "INTConstant",    "inputs": {"value": half_w}},
        "S1_height":      {"class_type": "INTConstant",    "inputs": {"value": half_h}},
        "S1_fps":         {"class_type": "FloatConstant",  "inputs": {"value": float(safe_fps)}},
        "S1_frames_expr": {"class_type": "ComfyMathExpression", "inputs": {"expression": "a*b+1", "values.a": ["S1_fps", 0], "values.b": int(duration)}},
        "S1_empty_vid":   {"class_type": "EmptyLTXVLatentVideo",  "inputs": {"width": ["S1_width", 0], "height": ["S1_height", 0], "length": ["S1_frames_expr", 1], "batch_size": 1}},
        "S1_empty_aud":   {"class_type": "LTXVEmptyLatentAudio",  "inputs": {"audio_vae": ["S1_avae", 0], "frames_number": ["S1_frames_expr", 1], "frame_rate": ["S1_fps", 0], "batch_size": 1}},
        "S1_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {
                "model":           ["S1_msr_loader", 0],
                "clip":            ["S1_clip", 0],
                "latent":          ["S1_empty_vid", 0],
                "global_prompt":   prompt_relay_desc or "",
                "local_prompts":   prompt_main,
                "segment_lengths": "",
                "epsilon":         0.001,
            },
        },
        "S1_ltxv_cond": {"class_type": "LTXVConditioning", "inputs": {"positive": ["S1_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": ["S1_fps", 0]}},
    }

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
        # 🔧 BUG FIX QUAN TRỌNG: Trước đây Stage 1 dùng CFGGuider cứng cfg=1.0
        # → video_cfg từ UI KHÔNG ảnh hưởng Stage 1, prompt adherence rất kém.
        # Fix: Thêm LTXVConditioning riêng cho Stage 1 + dùng LTXVDualCFGGuider
        # → Stage 1 giờ cũng được hưởng video_cfg & audio_cfg đúng từ UI.
        "S1_cond":        {"class_type": "LTXVConditioning",   "inputs": {"positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "frame_rate": ["S1_fps", 0]}},
        "S1_guider":      {"class_type": "LTXVDualCFGGuider",  "inputs": {"model": ["S1_relay", 0], "positive": ["S1_cond", 0], "negative": ["S1_cond", 1], "video_cfg": float(video_cfg), "audio_cfg": float(audio_cfg)}},
        "S1_noise":       {"class_type": "RandomNoise",         "inputs": {"noise_seed": int(seed)}},
        "S1_sampler_sel": {"class_type": "KSamplerSelect",      "inputs": {"sampler_name": "euler_ancestral"}},
        "S1_sigmas":      {"class_type": "ManualSigmas",        "inputs": {"sigmas": SIGMAS_PASS1}},
        "S1_concat_av":   {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["S1_msr_guide", 2], "audio_latent": ["S1_empty_aud", 0]}},
        "S1_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S1_noise", 0], "guider": ["S1_guider", 0], "sampler": ["S1_sampler_sel", 0], "sigmas": ["S1_sigmas", 0], "latent_image": ["S1_concat_av", 0]}},
        "S1_sep_av":      {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["S1_sample", 0]}},
        "S1_crop_guides": {"class_type": "LTXVCropGuides",      "inputs": {"positive": ["S1_cond", 0], "negative": ["S1_cond", 1], "latent": ["S1_sep_av", 0]}},
        "S1_vae_decode":  {"class_type": "VAEDecode",           "inputs": {"samples": ["S1_crop_guides", 2], "vae": ["S1_vvae", 0]}},
        "S1_aud_decode":  {"class_type": "LTXVAudioVAEDecode",  "inputs": {"samples": ["S1_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S1_create_vid":  {"class_type": "CreateVideo",         "inputs": {"images": ["S1_vae_decode", 0], "audio": ["S1_aud_decode", 0], "fps": float(safe_fps)}},
        "S1_save":        {"class_type": "SaveVideo",           "inputs": {"video": ["S1_create_vid", 0], "filename_prefix": "output/LTX25_MSR_Stage1", "format": "auto", "codec": "auto"}},
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
                "local_prompts":   prompt_main,
                "segment_lengths": "",
                "epsilon":         0.001,
            },
        },
    })

    stage2_seed = (int(seed) + 1000) if seed is not None else 42
    # Stage 2 giữ nguyên msr_strength như Stage 1 — giảm mạnh là nguyên nhân nhân vật bị đổi ở bước upscale
    stage2_msr_strength = safe_msr_strength

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
        "S2_ltxv_cond":   {"class_type": "LTXVConditioning",      "inputs": {"positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "frame_rate": ["S1_fps", 0]}},
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
        "S2_save":        {"class_type": "SaveVideo",             "inputs": {"video": ["S2_create_vid", 0], "filename_prefix": "output/LTX25_MSR_DualStage", "format": "auto", "codec": "auto"}},
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
    run_stage2, low_vram,
    use_quality_wrap, post_enhance,
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
        ensure_server(low_vram)
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

    yield None, None, (
        f"✅ Server sẵn sàng. Bắt đầu tạo chuỗi {total_scenes} phân cảnh MSR (tổng {total_seconds}s)...\n"
        f"📸 Ảnh tham khảo: {len(loaded)} slot · Chế độ: {stage_note} · Base Seed: {base_seed} · Video CFG: {video_cfg}"
    )

    generated_videos = []
    for i, p in enumerate(scene_prompts):
        label = f"phân cảnh {i + 1}/{total_scenes}"
        seed_i = base_seed if fixed_seed else (base_seed + i)

        # Tự động thêm prefix/suffix chất lượng điện ảnh vào prompt
        p_wrapped = apply_quality_wrapping(p, use_quality_wrap=bool(use_quality_wrap))

        yield generated_videos, None, (
            f"🔄 Đang quay {label} [{stage_note}]... (Seed: {seed_i})\n"
            f"📝 Nội dung: {p[:120]}..."
        )

        wf = build_msr_workflow(
            prompt_relay_desc = prompt_relay_desc or "",
            prompt_main       = p_wrapped,
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
            run_stage2        = bool(run_stage2),
        )

        # Timeout động: Stage1 ~3 phút/giây video, Stage2 thêm x2
        # Turbo LoRA (Stage1-only) tối thiểu 10 phút; Stage2 đầy đủ tối thiểu 20 phút
        base_timeout = max(600, int(v_length) * 180)
        scene_timeout = base_timeout * 2 if run_stage2 else base_timeout

        # Snapshot danh sách file trước khi submit để detect Stage 1 output mới
        snap_before = set(glob.glob(f"{OUTPUT_DIR}**/*.mp4", recursive=True))

        stage1_fallback = None
        try:
            for is_done, p_id, prog_msg in submit_and_wait_gen(
                wf, scene_label=label, max_wait_seconds=scene_timeout
            ):
                if not is_done:
                    yield generated_videos, None, (
                        f"🔄 Đang quay {label} [{stage_note}]... (Seed: {seed_i})\n"
                        f"⏳ Tiến độ: {prog_msg}\n"
                        f"📝 Nội dung: {p[:120]}..."
                    )
                else:
                    break
        except RuntimeError as e:
            err_str = str(e)
            # Nếu Stage 2 timeout nhưng Stage 1 đã ghi file → dùng Stage 1 làm fallback
            if "Timeout" in err_str and run_stage2:
                snap_after = set(glob.glob(f"{OUTPUT_DIR}**/*.mp4", recursive=True))
                new_files = sorted(snap_after - snap_before, key=os.path.getmtime)
                stage1_candidates = [f for f in new_files if "Stage1" in f]
                if stage1_candidates:
                    stage1_fallback = stage1_candidates[-1]
                    yield generated_videos, None, (
                        f"⚠️ Stage 2 timeout ở {label} — "
                        f"dùng video Stage 1 thay thế: {os.path.basename(stage1_fallback)}"
                    )
                else:
                    yield generated_videos, None, f"❌ {err_str}"; return
            else:
                yield generated_videos, None, f"❌ {err_str}"; return

        # Dùng Stage 1 fallback nếu Stage 2 timeout, ngược lại tìm video mới nhất
        if stage1_fallback:
            latest_video = stage1_fallback
        else:
            latest_video = find_latest_video()
        if not latest_video:
            yield generated_videos, None, f"⚠️ Không tìm thấy file video ở {label}!"; return

        # Tự động cắt reference frames dư thừa ở đầu video
        latest_video = trim_ref_frames(latest_video, target_duration_s=int(v_length), fps=v_fps)

        # Hậu kỳ ffmpeg: khử nhiễu + tăng nét (tuỳ chọn)
        if post_enhance:
            yield generated_videos, None, f"✨ Đang enhance video {label} (denoise + sharpen)..."
            latest_video = enhance_video(latest_video, sharpen=True, denoise=True)

        fallback_note = " ⚠️[Stage1 fallback]" if stage1_fallback else ""
        enhance_note  = " ✨[enhanced]" if post_enhance else ""
        generated_videos.append(latest_video)
        yield generated_videos, None, f"🔔 [DING] ✅ Xong {label} ({i + 1}/{total_scenes})!{fallback_note}{enhance_note}"

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
    "16:9 (1536x864) · 1.5K Wide ⚠️ Cần A100/L4",
    "9:16 (864x1536) · 1.5K Dọc ⚠️ Cần A100/L4",
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

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="violet", secondary_hue="purple", neutral_hue="slate"),
    title="LTX-2.5 MSR Studio",
    css=custom_css,
    js=notification_js,
    fill_width=True,
) as demo:

    with gr.Column(elem_id="msr-header"):
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown(
                    """
                    # 🎬 LTX-2.5 MSR Studio (Tạo Video Dài Tự Động)
                    Multi-Subject Reference — Tạo phim dài nhiều phân cảnh từ ảnh tham khảo nhân vật & bối cảnh

                    <div style="margin-top:4px; opacity:0.9; font-size:0.9rem;">
                    ⚡ LTX-2.5 · 🎭 Tối đa 4 nhân vật + 1 bối cảnh · 🎞️ Tự động render chuỗi kịch bản & ghép nối hoàn chỉnh bằng ffmpeg
                    </div>
                    """
                )
            with gr.Column(scale=1, min_width=160):
                restart_btn = gr.Button("🔄 Restart Server", size="sm")
                free_btn    = gr.Button("🧹 Giải Phóng VRAM", size="sm")
                log_btn     = gr.Button("📋 Xem Log Server",  size="sm")
                restart_out = gr.Markdown("🟢 Sẵn sàng")
        restart_btn.click(fn=force_restart_server, outputs=[restart_out])
        free_btn.click(fn=free_comfyui_memory,     outputs=[restart_out])
        log_btn.click(fn=read_server_log,           outputs=[restart_out])

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
                    "① <b>Mô tả nhân vật</b>: dùng <code>Image 1:... Image 2:...</code> — "
                    "phải khớp <b>chính xác</b> với Pic 1, Pic 2 trong ảnh tham khảo bên trên. "
                    "Mô tả càng chi tiết (màu lông, trang phục, đặc điểm) càng giữ được nhân vật đúng.<br>"
                    "② <b>Kịch bản phim</b>: mỗi phân cảnh cách nhau 1 dòng trống. "
                    "Hệ thống render từng cảnh rồi ghép nối thành phim dài.<br>"
                    "<span style='color:#e53935'>⚠️ <b>Hội thoại / SPEECH</b>: mô tả lời nói <b>ở đầu câu prompt</b>, "
                    "KHÔNG dùng timestamp (At 00:08...) vì model sẽ đẩy speech về cuối video. "
                    "Ví dụ đúng: <i>\"Figure 1 immediately says 'Hello!' while walking forward...\"</i></span>"
                    "</div>"
                )
                msr_relay_desc = gr.Textbox(
                    label="① Mô tả nhân vật — phải khớp với Pic 1/2/3/4 bên trên",
                    lines=4,
                    placeholder=(
                        "Image 1: A chubby orange tabby cat with fluffy ginger fur, wearing a miniature chef hat and white apron.\n\n"
                        "Image 2: A cute Corgi puppy with golden fur, wearing a red bandana around its neck.\n\n"
                        "Image 3: A curious raccoon with grey striped tail, holding a small wooden spoon."
                    ),
                )
                scene_count_display = gr.Markdown("🔹 **Số phân cảnh nhận diện được:** 0", elem_classes="scene-counter")
                msr_prompt = gr.Textbox(
                    label="② Kịch bản / Prompt chính (mỗi phân cảnh cách nhau 1 dòng trống)",
                    lines=6,
                    placeholder=(
                        "Figure 1 (orange cat chef) immediately waves the wooden spoon and shouts 'Dinner is ready!', "
                        "camera slowly pushes in as steam rises from the pot on the counter.\n\n"
                        "Figure 2 (corgi puppy) immediately slides across the kitchen floor excitedly toward the food bowl, "
                        "tail wagging rapidly, camera follows from behind.\n\n"
                        "All characters immediately freeze and stare at camera as the kitchen light flicks on, "
                        "wide shot, everyone caught in the act around the feast."
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
                    length_msr = gr.Slider(label="⏱️ Thời lượng MỖI cảnh (giây)", minimum=1, maximum=20, step=1, value=10)
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
                    msr_lora_dd = gr.Dropdown(
                        label="MSR LoRA", choices=list_msr_loras(), value=MSR_LORA_FILENAME, scale=3)
                    msr_lora_str_sl = gr.Slider(
                        label="LoRA strength", minimum=0.0, maximum=2.0, step=0.05, value=1.0, scale=2,
                        info="1.0 = khuyến nghị để giữ nhân vật đúng. Giảm xuống nếu nhân vật bị cứng/artifact")
                msr_refresh_btn = gr.Button("🔄 Refresh MSR LoRA", size="sm")
                msr_refresh_btn.click(fn=lambda: gr.update(choices=list_msr_loras()), outputs=[msr_lora_dd])

                gr.Markdown("**🎯 Cài đặt MSR Guide & Độ Tuân Thủ Prompt**")
                with gr.Row():
                    msr_video_cfg = gr.Slider(
                        label="🎯 Video CFG (Độ tuân thủ Prompt)", minimum=1.0, maximum=3.5, step=0.1, value=2.5,
                        info="2.5 – 3.0 để AI bám sát prompt & hội thoại. Giảm nếu video bị artifact", scale=1)
                    msr_guide_str_sl = gr.Slider(
                        label="Reference strength", minimum=0.0, maximum=1.0, step=0.05, value=0.85,
                        info="0.85 = giữ nhân vật chặt hơn. Giảm nếu chuyển động bị cứng", scale=1)
                with gr.Row():
                    msr_ref_frames = gr.Radio(
                        label="Reference frames", choices=["25", "33"], value="33",
                        info="33 = mặc định MSR chính thức")
                    msr_tiled = gr.Checkbox(label="Tiled VAE encode", value=False)

                gr.Markdown("**⚙️ Pipeline & Chất Lượng**")
                with gr.Row():
                    msr_stage2   = gr.Checkbox(label="✅ Chạy Stage 2 (upscale x2 + refine)", value=True)
                    msr_low_vram = gr.Checkbox(label="🧊 Low VRAM Mode", value=auto_detect_low_vram())
                with gr.Row():
                    msr_quality_wrap = gr.Checkbox(
                        label="✨ Auto Quality Prefix (Cinematic 4K...)",
                        value=True,
                        info="Tự động thêm tiền tố chất lượng điện ảnh vào mỗi prompt (bỏ nếu prompt đã có 'cinematic', '4K'...)"
                    )
                    msr_post_enhance = gr.Checkbox(
                        label="🔬 Post-Enhance (Denoise + Sharpen)",
                        value=False,
                        info="Hậu kỳ ffmpeg sau render: khử nhiễu hqdn3d + tăng nét unsharp. Thêm ~30s/cảnh."
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
                "<b>💡 Hướng dẫn tạo phim 30s–60s:</b><br>"
                "• Bạn dán toàn bộ 3 phân đoạn trong kịch bản vào ô prompt (cách nhau 2 lần Enter).<br>"
                "• Nhấn <b>Bắt Đầu Tạo Phim MSR</b>: hệ thống sẽ tự động chạy Shot 1 (10s) → Shot 2 (10s) → Shot 3 (10s) "
                "rồi tự ghép lại thành 1 video 30s hoàn chỉnh!<br>"
                "• Tất cả các cảnh đều đồng bộ giữ nguyên đúng nhân vật từ các ảnh tham khảo."
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
            msr_stage2, msr_low_vram,
            msr_quality_wrap, msr_post_enhance,
        ],
        outputs=[gallery_msr, video_out_msr, msr_status],
    )
    def on_clear():
        free_comfyui_memory()
        return None, None, "🟢 Đã dọn dẹp hàng đợi & giải phóng GPU VRAM / System RAM!", "🔹 **Số phân cảnh nhận diện được:** 0"

    msr_clear.click(
        fn=on_clear,
        outputs=[gallery_msr, video_out_msr, msr_status, scene_count_display],
    )

demo.queue()
demo.launch(share=True, inline=False, debug=True)
