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

get_ipython().system("pip install -q gradio")

import json
import math
import os
import random
import shutil
import socket
import subprocess
import time
import urllib.request

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
    "subtitles, watermark, worst quality, blurry, jittery, distorted, inconsistent appearance"
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
    import glob
    mp4_files = (
        glob.glob(f"{output_dir}*.mp4")
        + glob.glob(f"{output_dir}output/*.mp4")
        + glob.glob(f"{output_dir}video/*.mp4")
    )
    if not mp4_files:
        return None
    return max(mp4_files, key=os.path.getmtime)


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
    msr_lora_name=None,
    msr_lora_strength=1.0,
    pic1_name=None,
    pic2_name=None,
    pic3_name=None,
    pic4_name=None,
    background_name=None,
    msr_strength=1.0,
    reference_frames="33",
    use_tiled_encode=False,
    tile_size=256,
    run_stage2=True,
):
    """Build workflow MSR 2-stage theo LTX2.5-MSR-sample-workflow.json.

    Stage 1: UNETLoader -> ComfyUILTX25MSRICLoRALoader
             PromptRelayEncode -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide
             CFGGuider -> SamplerCustomAdvanced -> SaveVideo (1/2 res)

    Stage 2: LTXVLatentUpsampler -> PromptRelayEncode -> LTXVConditioning
             ComfyUILTX25MSRMultiReferenceGuide -> LTXVDualCFGGuider
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
            "inputs": {"model": ["S1_msr_loader", 0], "clip": ["S1_clip", 0], "latent": ["S1_empty_vid", 0],
                       "character_description": prompt_relay_desc, "prompt": prompt_main, "negative_text": "", "relay_strength": 0.001},
        },
        "S1_ltxv_cond": {"class_type": "LTXVConditioning", "inputs": {"positive": ["S1_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": ["S1_fps", 0]}},
    }

    msr_s1 = {
        "positive": ["S1_ltxv_cond", 0], "negative": ["S1_ltxv_cond", 1],
        "vae": ["S1_vvae", 0], "latent": ["S1_empty_vid", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": float(msr_strength), "reference_frames": reference_frames,
        "use_tiled_encode": use_tiled_encode, "tile_size": tile_size, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            wf[f"S1_load_{slot}"] = {"class_type": "LoadImage", "inputs": {"image": img}}
            msr_s1[slot] = [f"S1_load_{slot}", 0]
    wf["S1_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s1}

    wf.update({
        "S1_cfg_guider":  {"class_type": "CFGGuider",           "inputs": {"model": ["S1_relay", 0], "positive": ["S1_msr_guide", 0], "negative": ["S1_msr_guide", 1], "cfg": 1.0}},
        "S1_noise":       {"class_type": "RandomNoise",          "inputs": {"noise_seed": int(seed)}},
        "S1_sampler_sel": {"class_type": "KSamplerSelect",       "inputs": {"sampler_name": "euler_ancestral"}},
        "S1_sigmas":      {"class_type": "ManualSigmas",         "inputs": {"sigmas": SIGMAS_PASS1}},
        "S1_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S1_msr_guide", 2], "audio_latent": ["S1_empty_aud", 0]}},
        "S1_sample":      {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["S1_noise", 0], "guider": ["S1_cfg_guider", 0], "sampler": ["S1_sampler_sel", 0], "sigmas": ["S1_sigmas", 0], "latent_image": ["S1_concat_av", 0]}},
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
        "S2_upsampler":      {"class_type": "LTXVLatentUpsampler",       "inputs": {"samples": ["S1_sep_av", 0], "upscale_model": ["S2_upscale_loader", 0], "vae": ["S1_vvae", 0]}},
        "S2_relay": {
            "class_type": "PromptRelayEncode",
            "inputs": {"model": ["S1_msr_loader", 0], "clip": ["S1_clip", 0], "latent": ["S2_upsampler", 0],
                       "character_description": prompt_relay_desc, "prompt": prompt_main, "negative_text": "", "relay_strength": 0.001},
        },
        "S2_ltxv_cond": {"class_type": "LTXVConditioning", "inputs": {"positive": ["S2_relay", 1], "negative": ["S1_neg_enc", 0], "frame_rate": ["S1_fps", 0]}},
    })

    msr_s2 = {
        "positive": ["S2_ltxv_cond", 0], "negative": ["S2_ltxv_cond", 1],
        "vae": ["S1_vvae", 0], "latent": ["S2_upsampler", 0],
        "msr_parameters": ["S1_msr_loader", 1],
        "strength": float(msr_strength), "reference_frames": reference_frames,
        "use_tiled_encode": use_tiled_encode, "tile_size": tile_size, "tile_overlap": 0,
    }
    for slot, img in pic_slot_map:
        if img:
            msr_s2[slot] = [f"S1_load_{slot}", 0]
    wf["S2_msr_guide"] = {"class_type": "ComfyUILTX25MSRMultiReferenceGuide", "inputs": msr_s2}

    wf.update({
        "S2_concat_av":   {"class_type": "LTXVConcatAVLatent",   "inputs": {"video_latent": ["S2_msr_guide", 2], "audio_latent": ["S1_sep_av", 1]}},
        "S2_dual_guider": {"class_type": "LTXVDualCFGGuider",    "inputs": {"model": ["S2_relay", 0], "positive": ["S2_msr_guide", 0], "negative": ["S2_msr_guide", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "S2_noise":       {"class_type": "RandomNoise",           "inputs": {"noise_seed": PASS2_FIXED_NOISE_SEED}},
        "S2_sampler_sel": {"class_type": "KSamplerSelect",        "inputs": {"sampler_name": "euler_ancestral"}},
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


# ==========================================================================
# GENERATE
# ==========================================================================
def generate_msr_gradio(
    pic1_path, pic2_path, pic3_path, pic4_path, background_path,
    prompt_relay_desc, prompt_main, negative_text,
    aspect_ratio, v_length, v_fps, v_seed,
    msr_lora_name, msr_lora_strength, msr_strength,
    reference_frames, use_tiled_encode,
    run_stage2, low_vram,
):
    if not pic1_path:
        yield None, "[!] Vui long tai anh Pic 1 (bat buoc)."; return
    if not prompt_main or not prompt_main.strip():
        yield None, "[!] Vui long nhap Prompt chinh."; return

    v_width, v_height       = parse_aspect_ratio(aspect_ratio)
    safe_width, safe_height = safe_dims(v_width, v_height)

    yield None, "[~] Dang kiem tra / khoi dong ComfyUI server..."
    try:
        ensure_server(low_vram)
    except Exception as e:
        yield None, f"[X] {e}"; return

    seed = get_seed(v_seed)
    yield None, f"[OK] Server san sang. Seed: {seed}"
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

    loaded     = [s for s in [pic1_name, pic2_name, pic3_name, pic4_name, bg_name] if s]
    stage_note = "Stage 1+2 (upscale x2)" if run_stage2 else "Stage 1 only"
    yield None, (
        f"[~] Dang render [{stage_note}]...\n"
        f"Anh: {len(loaded)} slot | LoRA: {msr_lora_name}\n"
        f"Kich thuoc: {safe_width}x{safe_height} | {v_length}s | {snap_fps_safe(v_fps)}fps"
    )

    wf = build_msr_workflow(
        prompt_relay_desc = prompt_relay_desc or "",
        prompt_main       = prompt_main,
        negative_text     = negative_text or NEGATIVE_PROMPT_DEFAULT,
        width=safe_width, height=safe_height,
        fps=v_fps, duration=v_length, seed=seed,
        msr_lora_name=msr_lora_name, msr_lora_strength=msr_lora_strength,
        pic1_name=pic1_name, pic2_name=pic2_name,
        pic3_name=pic3_name, pic4_name=pic4_name, background_name=bg_name,
        msr_strength=msr_strength, reference_frames=str(reference_frames),
        use_tiled_encode=bool(use_tiled_encode), run_stage2=bool(run_stage2),
    )

    try:
        submit_and_wait(wf, scene_label="MSR")
    except Exception as e:
        yield None, f"[X] {e}"; return

    latest_video = find_latest_video()
    if not latest_video:
        yield None, "[!] Khong tim thay file video dau ra!"; return

    yield latest_video, f"[DING] Hoan tat! Video da luu. (Seed: {seed})"


# ==========================================================================
# GRADIO UI
# ==========================================================================
ratio_choices = [
    "16:9 (1280x720) - HD 720p Ngang",
    "9:16 (720x1280) - HD 720p Doc",
    "1:1 (720x720) - HD 720p Vuong",
    "16:9 (832x480) - Nhe / Tiet kiem VRAM",
    "9:16 (480x832) - Nhe / Tiet kiem VRAM",
]

custom_css = """
.gradio-container { max-width: 1440px; margin: 0 auto; }
#msr-header { background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
              border-radius:16px; padding:20px 26px; margin-bottom:14px; }
#msr-header h1, #msr-header p { color:#fff !important; margin:0 !important; }
.info-box { background:rgba(99,102,241,.08); border-left:3px solid #6366f1;
            padding:10px 14px; border-radius:8px; font-size:.87rem;
            margin-bottom:8px; }
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
            g.exponentialRampToValueAtTime(.01,c.currentTime+.4);
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
                    "# LTX-2.5 MSR Studio\n"
                    "Multi-Subject Reference - Tao video tu nhieu anh tham khao nhan vat\n\n"
                    "LTX-2.5 | Toi da 4 nhan vat + 1 nen | 2-Stage: Generation + Latent x2 Upscale"
                )
            with gr.Column(scale=1, min_width=160):
                restart_btn = gr.Button("Restart Server", size="sm")
                restart_out = gr.Markdown("San sang")
        restart_btn.click(fn=force_restart_server, outputs=[restart_out])

    with gr.Row():
        with gr.Column(scale=5):

            with gr.Group():
                gr.Markdown("### Anh tham khao nhan vat / boi canh")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Thu tu slot co dinh: Pic 1 - Pic 2 - Pic 3 - Pic 4 - Background. "
                    "Chi Pic 1 bat buoc, cac slot con lai tuy chon."
                    "</div>"
                )
                with gr.Row():
                    msr_pic1 = gr.Image(label="Pic 1 - Nhan vat 1 (bat buoc)", type="filepath")
                    msr_pic2 = gr.Image(label="Pic 2 - Nhan vat 2 (tuy chon)", type="filepath")
                with gr.Row():
                    msr_pic3 = gr.Image(label="Pic 3 - Nhan vat 3 (tuy chon)", type="filepath")
                    msr_pic4 = gr.Image(label="Pic 4 - Nhan vat 4 (tuy chon)", type="filepath")
                msr_bg = gr.Image(label="Background - Boi canh (tuy chon)", type="filepath")

            with gr.Group():
                gr.Markdown("### Prompt")
                gr.Markdown(
                    "<div class='info-box'>"
                    "PromptRelayEncode dung 2 truong rieng biet:<br>"
                    "(1) Mo ta nhan vat: mo ta tung nhan vat theo thu tu slot (Image 1: ... / Image 2: ...)<br>"
                    "(2) Prompt chinh: kich ban hanh dong video day du"
                    "</div>"
                )
                msr_relay_desc = gr.Textbox(
                    label="(1) Mo ta nhan vat (character_description)",
                    lines=5,
                    placeholder=(
                        "Image 1: Beast-girl, fluffy orange cat ears, big amber eyes, "
                        "cream-white puffy dress, Pixar-style 3D cartoon rendering.\n\n"
                        "Image 2: Elf girl, long pointed ears, silver-white long hair, "
                        "leaf-green robe, Pixar-style 3D cartoon rendering.\n\n"
                        "Image 3: Scene, enchanted forest clearing, warm golden light."
                    ),
                )
                msr_prompt = gr.Textbox(
                    label="(2) Prompt chinh - hanh dong / kich ban",
                    lines=6,
                    placeholder=(
                        "A clearing in an enchanted forest, warm dappled golden light. "
                        "[Shot 1] Wide two-shot: the beast-girl and elf girl stand in the clearing "
                        "as camera slow-dolly-pushes in 30%..."
                    ),
                )
                msr_neg = gr.Textbox(
                    label="Negative Prompt",
                    lines=2,
                    value=NEGATIVE_PROMPT_DEFAULT,
                )

            with gr.Accordion("Cai dat nang cao", open=False):
                gr.Markdown("**Kich thuoc & thoi luong**")
                ratio_msr = gr.Radio(
                    label="Ti le khung hinh",
                    choices=ratio_choices,
                    value=ratio_choices[0],
                    info="Stage 1 chay 1/2 res, Stage 2 upscale x2 ve full res",
                )
                with gr.Row():
                    length_msr = gr.Slider(label="Thoi luong (giay)", minimum=1, maximum=10, step=1, value=10)
                    fps_msr    = gr.Slider(label="FPS", minimum=8, maximum=120, step=8, value=24)
                seed_msr = gr.Number(label="Seed (-1 = ngau nhien)", value=-1, precision=0)

                gr.Markdown("**MSR LoRA**")
                gr.Markdown(
                    "<div class='info-box'>"
                    "Dat file LoRA vao /content/ComfyUI/models/loras/ltx2.5/ roi nhan Refresh."
                    "</div>"
                )
                with gr.Row():
                    msr_lora_dd = gr.Dropdown(
                        label="MSR LoRA", choices=list_msr_loras(), value=MSR_LORA_FILENAME, scale=3)
                    msr_lora_str_sl = gr.Slider(
                        label="LoRA strength", minimum=0.0, maximum=2.0, step=0.05, value=1.0, scale=2)
                msr_refresh_btn = gr.Button("Refresh MSR LoRA", size="sm")
                msr_refresh_btn.click(fn=lambda: gr.update(choices=list_msr_loras()), outputs=[msr_lora_dd])

                gr.Markdown("**Cai dat MSR Guide**")
                msr_guide_str_sl = gr.Slider(
                    label="Reference strength", minimum=0.0, maximum=2.0, step=0.05, value=1.0,
                    info="Do bam anh tham khao - 1.0 bam sat nhat")
                with gr.Row():
                    msr_ref_frames = gr.Radio(
                        label="Reference frames", choices=["25", "33"], value="33",
                        info="33 = mac dinh MSR chinh thuc")
                    msr_tiled = gr.Checkbox(label="Tiled VAE encode", value=False)

                gr.Markdown("**Pipeline**")
                with gr.Row():
                    msr_stage2   = gr.Checkbox(label="Chay Stage 2 (upscale x2 + refine)", value=True)
                    msr_low_vram = gr.Checkbox(label="Low VRAM Mode", value=True)

        with gr.Column(scale=5):
            with gr.Group():
                msr_video_out = gr.Video(label="MSR Output Video", height=420)
                with gr.Row():
                    msr_btn   = gr.Button("Tao Video MSR", variant="primary", scale=3)
                    msr_clear = gr.Button("Clear", scale=1)
                msr_status = gr.Textbox(
                    label="Status / Log", interactive=False, lines=5, elem_classes="status-box")

            gr.Markdown(
                "<div class='info-box'>"
                "<b>Custom nodes can cai:</b><br>"
                "- ComfyUI-LTX2.5-MSR : liconstudio/ComfyUI-LTX2.5-MSR<br>"
                "- ComfyUI-PromptRelay : kijai/ComfyUI-PromptRelay<br>"
                "- ComfyUI-KJNodes     : kijai/ComfyUI-KJNodes<br><br>"
                "<b>Models can thiet:</b><br>"
                "- UNET     -> models/diffusion_models/<br>"
                "- CLIP     -> models/text_encoders/<br>"
                "- VAE      -> models/vae/<br>"
                "- Upscaler -> models/<br>"
                "- MSR LoRA -> models/loras/ltx2.5/"
                "</div>"
            )

    msr_btn.click(
        fn=generate_msr_gradio,
        inputs=[
            msr_pic1, msr_pic2, msr_pic3, msr_pic4, msr_bg,
            msr_relay_desc, msr_prompt, msr_neg,
            ratio_msr, length_msr, fps_msr, seed_msr,
            msr_lora_dd, msr_lora_str_sl, msr_guide_str_sl,
            msr_ref_frames, msr_tiled,
            msr_stage2, msr_low_vram,
        ],
        outputs=[msr_video_out, msr_status],
    )
    msr_clear.click(fn=lambda: (None, ""), outputs=[msr_video_out, msr_status])

demo.queue()
demo.launch(share=True, inline=False, debug=True)
