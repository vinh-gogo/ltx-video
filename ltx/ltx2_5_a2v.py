#@title 🎙️ Cell 2: LTX-2.5 A2V Studio — Audio-to-Video Two-Stage Distilled
# ==============================================================================
# Cell 2: Giao diện Gradio Live & API Dispatcher tạo video từ ÂM THANH (A2V)
# dựa trên kiến trúc chính thức: workflow/ltx/LTX-2.5_A2V_Two_Stage_Distilled.json
#
# Điểm đột phá của pipeline A2V:
#  1. Audio Latent Freezing: Âm thanh được VAE Encode và ĐÓNG BĂNG (noise_mask=0),
#     giữ trọn vẹn nhịp điệu/lời thoại để điều hướng video sinh ra khớp từng nốt nhạc/khẩu hình.
#  2. Lossless Original Audio Muxing: Waveform âm thanh gốc được cắt (trim) và mux trực tiếp
#     vào video đầu ra qua CreateVideo, triệt tiêu hoàn toàn méo âm (không giải mã audio qua VAE).
#  3. Two-Stage Distilled (8 steps + 3 steps Refine):
#     - Stage 1: 8 bước sinh video thô bám chặt audio latent.
#     - Stage 2: 2x Spatial Upscale + 3 bước tinh chỉnh siêu nét với LTX-2.5 Spatial Refiner.
#  4. Optional Start Frame (I2V): Cho phép nạp ảnh chân dung/bối cảnh để nhân vật xuất hiện
#     và cử động theo bài hát / giọng nói một cách tự nhiên.
#
# Yêu cầu: Cell 1 (download_a2v.py) đã tải xong model weights.
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
# CẤU HÌNH HỆ THỐNG & ĐƯỜNG DẪN COMFYUI
# ==============================================================================
INPUT_DIR  = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"
COMFYUI_DIR = "/content/ComfyUI"
COMFYUI_LOG_PATH = "/content/comfyui.log"

# Tự động chọn mô hình có sẵn trong thư mục ComfyUI (hỗ trợ cả int8 và bf16)
def resolve_model_file(folder, preferred_names):
    models_dir = os.path.join(COMFYUI_DIR, "models", folder)
    if not os.path.exists(models_dir):
        return preferred_names[0]
    existing = os.listdir(models_dir)
    for name in preferred_names:
        if name in existing:
            return name
    return preferred_names[0]

UNET_FILENAME = resolve_model_file(
    "diffusion_models",
    [
        "ltx-2.5-22b-distilled-transformer-bf16.safetensors",
        "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    ]
)

TEXT_ENCODER_FILENAME = resolve_model_file(
    "text_encoders",
    [
        "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
        "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
    ]
)

VIDEO_VAE_FILENAME        = "ltx-2.5-video-vae-bf16.safetensors"
AUDIO_VAE_FILENAME        = "ltx-2.5-audio-vae-bf16.safetensors"
SPATIAL_UPSCALER_FILENAME = "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"

# Chuẩn Sigmas chính thức của LTX-2.5 Distilled (8 bước) và Two-Stage Refinement (3 bước)
SIGMAS_PASS1 = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
SIGMAS_PASS2 = "0.909375, 0.725, 0.421875, 0.0"

QUALITY_PREFIX = (
    "Cinematic photorealistic 4K ultra-detailed footage, master cinematography, "
    "sharp focus, professional lighting, natural film grain, "
)
QUALITY_SUFFIX = (
    ", lifelike textures, smooth cinematic movement naturally reacting to the audio, "
    "highly detailed features, temporal consistency, synchronized rhythm"
)

NEGATIVE_PROMPT_DEFAULT = (
    "split screen, collage, grid, multiple panels, photo frame, triple view, character sheet, "
    "lineup, side by side, border, letterbox, white bars, inset image, picture-in-picture, "
    "blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, "
    "compression artifacts, glitches, watermark, text, logo, subtitles, "
    "static frame, frozen image, lack of motion, deformed limbs, bad anatomy"
)

# ==============================================================================
# HÀM QUẢN LÝ COMFYUI SERVER & GPU
# ==============================================================================
_SERVER_STATE = {"running_low_vram": None}


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


def start_comfyui(low_vram=True):
    cmd = ["python", "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch"]
    if low_vram:
        cmd += ["--lowvram"]
    else:
        cmd += ["--highvram"]

    log_file = open(COMFYUI_LOG_PATH, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=COMFYUI_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        close_fds=True,
    )
    _SERVER_STATE["running_low_vram"] = low_vram

    for _ in range(60):
        time.sleep(1.0)
        if is_server_running(8188):
            return proc
    raise RuntimeError("⏰ Không thể kết nối tới ComfyUI server sau 60 giây. Xem log tại " + COMFYUI_LOG_PATH)


def ensure_server(low_vram=True):
    needs_restart = (
        _SERVER_STATE["running_low_vram"] is not None
        and _SERVER_STATE["running_low_vram"] != low_vram
    )
    if needs_restart and is_server_running(8188):
        subprocess.run(["pkill", "-f", "main.py"], capture_output=True)
        time.sleep(2.0)
        _SERVER_STATE["running_low_vram"] = None

    if not is_server_running(8188):
        start_comfyui(low_vram=low_vram)


def free_comfyui_memory():
    """Giải phóng VRAM trên server sau mỗi lượt render."""
    try:
        req = urllib.request.Request("http://127.0.0.1:8188/free", data=b'{"unload_models":false,"free_memory":true}')
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


# ==============================================================================
# HÀM XỬ LÝ KÍCH THƯỚC & ĐỊNH DẠNG TỶ LỆ
# ==============================================================================
def snap_32(x):
    """Mọi kích thước LTX-2.5 phải chia hết cho 32."""
    return max(128, int(round(x / 32.0)) * 32)


def snap_fps_safe(fps):
    target = round(float(fps))
    return target if target in (24, 25, 30, 48, 50, 60) else 24


def parse_aspect_ratio(aspect_str):
    mapping = {
        "16:9 Landscape (960x544 - Chuẩn A2V Stage 1)": (960, 544),
        "9:16 Vertical (544x960 - TikTok/Reels/Shorts)": (544, 960),
        "1:1 Square (640x640 - Vuông)": (640, 640),
        "4:3 Classic TV (768x576)": (768, 576),
        "21:9 Ultrawide Cinema (1024x448)": (1024, 448),
        "720p HD 16:9 (1280x704)": (1280, 704),
    }
    return mapping.get(aspect_str, (960, 544))


def get_audio_duration(file_path):
    """Lấy thời lượng thực tế của file âm thanh."""
    if not file_path or not os.path.exists(file_path):
        return 5.0
    try:
        import soundfile as sf
        info = sf.info(file_path)
        return float(info.duration)
    except Exception:
        pass
    try:
        cap = cv2.VideoCapture(file_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if frames > 0:
            return float(frames / fps)
    except Exception:
        pass
    return 5.0


# ==============================================================================
# THUẬT TOÁN DỰNG WORKFLOW: LTX-2.5 A2V TWO-STAGE DISTILLED (CHUẨN 100%)
# ==============================================================================
def build_a2v_workflow(
    *,
    audio_filename,
    start_image_filename=None,
    positive_prompt,
    negative_prompt=None,
    width=960,
    height=544,
    fps=24,
    audio_start=0.0,
    duration=5.0,
    seed=None,
    video_cfg=1.0,
    img_strength=0.7,
    img_compression=18,
    run_stage2=True,
):
    """
    Tạo API Workflow JSON ComfyUI tái hiện chính xác 1:1 workflow:
    workflow/ltx/LTX-2.5_A2V_Two_Stage_Distilled.json
    """
    if negative_prompt is None:
        negative_prompt = NEGATIVE_PROMPT_DEFAULT
    if seed is None:
        seed = random.randint(1, 999_999_999)

    safe_fps = snap_fps_safe(fps)
    w = snap_32(width)
    h = snap_32(height)

    # 1. Khởi tạo Models & Text Encoders
    wf = {
        "unet":   {"class_type": "UNETLoader",  "inputs": {"unet_name": UNET_FILENAME, "weight_dtype": "default"}},
        "clip":   {"class_type": "CLIPLoader",  "inputs": {"clip_name": TEXT_ENCODER_FILENAME, "type": "ltxv", "device": "default"}},
        "vvae":   {"class_type": "VAELoader",   "inputs": {"vae_name": VIDEO_VAE_FILENAME}},
        "avae":   {"class_type": "VAELoader",   "inputs": {"vae_name": AUDIO_VAE_FILENAME}},

        # 2. Xử lý Prompt & Frame Rate Conditioning
        "pos_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": positive_prompt}},
        "neg_enc": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": negative_prompt}},
        "fps_c":   {"class_type": "FloatConstant",  "inputs": {"value": float(safe_fps)}},
        "cond":    {"class_type": "LTXVConditioning", "inputs": {"positive": ["pos_enc", 0], "negative": ["neg_enc", 0], "frame_rate": ["fps_c", 0]}},

        # 3. Tính toán số Frame chuẩn LTX: 1 + floor(fps * duration / 8) * 8
        "frames_expr": {
            "class_type": "ComfyMathExpression",
            "inputs": {
                "expression": "1 + floor(a*b/8)*8",
                "values.a": ["fps_c", 0],
                "values.b": float(duration)
            }
        },

        # 4. Nạp Audio & Trim chính xác theo audio_start + duration
        "load_audio": {"class_type": "LoadAudio", "inputs": {"audio": audio_filename}},
        "trim_audio": {
            "class_type": "TrimAudioDuration",
            "inputs": {
                "audio": ["load_audio", 0],
                "start_index": float(audio_start),
                "duration": float(duration)
            }
        },

        # 5. Mã hóa Audio VAE & ĐÓNG BĂNG Token (Noise Mask = 0)
        # Giúp audio latent không bị nhiễu khuếch tán làm hỏng
        "audio_latent": {"class_type": "LTXVAudioVAEEncode", "inputs": {"audio": ["trim_audio", 0], "audio_vae": ["avae", 0]}},
        "solid_mask_0": {"class_type": "SolidMask", "inputs": {"value": 0.0, "width": 1024, "height": 1024}},
        "frozen_audio": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["audio_latent", 0], "mask": ["solid_mask_0", 0]}},

        # 6. Khởi tạo Video Latent trống
        "empty_vid": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": w,
                "height": h,
                "length": ["frames_expr", 1],
                "batch_size": 1
            }
        },
    }

    # 7. Xử lý Start Image (Nếu người dùng tải ảnh lên để animate)
    vid_latent_ref = ["empty_vid", 0]
    if start_image_filename:
        wf["load_img"] = {"class_type": "LoadImage", "inputs": {"image": start_image_filename}}
        wf["preprocess_img"] = {
            "class_type": "LTXVPreprocess",
            "inputs": {
                "image": ["load_img", 0],
                "img_compression": int(img_compression)
            }
        }
        wf["i2v_inject"] = {
            "class_type": "LTXVImgToVideoInplace",
            "inputs": {
                "latent": ["empty_vid", 0],
                "image": ["preprocess_img", 0],
                "vae": ["vvae", 0],
                "strength": float(img_strength),
                "bypass": False
            }
        }
        vid_latent_ref = ["i2v_inject", 0]

    # 8. Ghép nối Video Latent + Frozen Audio Latent
    wf["concat_av"] = {
        "class_type": "LTXVConcatAVLatent",
        "inputs": {
            "video_latent": vid_latent_ref,
            "audio_latent": ["frozen_audio", 0]
        }
    }

    # 9. STAGE 1: Sampler Distilled (8 bước)
    wf.update({
        "guider":      {"class_type": "CFGGuider", "inputs": {"model": ["unet", 0], "positive": ["cond", 0], "negative": ["cond", 1], "cfg": float(video_cfg)}},
        "noise":       {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "sigmas_s1":   {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS1}},
        "sample_s1": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["noise", 0],
                "guider": ["guider", 0],
                "sampler": ["sampler_sel", 0],
                "sigmas": ["sigmas_s1", 0],
                "latent_image": ["concat_av", 0]
            }
        },
        "sep_av_s1": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["sample_s1", 0]}},
    })

    # Nếu không chạy Stage 2, xuất ngay video từ Stage 1
    if not run_stage2:
        wf.update({
            "vdecode": {
                "class_type": "VAEDecodeTiled",
                "inputs": {
                    "samples": ["sep_av_s1", 0],
                    "vae": ["vvae", 0],
                    "tile_size": 512,
                    "overlap": 64,
                    "temporal_size": 64,
                    "temporal_overlap": 8
                }
            },
            # Sử dụng waveform âm thanh gốc (lossless) từ trim_audio
            "create_vid": {
                "class_type": "CreateVideo",
                "inputs": {
                    "images": ["vdecode", 0],
                    "audio": ["trim_audio", 0],
                    "fps": float(safe_fps),
                    "bit_depth": 8
                }
            },
            "save_vid": {
                "class_type": "SaveVideo",
                "inputs": {
                    "video": ["create_vid", 0],
                    "filename_prefix": "video/LTX_2.5_a2v_Stage1",
                    "format": "auto",
                    "codec": "auto"
                }
            },
        })
        return wf

    # 10. STAGE 2: Spatial Upscale x2 + 3-Step Refiner
    wf.update({
        "upscale_loader": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": SPATIAL_UPSCALER_FILENAME}},
        "upsampler": {
            "class_type": "LTXVLatentUpsampler",
            "inputs": {
                "samples": ["sep_av_s1", 0],
                "upscale_model": ["upscale_loader", 0],
                "vae": ["vvae", 0]
            }
        },
    })

    s2_vid_latent = ["upsampler", 0]
    if start_image_filename:
        wf["s2_i2v_inject"] = {
            "class_type": "LTXVImgToVideoInplace",
            "inputs": {
                "latent": ["upsampler", 0],
                "image": ["load_img", 0],
                "vae": ["vvae", 0],
                "strength": 1.0,
                "bypass": False
            }
        }
        s2_vid_latent = ["s2_i2v_inject", 0]

    # Tiếp tục đóng băng audio latent trong Stage 2
    wf.update({
        "s2_solid_mask_0": {"class_type": "SolidMask", "inputs": {"value": 0.0, "width": 1024, "height": 1024}},
        "s2_frozen_audio": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["audio_latent", 0], "mask": ["s2_solid_mask_0", 0]}},
        "s2_concat_av": {
            "class_type": "LTXVConcatAVLatent",
            "inputs": {
                "video_latent": s2_vid_latent,
                "audio_latent": ["s2_frozen_audio", 0]
            }
        },
        "s2_noise":     {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed) + 1000}},
        "s2_sigmas":    {"class_type": "ManualSigmas", "inputs": {"sigmas": SIGMAS_PASS2}},
        "s2_sample": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["s2_noise", 0],
                "guider": ["guider", 0],
                "sampler": ["sampler_sel", 0],
                "sigmas": ["s2_sigmas", 0],
                "latent_image": ["s2_concat_av", 0]
            }
        },
        "s2_sep_av": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["s2_sample", 0]}},

        # 11. Giải mã Video VAE & Ghép Âm thanh gốc (CreateVideo)
        "vdecode": {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples": ["s2_sep_av", 0],
                "vae": ["vvae", 0],
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 64,
                "temporal_overlap": 8
            }
        },
        "create_vid": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["vdecode", 0],
                "audio": ["trim_audio", 0],
                "fps": float(safe_fps),
                "bit_depth": 8
            }
        },
        "save_vid": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["create_vid", 0],
                "filename_prefix": "video/LTX_2.5_a2v_TwoStage",
                "format": "auto",
                "codec": "auto"
            }
        },
    })

    return wf


# ==============================================================================
# HÀM GỬI PROMPT & THEO DÕI TIẾN TRÌNH COMFYUI
# ==============================================================================
def submit_and_wait_a2v(workflow, max_wait_seconds=1800, poll_interval=2):
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
                yield True, prompt_id, "✅ Hoàn tất render video!"
                return

            prog_text = "Đang lấy mẫu diffusion (Sampling)..."
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
    raise RuntimeError(f"⏰ Quá thời gian chờ ({max_wait_seconds // 60} phút)!")


def find_latest_video(prefix="LTX_2.5_a2v"):
    search_dirs = [
        os.path.join(OUTPUT_DIR, "video"),
        OUTPUT_DIR,
        os.path.join(OUTPUT_DIR, "output"),
    ]
    candidates = []
    for d in search_dirs:
        if os.path.exists(d):
            for ext in ("*.mp4", "*.mkv", "*.mov", "*.webm"):
                for p in glob.glob(os.path.join(d, ext)):
                    candidates.append((os.path.getmtime(p), p))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


# ==============================================================================
# GRADIO DISPATCHER & GIAO DIỆN ĐIỀU KHIỂN
# ==============================================================================
def studio_generate_a2v(
    audio_path,
    start_image_path,
    prompt_text,
    negative_text,
    aspect_ratio,
    duration,
    audio_start,
    v_fps,
    v_seed,
    randomize_seed,
    video_cfg,
    img_strength,
    run_stage2,
    low_vram,
    use_quality_wrap,
):
    if not audio_path or not os.path.exists(audio_path):
        yield None, "⚠️ Vui lòng tải lên file âm thanh (Audio Input) để dẫn đường cho video!"
        return

    if not prompt_text or not prompt_text.strip():
        yield None, "⚠️ Vui lòng nhập prompt mô tả hình ảnh và hành động trên màn hình!"
        return

    # Tự động tính thời lượng nếu người dùng để 0
    audio_len = get_audio_duration(audio_path)
    if duration <= 0:
        duration = min(audio_len - float(audio_start), 15.0)
        duration = max(duration, 2.0)

    width, height = parse_aspect_ratio(aspect_ratio)

    yield None, "🔄 Đang kiểm tra và khởi động ComfyUI server..."
    try:
        ensure_server(low_vram=low_vram)
    except Exception as e:
        yield None, f"❌ Lỗi máy chủ: {e}"
        return

    # Seed
    if randomize_seed or not v_seed:
        active_seed = random.randint(1, 999_999_999)
    else:
        try:
            active_seed = int(v_seed)
        except Exception:
            active_seed = random.randint(1, 999_999_999)

    # Sao chép file vào input ComfyUI
    os.makedirs(INPUT_DIR, exist_ok=True)
    audio_ext = os.path.splitext(audio_path)[1] or ".wav"
    audio_name = f"a2v_audio_{int(time.time())}{audio_ext}"
    shutil.copy2(audio_path, os.path.join(INPUT_DIR, audio_name))

    start_img_name = None
    if start_image_path and os.path.exists(start_image_path):
        img_ext = os.path.splitext(start_image_path)[1] or ".png"
        start_img_name = f"a2v_start_{int(time.time())}{img_ext}"
        shutil.copy2(start_image_path, os.path.join(INPUT_DIR, start_img_name))

    # Bọc prompt chất lượng cao nếu được chọn
    final_prompt = prompt_text.strip()
    if use_quality_wrap:
        final_prompt = f"{QUALITY_PREFIX}{final_prompt}{QUALITY_SUFFIX}"

    yield None, f"📐 Đang dựng workflow A2V (Độ phân giải: {width}x{height}, Thời lượng: {duration:.1f}s, Seed: {active_seed})..."
    wf = build_a2v_workflow(
        audio_filename=audio_name,
        start_image_filename=start_img_name,
        positive_prompt=final_prompt,
        negative_prompt=negative_text or NEGATIVE_PROMPT_DEFAULT,
        width=width,
        height=height,
        fps=v_fps,
        audio_start=float(audio_start),
        duration=float(duration),
        seed=active_seed,
        video_cfg=float(video_cfg),
        img_strength=float(img_strength),
        img_compression=18,
        run_stage2=bool(run_stage2),
    )

    t_start = time.time()
    for done, prompt_id, prog_text in submit_and_wait_a2v(wf):
        elapsed = int(time.time() - t_start)
        if not done:
            yield None, f"⏳ [Tiến trình: {elapsed}s] {prog_text}"
        else:
            yield None, f"🎉 Đang hoàn tất video trong {elapsed}s..."

    final_vid = find_latest_video()
    if final_vid and os.path.exists(final_vid):
        yield final_vid, f"✅ Xuất video thành công: {os.path.basename(final_vid)} ({int(time.time() - t_start)}s)"
    else:
        yield None, "⚠️ Không tìm thấy file video đầu ra trong thư mục output!"


# ==============================================================================
# CSS & THIẾT KẾ GIAO DIỆN GRADIO
# ==============================================================================
custom_css = """
.gradio-container { max-width: 1400px !important; margin: 0 auto !important; font-family: 'Inter', -apple-system, sans-serif !important; }
#a2v-header {
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #a855f7 100%);
    border-radius: 16px; padding: 24px 30px; margin-bottom: 16px; color: #fff;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);
}
#a2v-header h1 { margin: 0 0 6px 0 !important; color: #fff !important; font-size: 1.8rem !important; }
#a2v-header p { margin: 0 !important; color: #e0e7ff !important; font-size: 0.95rem !important; }
.status-box textarea { font-family: 'Consolas', monospace !important; font-size: 0.88rem !important; }
.btn-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; font-weight: 600 !important; }
"""

with gr.Blocks(title="LTX-2.5 A2V Studio - Audio to Video", css=custom_css) as demo:
    gr.HTML(
        """
        <div id="a2v-header">
            <h1>🎙️ LTX-2.5 A2V Studio — Audio to Video Two-Stage Distilled</h1>
            <p>Mô hình điện ảnh tạo video đồng bộ từ Âm thanh (Lời thoại, Nhạc điệu) với cơ chế Audio Latent Freezing & Lossless Audio Muxing.</p>
        </div>
        """
    )

    with gr.Row():
        # CỘT TRÁI: INPUTS
        with gr.Column(scale=5):
            with gr.Group():
                gr.Markdown("### 1. 🎵 Âm thanh & Khung hình đầu (Inputs)")
                audio_in = gr.Audio(label="Tải lên Âm thanh (Audio Input - Bắt buộc)", type="filepath")
                start_image_in = gr.Image(label="Ảnh khung hình đầu (Start Frame Still - Tùy chọn)", type="filepath")

            with gr.Group():
                gr.Markdown("### 2. 📝 Kịch bản & Prompt")
                prompt_in = gr.Textbox(
                    label="Mô tả bối cảnh và diễn biến (Prompt)",
                    lines=3,
                    placeholder="A charismatic singer performing on a dimly lit jazz stage with warm amber spotlight, expressive lips moving naturally to the rhythm, shallow depth of field...",
                )
                neg_prompt_in = gr.Textbox(
                    label="Negative Prompt (Chặn lỗi)",
                    lines=2,
                    value=NEGATIVE_PROMPT_DEFAULT,
                )
                quality_wrap_in = gr.Checkbox(label="Tự động thêm tiền tố / hậu tố Cinema 4K", value=True)

            with gr.Group():
                gr.Markdown("### 3. ⚙️ Thông số Render")
                with gr.Row():
                    aspect_in = gr.Dropdown(
                        choices=[
                            "16:9 Landscape (960x544 - Chuẩn A2V Stage 1)",
                            "9:16 Vertical (544x960 - TikTok/Reels/Shorts)",
                            "1:1 Square (640x640 - Vuông)",
                            "4:3 Classic TV (768x576)",
                            "21:9 Ultrawide Cinema (1024x448)",
                        ],
                        value="16:9 Landscape (960x544 - Chuẩn A2V Stage 1)",
                        label="Tỷ lệ khung hình (Aspect Ratio)",
                    )
                    fps_in = gr.Dropdown(choices=[24, 25, 30], value=24, label="FPS")

                with gr.Row():
                    duration_in = gr.Slider(minimum=0.0, maximum=15.0, value=5.0, step=0.5, label="Thời lượng (giây - 0 là Tự động)")
                    audio_start_in = gr.Slider(minimum=0.0, maximum=60.0, value=0.0, step=0.5, label="Cắt từ giây thứ (Audio Start)")

                with gr.Row():
                    stage2_in = gr.Checkbox(label="Chạy Stage 2 (x2 Spatial Upscale + 3-step Refiner)", value=True)
                    lowvram_in = gr.Checkbox(label="Chế độ tiết kiệm VRAM (--lowvram)", value=True)

                with gr.Accordion("🛠️ Tùy chọn Nâng cao (CFG, Image Strength, Seed)", open=False):
                    with gr.Row():
                        cfg_in = gr.Slider(minimum=1.0, maximum=3.0, value=1.0, step=0.1, label="Video CFG Scale")
                        img_str_in = gr.Slider(minimum=0.1, maximum=1.0, value=0.7, step=0.05, label="Độ bám ảnh Start Frame")
                    with gr.Row():
                        seed_in = gr.Textbox(label="Seed", value="", placeholder="Để trống nếu muốn ngẫu nhiên")
                        random_seed_in = gr.Checkbox(label="Randomize Seed", value=True)

            gen_btn = gr.Button("🚀 BẮT ĐẦU RENDER VIDEO A2V", elem_classes=["btn-primary"], size="lg")

        # CỘT PHẢI: KẾT QUẢ & STATUS
        with gr.Column(scale=5):
            status_box = gr.Textbox(label="Trạng thái & Tiến trình", lines=3, elem_classes=["status-box"])
            video_out = gr.Video(label="Video Thành Phẩm (A2V Master)", interactive=False)

    gen_btn.click(
        fn=studio_generate_a2v,
        inputs=[
            audio_in,
            start_image_in,
            prompt_in,
            neg_prompt_in,
            aspect_in,
            duration_in,
            audio_start_in,
            fps_in,
            seed_in,
            random_seed_in,
            cfg_in,
            img_str_in,
            stage2_in,
            lowvram_in,
            quality_wrap_in,
        ],
        outputs=[video_out, status_box],
    )


if __name__ == "__main__":
    demo.queue().launch(share=True, inbrowser=True)
