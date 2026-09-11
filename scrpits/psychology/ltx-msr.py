# @title [TEST Cell MSR] LTX-2.5 MSR — Multi-Subject Reference Video
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

SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.85, 0.7250, 0.4219, 0.0"

NEGATIVE_PROMPT_DEFAULT = (
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, glitches, watermark, text, logo, subtitles, "
    "static frame, frozen image, standing still, lack of motion, ignored prompt, "
    "deformed limbs, extra paws, duplicate limbs, distorted face, inconsistent appearance, "
    "mid-shot camera cut, character switching, sudden transition"
)


def is_server_running(port=8188):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


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


def ensure_server(low_vram, boot_timeout=300):
    current_mtime = _get_custom_nodes_mtime()
    need_restart = (
        not is_server_running()
        or _SERVER_STATE["running_low_vram"] != low_vram
        or _SERVER_STATE["custom_nodes_mtime"] != current_mtime
    )
    if not need_restart:
        return
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    os.chdir("/content/ComfyUI")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    cmd = ["python", "main.py"]
    if low_vram:
        cmd.insert(2, "--cache-none")
    subprocess.Popen(cmd)
    waited = 0
    while not is_server_running():
        time.sleep(2)
        waited += 2
        if waited > boot_timeout:
            raise RuntimeError(f"Server khong khoi dong duoc sau {boot_timeout}s.")
    _SERVER_STATE["running_low_vram"] = low_vram
    _SERVER_STATE["custom_nodes_mtime"] = current_mtime


def force_restart_server():
    os.system("fuser -k 8188/tcp")
    time.sleep(2)
    _SERVER_STATE["running_low_vram"] = None
    _SERVER_STATE["custom_nodes_mtime"] = None
    return "Server da tat. Lan tao video tiep theo se tu khoi dong lai."


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
        raise RuntimeError(f"ComfyUI tu choi workflow: {body[:800]}")
    except Exception as e:
        raise RuntimeError(f"Loi gui job API: {e}")
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
                raise RuntimeError(f"Render that bai o {scene_label}")
        except RuntimeError:
            raise
        except Exception:
            raise RuntimeError(f"Server bi crash o {scene_label}!")
        time.sleep(poll_interval)
        waited += poll_interval
    raise RuntimeError(f"Timeout: {scene_label} qua {max_wait_seconds // 60} phut.")


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
        # Workflow gốc: Stage 1 dùng CFGGuider đơn giản (cfg=1.0), KHÔNG phải LTXVDualCFGGuider
        # Chỉ Stage 2 mới dùng LTXVDualCFGGuider (có video_cfg + audio_cfg riêng)
        "S1_guider":      {"class_type": "CFGGuider",           "inputs": {"model": ["S1_relay", 0], "positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "cfg": 1.0}},
        "S1_noise":       {"class_type": "RandomNoise",          "inputs": {"noise_seed": int(seed)}},
        "S1_sampler_sel": {"class_type": "KSamplerSelect",       "inputs": {"sampler_name": "euler_ancestral"}},
        "S1_sigmas":      {"class_type": "ManualSigmas",         "inputs": {"sigmas": SIGMAS_PASS1}},
        "S1_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S1_msr_guide", 2], "audio_latent": ["S1_empty_aud", 0]}},
        "S1_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S1_noise", 0], "guider": ["S1_guider", 0], "sampler": ["S1_sampler_sel", 0], "sigmas": ["S1_sigmas", 0], "latent_image": ["S1_concat_av", 0]}},
        "S1_sep_av":      {"class_type": "LTXVSeparateAVLatent",  "inputs": {"av_latent": ["S1_sample", 0]}},
        "S1_crop_guides": {"class_type": "LTXVCropGuides",       "inputs": {"positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "latent": ["S1_sep_av", 0]}},
        "S1_vae_decode":  {"class_type": "VAEDecode",             "inputs": {"samples": ["S1_crop_guides", 2], "vae": ["S1_vvae", 0]}},
        "S1_aud_decode":  {"class_type": "LTXVAudioVAEDecode",   "inputs": {"samples": ["S1_sep_av", 1], "audio_vae": ["S1_avae", 0]}},
        "S1_create_vid":  {"class_type": "CreateVideo",           "inputs": {"images": ["S1_vae_decode", 0], "audio": ["S1_aud_decode", 0], "fps": float(safe_fps)}},
        "S1_save":        {"class_type": "SaveVideo",             "inputs": {"video": ["S1_create_vid", 0], "filename_prefix": "output/LTX25_MSR_Stage1", "format": "auto", "codec": "auto"}},
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
# BUILD WORKFLOW V2V — INPAINT WITH FIRST FRAME + RIPPLE LoRA
# ==========================================================================
# Tham chiếu: RuneXX/LTX-2.5-Workflows · Video-to-Video/
#             LTX-2.5_-_Inpaint-with-first-frame_Ripple-Lora.json
#
# Pipeline:
#   LoadVideo  →  VAEEncode (video latent)  +  extract first frame
#   CLIPTextEncode (pos/neg)  →  LTXVConditioning
#   LoraLoaderModelOnly (Ripple LoRA)
#   ModelAttentionBackend → LTXVChunkFeedForward → LTX2AttentionTunerPatch
#   LTXVInpaintConditioning (masked inpaint, first-frame anchor)
#   LTXVDualCFGGuider → SamplerCustomAdvanced (ManualSigmas denoise)
#   LTXVSeparateAVLatent → VAEDecodeTiled → SaveVideo
# ==========================================================================

RIPPLE_LORA_FILENAME = globals().get(
    "RIPPLE_LORA_FILENAME", "ltx2.5/LTX25_Ripple_v11.safetensors"
)


def list_ripple_loras():
    """Liệt kê các LoRA Ripple / V2V trong thư mục MSR_LORA_SUBDIR."""
    msr_dir = os.path.join(LORA_DIR, MSR_LORA_SUBDIR)
    os.makedirs(msr_dir, exist_ok=True)
    files = sorted(
        f"{MSR_LORA_SUBDIR}/{f}"
        for f in os.listdir(msr_dir)
        if f.lower().endswith((".safetensors", ".pt", ".ckpt"))
    )
    return files if files else [RIPPLE_LORA_FILENAME]


def build_v2v_workflow(
    *,
    prompt_text,
    negative_text=None,
    input_video_name,
    width=720,
    height=1280,
    fps=24,
    seed=None,
    video_cfg=3.0,
    audio_cfg=3.0,
    ripple_lora_name=None,
    ripple_lora_strength=1.35,
    denoise_strength=0.65,
    chunk_feed_forward=True,
    chunk_size=2,
    attention_tuner=True,
    run_upscale=False,
):
    """Build workflow V2V Inpaint-with-First-Frame + Ripple LoRA cho LTX-2.5.

    Cấu trúc pipeline (bám theo HuggingFace RuneXX workflow):
      1. Tải model: UNETLoader → LoraLoaderModelOnly (Ripple)
                    ModelAttentionBackend → LTXVChunkFeedForward → LTX2AttentionTunerPatch
      2. Encode video: VHS_LoadVideo → VAEEncode → video latent
      3. First frame: VHS_GetVideoFrames (index=0) → dùng làm anchor ảnh đầu
      4. Text encode: CLIPTextEncode pos + neg → LTXVConditioning
      5. Inpaint: LTXVInpaintConditioning (frame đầu cố định, phần còn lại regenerate)
      6. Sampling: LTXVDualCFGGuider + SamplerCustomAdvanced + ManualSigmas (denoise)
      7. Decode: LTXVSeparateAVLatent → VAEDecodeTiled → SaveVideo
    """
    if negative_text is None:
        negative_text = NEGATIVE_PROMPT_DEFAULT
    if ripple_lora_name is None:
        ripple_lora_name = RIPPLE_LORA_FILENAME
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps = snap_fps_safe(fps)
    clamp_den = max(0.05, min(1.0, float(denoise_strength)))
    # Tự tạo schedule sigma dựa trên denoise_strength
    sigmas_v2v = (
        f"{clamp_den:.3f}, "
        f"{clamp_den*0.85:.3f}, "
        f"{clamp_den*0.65:.3f}, "
        f"{clamp_den*0.43:.3f}, "
        f"{clamp_den*0.21:.3f}, "
        f"0.0"
    )

    wf = {
        # ── 1. Loader ──────────────────────────────────────────────────────
        "V_unet":  {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "V_clip":  {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "V_vvae":  {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "V_avae":  {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},

        # ── 2. Ripple LoRA ─────────────────────────────────────────────────
        "V_ripple_lora": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model":          ["V_unet", 0],
                "lora_name":      ripple_lora_name,
                "strength_model": float(ripple_lora_strength),
            },
        },
    }

    # ── 3. Attention backend + Memory / Performance patches ───────────────
    prev_model_node = "V_ripple_lora"
    if chunk_feed_forward:
        wf["V_attn_backend"] = {
            "class_type": "ModelAttentionBackend",
            "inputs": {"model": [prev_model_node, 0], "attention": "comfy kitchen attention"},
        }
        wf["V_chunk_ff"] = {
            "class_type": "LTXVChunkFeedForward",
            "inputs": {"model": ["V_attn_backend", 0], "chunks": int(chunk_size), "dim_threshold": 4096},
        }
        prev_model_node = "V_chunk_ff"

    if attention_tuner:
        wf["V_attn_tuner"] = {
            "class_type": "LTX2AttentionTunerPatch",
            "inputs": {
                "model":                [prev_model_node, 0],
                "blocks":               "",
                "video_scale":          1,
                "audio_scale":          1,
                "audio_to_video_scale": 1,
                "video_to_audio_scale": 1,
                "triton_kernels":       True,
            },
        }
        prev_model_node = "V_attn_tuner"

    final_model_ref = [prev_model_node, 0]

    wf.update({
        # ── 4. Load video đầu vào & encode latent ─────────────────────────
        "V_load_video": {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video":             input_video_name,
                "force_rate":        safe_fps,
                "force_size":        "Custom Height",
                "custom_width":      int(width),
                "custom_height":     int(height),
                "frame_load_cap":    0,
                "skip_first_frames": 0,
                "select_every_nth":  1,
            },
        },
        "V_vae_encode": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["V_load_video", 0], "vae": ["V_vvae", 0]},
        },

        # ── 5. Trích first frame làm anchor ───────────────────────────────
        # VHS_GetVideoFrames: lấy frame index=0 để ghim cố định đầu video
        "V_first_frame": {
            "class_type": "VHS_GetVideoFrames",
            "inputs": {"image": ["V_load_video", 0], "index": 0, "skip_first_frames": 0},
        },

        # ── 6. Text encode ─────────────────────────────────────────────────
        "V_pos_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["V_clip", 0], "text": prompt_text}},
        "V_neg_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["V_clip", 0], "text": negative_text}},

        # ── 7. FPS constant ────────────────────────────────────────────────
        "V_fps":    {"class_type": "FloatConstant", "inputs": {"value": float(safe_fps)}},
        "V_width":  {"class_type": "INTConstant",   "inputs": {"value": int(width)}},
        "V_height": {"class_type": "INTConstant",   "inputs": {"value": int(height)}},

        # ── 8. LTXVConditioning ────────────────────────────────────────────
        "V_ltxv_cond": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive":   ["V_pos_enc", 0],
                "negative":   ["V_neg_enc", 0],
                "frame_rate": ["V_fps", 0],
            },
        },

        # ── 9. Empty audio latent (sync với video encode frame count) ──────
        "V_empty_aud": {
            "class_type": "LTXVEmptyLatentAudio",
            "inputs": {
                "audio_vae":     ["V_avae", 0],
                "frames_number": 0,   # 0 = auto-match từ video latent
                "frame_rate":    ["V_fps", 0],
                "batch_size":    1,
            },
        },

        # ── 10. LTXVInpaintConditioning — first-frame anchor + denoise mask
        "V_inpaint_cond": {
            "class_type": "LTXVInpaintConditioning",
            "inputs": {
                "positive":         ["V_ltxv_cond", 0],
                "negative":         ["V_ltxv_cond", 1],
                "vae":              ["V_vvae", 0],
                "latent":           ["V_vae_encode", 0],
                "ref_image":        ["V_first_frame", 0],
                "strength":         clamp_den,
                "noise_mask_start": 0.0,
                "noise_mask_end":   1.0,
            },
        },

        # ── 11. Concat audio + video latent ───────────────────────────────
        "V_concat_av": {
            "class_type": "LTXVConcatAVLatent",
            "inputs": {
                "video_latent": ["V_inpaint_cond", 2],
                "audio_latent": ["V_empty_aud", 0],
            },
        },

        # ── 12. Dual CFG Guider + Sampler ─────────────────────────────────
        "V_dual_guider": {
            "class_type": "LTXVDualCFGGuider",
            "inputs": {
                "model":     final_model_ref,
                "positive":  ["V_inpaint_cond", 0],
                "negative":  ["V_inpaint_cond", 1],
                "video_cfg": float(video_cfg),
                "audio_cfg": float(audio_cfg),
            },
        },
        "V_noise":       {"class_type": "RandomNoise",          "inputs": {"noise_seed": int(seed)}},
        "V_sampler_sel": {"class_type": "KSamplerSelect",       "inputs": {"sampler_name": "euler"}},
        "V_sigmas":      {"class_type": "ManualSigmas",         "inputs": {"sigmas": sigmas_v2v}},
        "V_sample": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise":        ["V_noise", 0],
                "guider":       ["V_dual_guider", 0],
                "sampler":      ["V_sampler_sel", 0],
                "sigmas":       ["V_sigmas", 0],
                "latent_image": ["V_concat_av", 0],
            },
        },

        # ── 13. Decode & Save ──────────────────────────────────────────────
        "V_sep_av":    {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["V_sample", 0]}},
        "V_vae_tiled": {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples":          ["V_sep_av", 0],
                "vae":              ["V_vvae", 0],
                "tile_size":        512,
                "overlap":          64,
                "temporal_size":    64,
                "temporal_overlap": 16,
            },
        },
        "V_aud_decode":  {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["V_sep_av", 1], "audio_vae": ["V_avae", 0]}},
        "V_create_vid":  {"class_type": "CreateVideo",         "inputs": {"images": ["V_vae_tiled", 0], "audio": ["V_aud_decode", 0], "fps": float(safe_fps)}},
        "V_save":        {"class_type": "SaveVideo",           "inputs": {"video": ["V_create_vid", 0], "filename_prefix": "output/LTX25_V2V_Ripple", "format": "auto", "codec": "auto"}},
    })

    # ── 14. Optional Spatial Upscale x2 ────────────────────────────────────
    if run_upscale:
        wf.update({
            "VU_upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
            "VU_upsampler":      {"class_type": "LTXVLatentUpsampler",      "inputs": {"samples": ["V_sep_av", 0], "upscale_model": ["VU_upscale_loader", 0], "vae": ["V_vvae", 0]}},
            "VU_vae_tiled":      {
                "class_type": "VAEDecodeTiled",
                "inputs": {"samples": ["VU_upsampler", 0], "vae": ["V_vvae", 0],
                           "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16},
            },
            "VU_aud_decode":     {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["V_sep_av", 1], "audio_vae": ["V_avae", 0]}},
            "VU_create_vid":     {"class_type": "CreateVideo",        "inputs": {"images": ["VU_vae_tiled", 0], "audio": ["VU_aud_decode", 0], "fps": float(safe_fps)}},
            "VU_save":           {"class_type": "SaveVideo",          "inputs": {"video": ["VU_create_vid", 0], "filename_prefix": "output/LTX25_V2V_Ripple_Upscaled", "format": "auto", "codec": "auto"}},
        })

    return wf


# ==========================================================================
# GENERATE V2V — HÀM GRADIO GENERATOR
# ==========================================================================
def generate_v2v_gradio(
    input_video_path,
    prompt_text,
    negative_text,
    aspect_ratio,
    v_fps,
    v_seed,
    video_cfg,
    audio_cfg,
    ripple_lora_name,
    ripple_lora_strength,
    denoise_strength,
    chunk_feed_forward,
    chunk_size,
    attention_tuner,
    run_upscale,
    low_vram,
):
    if not input_video_path:
        yield None, "⚠️ Vui lòng tải lên video đầu vào trước khi render!"; return
    if not prompt_text or not prompt_text.strip():
        yield None, "⚠️ Vui lòng nhập prompt mô tả hiệu ứng V2V!"; return

    v_width, v_height = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

    yield None, "🔄 Đang kiểm tra / khởi động ComfyUI server..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, f"❌ {e}"; return

    seed = get_seed(v_seed)
    os.makedirs(INPUT_DIR, exist_ok=True)

    # Copy video đầu vào vào input dir của ComfyUI
    ext = os.path.splitext(input_video_path)[1].lower() or ".mp4"
    video_name = f"v2v_input_{int(time.time())}{ext}"
    shutil.copy(input_video_path, os.path.join(INPUT_DIR, video_name))

    yield None, (
        f"✅ Server sẵn sàng. Bắt đầu V2V Ripple LoRA render...\n"
        f"📹 Video: {os.path.basename(input_video_path)} · "
        f"Seed: {seed} · Denoise: {denoise_strength} · "
        f"Video CFG: {video_cfg} · LoRA: {os.path.basename(str(ripple_lora_name))}"
    )

    wf = build_v2v_workflow(
        prompt_text          = prompt_text,
        negative_text        = negative_text or NEGATIVE_PROMPT_DEFAULT,
        input_video_name     = video_name,
        width                = safe_width,
        height               = safe_height,
        fps                  = v_fps,
        seed                 = seed,
        video_cfg            = float(video_cfg),
        audio_cfg            = float(audio_cfg),
        ripple_lora_name     = ripple_lora_name,
        ripple_lora_strength = float(ripple_lora_strength),
        denoise_strength     = float(denoise_strength),
        chunk_feed_forward   = bool(chunk_feed_forward),
        chunk_size           = int(chunk_size),
        attention_tuner      = bool(attention_tuner),
        run_upscale          = bool(run_upscale),
    )

    try:
        submit_and_wait(wf, scene_label="V2V Ripple LoRA")
    except Exception as e:
        yield None, f"❌ {e}"; return

    latest_video = find_latest_video()
    if not latest_video:
        yield None, "⚠️ Không tìm thấy file video output sau khi render!"; return

    yield latest_video, (
        f"🔔 [DING] 🎉 V2V Ripple LoRA hoàn tất!\n"
        f"Seed: {seed} · Denoise: {denoise_strength} · CFG: {video_cfg} · "
        f"{'Upscaled x2' if run_upscale else 'No upscale'}"
    )


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
            run_stage2        = bool(run_stage2),
        )

        try:
            submit_and_wait(wf, scene_label=label)
        except Exception as e:
            yield generated_videos, None, f"❌ {e}"; return

        latest_video = find_latest_video()
        if not latest_video:
            yield generated_videos, None, f"⚠️ Không tìm thấy file video ở {label}!"; return

        # Tự động cắt reference frames dư thừa ở đầu video
        # (xảy ra khi LTXVCropGuides không hoạt động đúng)
        latest_video = trim_ref_frames(latest_video, target_duration_s=int(v_length), fps=v_fps)

        generated_videos.append(latest_video)
        yield generated_videos, None, f"🔔 [DING] ✅ Xong {label} ({i + 1}/{total_scenes})!"

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

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="violet", secondary_hue="purple", neutral_hue="slate"),
    title="LTX-2.5 MSR Studio",
    css=custom_css,
    js=notification_js,
    fill_width=True,
) as demo:

    with gr.Tabs():

        # ======================================================================
        # TAB 1 — MSR: Multi-Subject Reference
        # ======================================================================
        with gr.Tab("🎭 MSR — Multi-Subject Reference"):
            with gr.Column(elem_id="msr-header"):
                gr.Markdown(
                    """
                    ### 🎭 MSR — Multi-Subject Reference
                    Tạo phim dài nhiều phân cảnh từ ảnh tham khảo nhân vật & bối cảnh

                    <div style="margin-top:4px; opacity:0.9; font-size:0.9rem;">
                    🎭 Tối đa 4 nhân vật + 1 bối cảnh · 🎞️ Tự động render chuỗi kịch bản & ghép nối hoàn chỉnh bằng ffmpeg
                    </div>
                    """
                )

            with gr.Row():
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
                        msr_neg = gr.Textbox(label="🚫 Negative Prompt", lines=2, value=NEGATIVE_PROMPT_DEFAULT)

                    with gr.Accordion("⚙️ Cài đặt nâng cao MSR", open=False):
                        gr.Markdown("**📐 Kích thước & thời lượng**")
                        ratio_msr = gr.Radio(
                            label="Tỉ lệ khung hình", choices=ratio_choices, value=ratio_choices[0],
                            info="Stage 1 chạy ½ res, Stage 2 upscale x2 về full res")
                        with gr.Row():
                            length_msr = gr.Slider(label="⏱️ Thời lượng MỖI cảnh (giây)", minimum=1, maximum=20, step=1, value=10)
                            fps_msr    = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24)
                        with gr.Row():
                            seed_msr = gr.Number(label="🎲 Seed (-1 = ngẫu nhiên)", value=-1, precision=0)
                            num_segments_msr = gr.Slider(
                                label="🔢 Số phân đoạn (khi chỉ có 1 prompt)", minimum=1, maximum=10, step=1, value=1,
                                info="Chỉ áp dụng nếu ô kịch bản chỉ có 1 prompt đơn")
                        fixed_seed_msr = gr.Checkbox(label="🔗 Dùng chung 1 Seed cho mọi phân cảnh", value=False)
                        gr.Markdown("**🧬 MSR LoRA**")
                        with gr.Row():
                            msr_lora_dd = gr.Dropdown(
                                label="MSR LoRA", choices=list_msr_loras(), value=MSR_LORA_FILENAME, scale=3)
                            msr_lora_str_sl = gr.Slider(
                                label="LoRA strength", minimum=0.0, maximum=2.0, step=0.05, value=0.85, scale=2,
                                info="0.85 = cân bằng giữa nhận diện nhân vật & chuyển động mượt")
                        msr_refresh_btn = gr.Button("🔄 Refresh MSR LoRA", size="sm")
                        msr_refresh_btn.click(fn=lambda: gr.update(choices=list_msr_loras()), outputs=[msr_lora_dd])
                        gr.Markdown("**🎯 MSR Guide & CFG**")
                        with gr.Row():
                            msr_video_cfg = gr.Slider(
                                label="🎯 Video CFG", minimum=1.0, maximum=3.5, step=0.1, value=1.5,
                                info="Khuyến nghị 1.5–2.0 để bám sát hành động kịch bản", scale=1)
                            msr_guide_str_sl = gr.Slider(
                                label="Reference strength", minimum=0.0, maximum=1.0, step=0.05, value=0.7,
                                info="0.7 chuẩn nhất (giữ nhân vật & chuyển động mượt)", scale=1)
                        with gr.Row():
                            msr_ref_frames = gr.Radio(label="Reference frames", choices=["25", "33"], value="33",
                                                      info="33 = mặc định MSR chính thức")
                            msr_tiled = gr.Checkbox(label="Tiled VAE encode", value=False)
                        gr.Markdown("**⚙️ Pipeline**")
                        with gr.Row():
                            msr_stage2   = gr.Checkbox(label="✅ Chạy Stage 2 (upscale x2 + refine)", value=True)
                            msr_low_vram = gr.Checkbox(label="🧊 Low VRAM Mode", value=True)

                with gr.Column(scale=5):
                    with gr.Group():
                        gallery_msr   = gr.Gallery(label="🎥 Các Phân Cảnh Lẻ (Shot 1, Shot 2...)", columns=2, height="auto")
                        video_out_msr = gr.Video(label="🎬 Phim Dài Hoàn Chỉnh (Ghép Nối Liền Mạch)")
                        with gr.Row():
                            msr_btn   = gr.Button("🎬 Bắt Đầu Tạo Phim MSR", variant="primary", scale=3)
                            msr_clear = gr.Button("🗑️ Clear", scale=1)
                        msr_status = gr.Textbox(
                            label="ℹ️ Status / Tiến trình", interactive=False, lines=5, elem_classes="status-box")
                    gr.Markdown(
                        "<div class='info-box'>"
                        "<b>💡 Hướng dẫn tạo phim 30s–60s:</b><br>"
                        "• Dán toàn bộ phân đoạn kịch bản vào ô prompt (cách nhau 2 lần Enter).<br>"
                        "• Hệ thống sẽ tự động chạy Shot 1 → Shot 2 → Shot 3 rồi ghép lại thành video hoàn chỉnh!<br>"
                        "• Tất cả cảnh đồng bộ giữ nguyên đúng nhân vật từ ảnh tham khảo."
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
                ],
                outputs=[gallery_msr, video_out_msr, msr_status],
            )
            msr_clear.click(
                fn=lambda: (None, None, "", "🔹 **Số phân cảnh nhận diện được:** 0"),
                outputs=[gallery_msr, video_out_msr, msr_status, scene_count_display],
            )

        # ======================================================================
        # TAB 2 — V2V: Video-to-Video + Ripple LoRA
        # ======================================================================
        with gr.Tab("🌊 V2V — Ripple LoRA (Video-to-Video)"):
            with gr.Column(elem_id="msr-header"):
                gr.Markdown(
                    """
                    ### 🌊 V2V Inpaint + Ripple LoRA
                    Video-to-Video · Giữ nguyên frame đầu làm anchor · Tạo hiệu ứng Ripple/Wave trên toàn bộ video

                    <div style="margin-top:4px; opacity:0.9; font-size:0.9rem;">
                    📹 Input: Video bất kỳ (MP4/WebM) · 🌊 Ripple LoRA biến đổi phong cách & chuyển động ·
                    🔒 First-frame anchor giữ nguyên bố cục · 🔧 Denoise strength = mức độ biến đổi
                    </div>
                    """
                )

            with gr.Row():
                # --- CỘT TRÁI V2V ---
                with gr.Column(scale=5):
                    with gr.Group():
                        gr.Markdown("### 📹 Video đầu vào")
                        gr.Markdown(
                            "<div class='info-box'>"
                            "Upload video gốc (MP4, WebM, AVI...) để biến đổi phong cách.<br>"
                            "<b>First frame</b> sẽ được ghim cố định làm anchor — phần còn lại được regenerate bởi Ripple LoRA.<br>"
                            "Khuyến nghị: video 9:16 dọc, dưới 30s, 720p."
                            "</div>"
                        )
                        v2v_input_video = gr.Video(label="📹 Video đầu vào (bắt buộc)", sources=["upload"])

                    with gr.Group():
                        gr.Markdown("### 📝 Prompt V2V")
                        v2v_prompt = gr.Textbox(
                            label="✍️ Mô tả hiệu ứng / phong cách mong muốn",
                            lines=4,
                            placeholder=(
                                "Ripple water effect, flowing liquid distortion on the characters, "
                                "cinematic wave animation, smooth motion, photorealistic quality, "
                                "consistent character appearance..."
                            ),
                        )
                        v2v_neg = gr.Textbox(label="🚫 Negative Prompt", lines=2, value=NEGATIVE_PROMPT_DEFAULT)

                    with gr.Accordion("⚙️ Cài đặt nâng cao V2V", open=True):
                        gr.Markdown("**📐 Output & FPS**")
                        ratio_v2v = gr.Radio(
                            label="Tỉ lệ khung hình output",
                            choices=ratio_choices,
                            value="9:16 (720x1280) · HD 720p Dọc",
                            info="Nên giữ nguyên tỉ lệ video gốc để tránh crop/stretch",
                        )
                        with gr.Row():
                            fps_v2v  = gr.Slider(label="🎞️ FPS", minimum=8, maximum=120, step=8, value=24)
                            seed_v2v = gr.Number(label="🎲 Seed (-1 = ngẫu nhiên)", value=-1, precision=0)

                        gr.Markdown("**🌊 Ripple LoRA**")
                        with gr.Row():
                            v2v_ripple_lora_dd = gr.Dropdown(
                                label="Ripple LoRA", choices=list_ripple_loras(),
                                value=RIPPLE_LORA_FILENAME, scale=3,
                                info="Đặt file LoRA vào: /content/ComfyUI/models/loras/ltx2.5/")
                            v2v_ripple_str = gr.Slider(
                                label="LoRA strength", minimum=0.5, maximum=2.0, step=0.05, value=1.35, scale=2,
                                info="1.35 = giá trị gốc workflow RuneXX · Tăng → hiệu ứng Ripple mạnh hơn")
                        v2v_ripple_refresh = gr.Button("🔄 Refresh Ripple LoRA", size="sm")
                        v2v_ripple_refresh.click(fn=lambda: gr.update(choices=list_ripple_loras()), outputs=[v2v_ripple_lora_dd])

                        gr.Markdown("**🎯 Denoise & CFG**")
                        with gr.Row():
                            v2v_denoise = gr.Slider(
                                label="🎛️ Denoise Strength (mức độ biến đổi)",
                                minimum=0.1, maximum=1.0, step=0.05, value=0.65,
                                info="0.3–0.5 = giữ nhiều nội dung gốc · 0.65–0.8 = biến đổi mạnh · 1.0 = tạo mới hoàn toàn",
                                scale=2)
                        with gr.Row():
                            v2v_video_cfg = gr.Slider(
                                label="🎯 Video CFG", minimum=1.0, maximum=8.0, step=0.5, value=3.0,
                                info="3.0 = giá trị gốc workflow · Tăng → bám sát prompt hơn", scale=1)
                            v2v_audio_cfg = gr.Slider(
                                label="🔊 Audio CFG", minimum=1.0, maximum=8.0, step=0.5, value=3.0,
                                info="CFG cho luồng audio latent", scale=1)

                        gr.Markdown("**⚙️ Patches Hiệu năng (KJNodes)**")
                        gr.Markdown(
                            "<div class='info-box'>"
                            "Các patch này giúp tiết kiệm VRAM và tăng tốc độ render đáng kể trên GPU < 24GB.<br>"
                            "<b>LTXVChunkFeedForward</b>: chia feed-forward thành chunks nhỏ hơn để giảm peak VRAM.<br>"
                            "<b>LTX2AttentionTunerPatch</b>: tối ưu attention scales giữa video ↔ audio latent."
                            "</div>"
                        )
                        with gr.Row():
                            v2v_chunk_ff = gr.Checkbox(
                                label="LTXVChunkFeedForward (tiết kiệm VRAM)", value=True,
                                info="Bật để chia feed-forward thành chunks — khuyến nghị với GPU < 24GB")
                            v2v_chunk_size = gr.Slider(
                                label="Chunk size", minimum=1, maximum=8, step=1, value=2,
                                info="2 = mặc định · Tăng nếu GPU mạnh")
                        with gr.Row():
                            v2v_attn_tuner  = gr.Checkbox(
                                label="LTX2AttentionTunerPatch (tối ưu attention)", value=True)
                            v2v_upscale     = gr.Checkbox(
                                label="Upscale x2 sau V2V (Spatial Upscaler)", value=False,
                                info="Bật để nâng độ phân giải lên x2 sau khi render V2V xong")
                        v2v_low_vram = gr.Checkbox(label="🧊 Low VRAM Mode", value=True)

                # --- CỘT PHẢI V2V ---
                with gr.Column(scale=5):
                    with gr.Group():
                        v2v_video_out = gr.Video(label="🌊 Video V2V Output (Ripple LoRA)")
                        with gr.Row():
                            v2v_btn   = gr.Button("🌊 Bắt Đầu V2V Ripple", variant="primary", scale=3)
                            v2v_clear = gr.Button("🗑️ Clear", scale=1)
                        v2v_status = gr.Textbox(
                            label="ℹ️ Status / Tiến trình V2V", interactive=False, lines=5, elem_classes="status-box")

                    gr.Markdown(
                        "<div class='info-box'>"
                        "<b>💡 Hướng dẫn dùng V2V Ripple LoRA:</b><br>"
                        "① Upload video gốc vào ô bên trái.<br>"
                        "② Nhập prompt mô tả hiệu ứng Ripple/Wave muốn áp dụng.<br>"
                        "③ Điều chỉnh <b>Denoise Strength</b>: thấp (0.3–0.5) giữ nhiều bố cục gốc, cao (0.7–0.9) biến đổi mạnh.<br>"
                        "④ Nhấn <b>Bắt Đầu V2V Ripple</b> và đợi render.<br>"
                        "<br>"
                        "<b>📁 Cần cài thêm custom node:</b><br>"
                        "• <code>ComfyUI-VideoHelperSuite</code> (VHS_LoadVideo, VHS_GetVideoFrames)<br>"
                        "• <code>ComfyUI-KJNodes</code> (LTXVChunkFeedForward, LTX2AttentionTunerPatch)<br>"
                        "• File LoRA: <code>LTX25_Ripple_v11.safetensors</code> đặt trong <code>loras/ltx2.5/</code>"
                        "</div>"
                    )

            v2v_btn.click(
                fn=generate_v2v_gradio,
                inputs=[
                    v2v_input_video,
                    v2v_prompt, v2v_neg,
                    ratio_v2v, fps_v2v, seed_v2v,
                    v2v_video_cfg, v2v_audio_cfg,
                    v2v_ripple_lora_dd, v2v_ripple_str,
                    v2v_denoise,
                    v2v_chunk_ff, v2v_chunk_size,
                    v2v_attn_tuner,
                    v2v_upscale,
                    v2v_low_vram,
                ],
                outputs=[v2v_video_out, v2v_status],
            )
            v2v_clear.click(
                fn=lambda: (None, ""),
                outputs=[v2v_video_out, v2v_status],
            )

demo.queue()
demo.launch(share=True, inline=False, debug=True)
