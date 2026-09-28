#@title 🎬 Cell 2: MiniMax H3 — Gradio Live UI (MSR & I2V Auto-Chaining) — UPGRADED
import glob, json, os, random, re, shutil, socket, subprocess, time, urllib.request
import cv2
import gradio as gr

# ==========================================================================
# CONFIG
# ==========================================================================
INPUT_DIR  = "/content/ComfyUI/input/"
OUTPUT_DIR = "/content/ComfyUI/output/"
COMFYUI_DIR = "/content/ComfyUI"
COMFYUI_LOG_PATH = "/content/comfyui.log"

_SERVER_STATE = {"running_low_vram": None, "custom_nodes_mtime": None, "fast_mode": None}

def is_server_running(port=8188):
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/system_stats")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception: return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception: return False

def _get_custom_nodes_mtime():
    cn_dir = os.path.join(COMFYUI_DIR, "custom_nodes")
    try:
        mtimes = []
        for entry in os.scandir(cn_dir):
            mtimes.append(entry.stat().st_mtime)
            if entry.is_dir():
                try:
                    for sub in os.scandir(entry.path):
                        if sub.name.endswith(".py"): mtimes.append(sub.stat().st_mtime)
                except OSError: pass
        return max(mtimes) if mtimes else 0.0
    except OSError: return 0.0

def ensure_server(low_vram=True, fast_mode=True, boot_timeout=120):
    main_py = os.path.join(COMFYUI_DIR, "main.py")
    if not os.path.exists(main_py): raise RuntimeError("❌ /content/ComfyUI/main.py không tồn tại! Chạy lại Cell 1.")
    current_mtime = _get_custom_nodes_mtime()
    if is_server_running():
        if (_SERVER_STATE["running_low_vram"] is None or
            (_SERVER_STATE["running_low_vram"] == low_vram and
             _SERVER_STATE["custom_nodes_mtime"] == current_mtime and
             _SERVER_STATE["fast_mode"] == fast_mode)):
            _SERVER_STATE["running_low_vram"] = low_vram
            _SERVER_STATE["custom_nodes_mtime"] = current_mtime
            _SERVER_STATE["fast_mode"] = fast_mode
            return
    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    time.sleep(2)
    os.chdir(COMFYUI_DIR)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    log_out = open(COMFYUI_LOG_PATH, "w", encoding="utf-8", errors="ignore")
    cmd = ["python", "-u", "main.py", "--listen", "127.0.0.1", "--port", "8188"]
    if low_vram: cmd.extend(["--lowvram", "--cache-none"])
    # ⭐ --fast flag: bật fp16_accumulation cho convolutions, tăng tốc VAE encoder ~2.2x
    if fast_mode: cmd.append("--fast")
    proc = subprocess.Popen(cmd, cwd=COMFYUI_DIR, stdout=log_out, stderr=subprocess.STDOUT)
    waited = 0
    while not is_server_running():
        time.sleep(2); waited += 2
        if proc.poll() is not None or waited > boot_timeout:
            raise RuntimeError("Server crash or timeout!")
    _SERVER_STATE["running_low_vram"] = low_vram
    _SERVER_STATE["custom_nodes_mtime"] = current_mtime
    _SERVER_STATE["fast_mode"] = fast_mode

def force_restart_server():
    os.system("fuser -k 8188/tcp 2>/dev/null || true")
    os.system("pkill -9 -f 'python.*main.py' 2>/dev/null || true")
    time.sleep(2)
    _SERVER_STATE["running_low_vram"] = None
    _SERVER_STATE["custom_nodes_mtime"] = None
    _SERVER_STATE["fast_mode"] = None
    return "🟢 Server đã tắt. Lần tạo video tiếp sẽ tự khởi động lại."

def free_comfyui_memory():
    for endpoint, payload in [("interrupt", b"{}"), ("queue", json.dumps({"clear": True}).encode()), ("free", json.dumps({"unload_models": True, "free_memory": True}).encode())]:
        try: urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:8188/{endpoint}", data=payload, headers={"Content-Type": "application/json"}), timeout=5)
        except Exception: pass
    try:
        import torch
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    except Exception: pass
    return "🟢 Đã giải phóng GPU VRAM!"

def read_server_log():
    if not os.path.exists(COMFYUI_LOG_PATH): return "ℹ️ Chưa có log."
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            return "".join(f.readlines()[-40:]) or "ℹ️ Log rỗng."
    except Exception as e: return f"⚠️ Lỗi đọc log: {e}"

# ==========================================================================
# HELPERS
# ==========================================================================
def get_seed(v):
    try: v = int(v)
    except Exception: v = -1
    return random.randint(1, 999_999_999) if v == -1 else v

def get_comfyui_progress_line():
    if not os.path.exists(COMFYUI_LOG_PATH): return ""
    try:
        with open(COMFYUI_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for l in reversed(lines[-20:]):
            s = l.strip()
            if "%" in s or "it/s" in s or "s/it" in s or "Executing node" in s:
                return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)[:100]
    except Exception: pass
    return ""

def parse_resolution(ratio_str):
    if "864x480"   in ratio_str: return 864,  480
    if "480x864"   in ratio_str: return 480,  864
    if "1344x768"  in ratio_str: return 1344, 768
    if "768x1344"  in ratio_str: return 768,  1344
    if "1056x1056" in ratio_str: return 1056, 1056
    return 864, 480

def duration_to_length(duration_s, fps):
    raw = int(round(float(duration_s) * float(fps)))
    n = max(1, round((raw - 1) / 4))
    return 4 * n + 1

def split_prompts(text):
    if not text: return []
    parts = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in parts if p.strip()]

def count_scenes(text):
    return f"🔹 **Số phân cảnh:** {len(split_prompts(text))}"

def extract_last_frame(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total - 1))
    ret, frame = cap.read()
    if ret: cv2.imwrite(output_path, frame)
    cap.release()

def concat_videos(video_paths, output_name):
    list_path = os.path.join(OUTPUT_DIR, f"{output_name}_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for v in video_paths: f.write(f"file '{os.path.abspath(v)}'\n")
    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp4")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_path]
    subprocess.run(cmd, capture_output=True)
    return output_path

# ==========================================================================
# ⭐ VIDEO POST-PROCESSING — Nâng cao chất lượng sau decode
# ==========================================================================
def post_process_video_ffmpeg(input_path, output_path, sharpen=True, denoise_light=True):
    """
    Post-process video bằng ffmpeg:
    - Sharpen nhẹ (unsharp) để bù mềm từ VAE decode
    - Denoise nhẹ (hqdn3d) để giảm noise mà VAE có thể tạo ra
    - Encode lại với CRF thấp (chất lượng cao)
    """
    filters = []
    if denoise_light:
        filters.append("hqdn3d=1.5:1.5:3:3")
    if sharpen:
        filters.append("unsharp=5:5:0.5:5:5:0.0")  # nhẹ, không quá sắc

    vf = ",".join(filters) if filters else None
    cmd = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd.extend(["-vf", vf])
    # CRF 18 = chất lượng cao, gần lossless
    cmd.extend(["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", output_path])
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    return output_path if result.returncode == 0 else input_path

# ==========================================================================
# BUILD WORKFLOW — UPGRADED
# ==========================================================================
def build_minimax_workflow(*, prompt, width, height, duration_s, fps, seed, scheduler,
                           steps_full=20, steps_turbo=4, use_turbo_lora, op_mode,
                           ref_image_size, pic1, pic2, pic3, pic4,
                           vae_mode="int8", use_tiled_decode=False,
                           tile_size=512, tile_overlap=128,
                           temporal_size=48, temporal_overlap=40,
                           turbo_variant="8-step v1.0 ⭐",
                           text_encoder_mode="int8"):
    is_i2v = (op_mode != "MSR (Tham chiếu đa bối cảnh)")
    unet_name = "minimax_h3_fl2va_pruned_int8_convrot.safetensors" if is_i2v else "minimax_h3_ref2va_pruned_int8_convrot.safetensors"

    # ⭐ Chọn Turbo LoRA theo variant
    if "8-step" in turbo_variant:
        if is_i2v:
            lora_name = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
        else:
            lora_name = "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
        steps_turbo = 8
    elif "v1.2" in turbo_variant:
        if is_i2v:
            lora_name = "minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors"
        else:
            # v1.2 chỉ có cho fl2v, fallback sang 4-step v0.1 cho ref2v
            lora_name = "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"
        steps_turbo = 4
    else:  # 4-step v1.0 (gốc)
        if is_i2v:
            lora_name = "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"
        else:
            lora_name = "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"
        steps_turbo = 4

    length = duration_to_length(duration_s, fps)

    # ⭐ Chọn Video VAE theo chế độ
    if vae_mode == "int8":
        video_vae_name = "minimax_h3_video_vae_int8_convrot.safetensors"
    else:
        video_vae_name = "minimax_h3_video_vae_fp16.safetensors"

    # ⭐ Chọn Text Encoder theo precision
    TEXT_ENCODER_MAP = {
        "int8": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
        "fp4":  "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    }
    clip_name = TEXT_ENCODER_MAP.get(text_encoder_mode, TEXT_ENCODER_MAP["int8"])

    # ⭐ Chọn model source: nếu dùng turbo thì qua LoRA, nếu không thì UNET trực tiếp
    actual_steps = steps_turbo if use_turbo_lora else steps_full

    wf = {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": unet_name, "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip_name, "type": "minimax", "device": "default"}},
        "video_vae": {"class_type": "VAELoader", "inputs": {"vae_name": video_vae_name}},
        "audio_vae": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "sampler_sel": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
    }

    # ⭐ Model source: UNET trực tiếp hoặc qua LoRA
    if use_turbo_lora:
        wf["turbo_lora"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["unet", 0], "lora_name": lora_name, "strength_model": 1.0}}
        model_ref = ["turbo_lora", 0]
    else:
        model_ref = ["unet", 0]

    wf["scheduler_node"] = {"class_type": "BasicScheduler", "inputs": {"model": model_ref, "scheduler": scheduler, "steps": actual_steps, "denoise": 1.0}}
    wf["sampler"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_sel", 0], "sigmas": ["scheduler_node", 0], "latent_image": ["core_node", 1]}}

    # ⭐ VAE Decode: Tiled hoặc Standard
    if use_tiled_decode:
        wf["vae_dec"] = {
            "class_type": "VAEDecodeTiled",
            "inputs": {
                "samples": ["sampler", 0],
                "vae": ["video_vae", 0],
                "tile_size": tile_size,
                "overlap": tile_overlap,
            }
        }
    else:
        wf["vae_dec"] = {"class_type": "VAEDecode", "inputs": {"samples": ["sampler", 0], "vae": ["video_vae", 0]}}

    wf["audio_dec"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["sampler", 0], "vae": ["audio_vae", 0]}}
    wf["create_vid"] = {"class_type": "CreateVideo", "inputs": {"images": ["vae_dec", 0], "audio": ["audio_dec", 0], "fps": fps}}
    wf["save_vid"] = {"class_type": "SaveVideo", "inputs": {"video": ["create_vid", 0], "filename_prefix": "video/MM_H3", "format": "auto", "codec": "auto"}}

    if is_i2v:
        wf["core_node"] = {
            "class_type": "MiniMaxH3ImageToVideo",
            "inputs": {"clip": ["clip", 0], "vae": ["video_vae", 0], "prompt": prompt, "width": int(width), "height": int(height), "length": int(length)}
        }
        if pic1:
            wf["load_first"] = {"class_type": "LoadImage", "inputs": {"image": pic1}}
            wf["core_node"]["inputs"]["first_frame"] = ["load_first", 0]
        if pic2 and op_mode == "I2V (Nội suy ảnh A -> B)":
            wf["load_last"] = {"class_type": "LoadImage", "inputs": {"image": pic2}}
            wf["core_node"]["inputs"]["last_frame"] = ["load_last", 0]
    else:
        wf["core_node"] = {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {"clip": ["clip", 0], "vae": ["video_vae", 0], "audio_vae": ["audio_vae", 0], "prompt": prompt, "width": int(width), "height": int(height), "length": int(length), "ref_image_size": ref_image_size}
        }
        for i, img in enumerate([pic1, pic2, pic3, pic4]):
            if img:
                nid = f"load_{i}"
                wf[nid] = {"class_type": "LoadImage", "inputs": {"image": img}}
                wf["core_node"]["inputs"][f"ref_images.ref_image_{i}"] = [nid, 0]

    wf["guider"] = {"class_type": "BasicGuider", "inputs": {"model": model_ref, "conditioning": ["core_node", 0]}}
    return wf

def submit_and_wait_gen(workflow, scene_label="", max_wait_seconds=1800, poll_interval=3):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        prompt_id = json.loads(urllib.request.urlopen(req, timeout=30).read())["prompt_id"]
    except Exception as e:
        free_comfyui_memory()
        raise RuntimeError(f"Lỗi API: {e}")
    waited = 0
    poll_count = 0
    while waited < max_wait_seconds:
        try:
            history = json.loads(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}"), timeout=30).read())
            if str(prompt_id) in history: yield True, prompt_id, "Hoàn tất"; return
            queue = json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8188/queue"), timeout=30).read())
            is_running = any(str(job[1]) == str(prompt_id) for job in queue.get("queue_running", []) + queue.get("queue_pending", []))
            poll_count += 1
            if not is_running and poll_count > 3: raise RuntimeError("Render thất bại")
            p_line = get_comfyui_progress_line()
            m, s = divmod(waited, 60)
            yield False, prompt_id, f"[{m:02d}m{s:02d}s] {p_line}" if p_line else f"[{m:02d}m{s:02d}s] Đang tính..."
        except Exception: pass
        time.sleep(poll_interval); waited += poll_interval
    free_comfyui_memory()
    raise RuntimeError("Timeout!")

# ==========================================================================
# GRADIO GENERATOR — UPGRADED
# ==========================================================================
def generate_minimax_gradio(
    op_mode, pic1_path, pic2_path, pic3_path, pic4_path, prompt_main,
    aspect_ratio, duration_s, fps, seed_val, num_segments, fixed_seed,
    scheduler, use_turbo_lora, ref_image_size, low_vram,
    # ⭐ New quality settings
    vae_mode, use_tiled_decode, post_process, fast_mode, steps_full_val, turbo_variant, text_encoder_mode
):
    prompts = split_prompts(prompt_main)
    if not prompts: yield None, None, "⚠️ Lỗi: Không có prompt!"; return
    ensure_server(low_vram, fast_mode)
    os.makedirs(INPUT_DIR, exist_ok=True)

    def _copy(p):
        if not p: return None
        n = f"img_{int(time.time()*1000)}.png"
        shutil.copy(p, os.path.join(INPUT_DIR, n))
        return n

    c_p1, c_p2, c_p3, c_p4 = _copy(pic1_path), _copy(pic2_path), _copy(pic3_path), _copy(pic4_path)
    w, h = parse_resolution(aspect_ratio)

    if len(prompts) == 1:
        num_segments = max(1, int(num_segments))
        scene_prompts = [prompts[0]] * num_segments
    else:
        scene_prompts = prompts

    total = len(scene_prompts)
    total_s = total * float(duration_s)

    # Xác định steps thực tế
    actual_steps_full = int(steps_full_val) if steps_full_val else 20
    actual_steps_turbo = 8 if "8-step" in turbo_variant else 4
    mode = f"Turbo {turbo_variant}" if use_turbo_lora else f"Full {actual_steps_full}-step"
    base_seed = get_seed(seed_val)
    vae_label = "int8_convrot ⚡" if vae_mode == "int8" else "fp16"

    yield None, None, (
        f"✅ Server sẵn sàng. Render {total} cảnh (~{total_s:.0f}s)...\n"
        f"🚀 {op_mode} · {mode} · VAE: {vae_label} · CLIP: {text_encoder_mode} · Seed: {base_seed}"
        + (" · 🔲 Tiled Decode" if use_tiled_decode else "")
        + (" · 🎨 Post-Process" if post_process else "")
        + (" · ⚡ Fast Mode" if fast_mode else "")
    )

    generated = []
    for i, p in enumerate(scene_prompts):
        label = f"cảnh {i+1}/{total}"
        seed_i = base_seed if fixed_seed else (base_seed + i)
        yield generated, None, f"🔄 Render {label} [{mode}] (Seed: {seed_i})\n📝 {p[:120]}..."

        cur_p1, cur_p2 = c_p1, c_p2
        if op_mode == "Auto-Chain (Nối tiếp dây chuyền)" and i > 0 and generated:
            ext = f"ext_{i}_{int(time.time())}.png"
            extract_last_frame(generated[-1], os.path.join(INPUT_DIR, ext))
            cur_p1 = ext; cur_p2 = None

        wf = build_minimax_workflow(
            prompt=p, width=w, height=h, duration_s=duration_s, fps=fps, seed=seed_i,
            scheduler=scheduler, steps_full=actual_steps_full, steps_turbo=actual_steps_turbo,
            use_turbo_lora=use_turbo_lora,
            op_mode=op_mode, ref_image_size=ref_image_size,
            pic1=cur_p1, pic2=cur_p2, pic3=c_p3, pic4=c_p4,
            vae_mode=vae_mode, use_tiled_decode=use_tiled_decode,
            turbo_variant=turbo_variant,
            text_encoder_mode=text_encoder_mode,
        )

        timeout = max(900, int(duration_s) * 150) if use_turbo_lora else max(2700, int(duration_s) * 400)
        try:
            for is_done, p_id, prog_msg in submit_and_wait_gen(wf, label, timeout):
                if not is_done: yield generated, None, f"🔄 Render {label} (Seed: {seed_i})\n⏳ {prog_msg}\n📝 {p[:120]}..."
                else: break
        except RuntimeError as e:
            yield generated, None, f"❌ {e}"; return

        mp4s = glob.glob(os.path.join(OUTPUT_DIR, "**/*.mp4"), recursive=True)
        if not mp4s: yield generated, None, f"⚠️ Lỗi: Không tìm thấy file mp4 cho {label}!"; return
        latest = max(mp4s, key=os.path.getmtime)

        # ⭐ Post-processing: sharpen + denoise nhẹ
        if post_process:
            yield generated, None, f"🎨 Post-processing {label}..."
            pp_path = latest.replace(".mp4", "_pp.mp4")
            latest = post_process_video_ffmpeg(latest, pp_path)

        generated.append(latest)
        yield generated, None, f"🔔 [DING] ✅ Xong {label}!"

    final = concat_videos(generated, f"final_{int(time.time())}") if len(generated) > 1 else generated[0]

    # ⭐ Post-process final video nếu bật và có nhiều cảnh
    if post_process and len(generated) > 1:
        yield generated, None, "🎨 Post-processing video cuối cùng..."
        final_pp = final.replace(".mp4", "_pp.mp4")
        final = post_process_video_ffmpeg(final, final_pp)

    yield generated, final, f"🔔 [DING] 🎉 Hoàn tất! ({total_s:.0f}s, {total} cảnh)"

# ==========================================================================
# GRADIO UI — UPGRADED
# ==========================================================================
ratio_choices = [
    "16:9 (864x480) ⭐ Khuyên dùng (nhanh, nhẹ VRAM)",
    "9:16 (480x864) ⭐ TikTok/Reels",
    "16:9 (1344x768) HD ⭐ Chất lượng cao nhất",
    "9:16 (768x1344) HD dọc — Chậm",
    "1:1  (1056x1056) Vuông",
]

custom_css = """
.gradio-container { max-width: 1560px; margin: 0 auto; }
#mm-header { background: linear-gradient(135deg, #0f4c81 0%, #1a73e8 100%);
             border-radius:16px; padding:20px 26px; margin-bottom:14px; }
#mm-header h1, #mm-header p, #mm-header h3, #mm-header div { color:#fff !important; margin:0 !important; }
.info-box { background:rgba(26,115,232,.08); border-left:3px solid #1a73e8;
            padding:10px 14px; border-radius:8px; font-size:.87rem; margin-bottom:8px; }
.quality-box { background:rgba(76,175,80,.08); border-left:3px solid #4caf50;
            padding:10px 14px; border-radius:8px; font-size:.87rem; margin-bottom:8px; }
.scene-counter { display:inline-block; background:rgba(26,115,232,.12); padding:6px 14px;
                 border-radius:999px; font-weight:600 !important; font-size:.85rem !important; }
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

with gr.Blocks(title="MiniMax H3 Studio — Upgraded", fill_width=True) as demo:
    with gr.Column(elem_id="mm-header"):
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown(
                    "### 🎬 MiniMax H3 — MSR & I2V Auto-Chaining (UPGRADED)\n"
                    "Video VAE int8 + Tiled Decode + Post-Processing + Fast Mode"
                )
            with gr.Column(scale=1, min_width=160):
                restart_btn = gr.Button("🔄 Restart Server", size="sm")
                free_btn = gr.Button("🧹 Giải Phóng VRAM", size="sm")
                log_btn = gr.Button("📋 Xem Log", size="sm")
                restart_out = gr.Markdown("🟢 Sẵn sàng")
        restart_btn.click(fn=force_restart_server, outputs=[restart_out])
        free_btn.click(fn=free_comfyui_memory, outputs=[restart_out])

    with gr.Row():
        with gr.Column(scale=5):
            with gr.Group():
                op_mode = gr.Radio(["MSR (Tham chiếu đa bối cảnh)", "I2V (Nội suy ảnh A -> B)", "Auto-Chain (Nối tiếp dây chuyền)"], label="🎯 Chế độ hoạt động", value="Auto-Chain (Nối tiếp dây chuyền)")
                gr.Markdown(
                    "<div class='info-box'>"
                    "<b>MSR:</b> Dùng <code>&lt;Picture 1&gt;</code> trong prompt. <b>I2V:</b> Pic 1 -> Pic 2. <b>Auto-Chain:</b> Trích xuất khung hình nối tiếp."
                    "</div>"
                )
                with gr.Row():
                    mm_pic1 = gr.Image(label="🎭 Pic 1 (bắt buộc / First Frame)", type="filepath")
                    mm_pic2 = gr.Image(label="🎭 Pic 2 (Last Frame / MSR)", type="filepath")
                with gr.Row():
                    mm_pic3 = gr.Image(label="🎭 Pic 3 (MSR)", type="filepath")
                    mm_pic4 = gr.Image(label="🎭 Pic 4 (MSR)", type="filepath")

            with gr.Group():
                gr.Markdown("### 📝 Prompt")
                scene_display = gr.Markdown("🔹 **Số phân cảnh:** 0", elem_classes="scene-counter")
                mm_prompt = gr.Textbox(
                    label="Prompt (mỗi cảnh cách 1 dòng trống)", lines=8,
                    placeholder=(
                        "<Picture 1> stands on a rooftop at night, cape billowing in wind. "
                        "He says 'Get ready!' with dramatic echo. City neon below.\n\n"
                        "Wide shot — <Picture 1> and <Picture 2> leap off the edge, "
                        "massive explosion behind them, cinematic BOOM sound."
                    ))

            # ⭐ PHẦN MỚI: Cài đặt Chất lượng Video VAE
            with gr.Accordion("🎨 Cài đặt Chất lượng Video (MỚI)", open=True):
                gr.Markdown(
                    "<div class='quality-box'>"
                    "⭐ <b>Các tùy chọn mới giúp cải thiện chất lượng video đầu ra:</b><br>"
                    "• <b>Video VAE int8:</b> Nhanh 1.4-2.7x, chất lượng tương đương fp16<br>"
                    "• <b>Tiled Decode:</b> Giảm VRAM, cho phép render độ phân giải cao hơn<br>"
                    "• <b>Post-Processing:</b> Sharpen + Denoise nhẹ sau render<br>"
                    "• <b>Fast Mode:</b> Bật --fast flag, tăng tốc VAE encoder ~2.2x"
                    "</div>"
                )
                with gr.Row():
                    vae_mode = gr.Radio(
                        label="🧠 Video VAE Precision",
                        choices=["int8", "fp16"],
                        value="int8",
                        info="int8_convrot: ⚡ Nhanh 1.4-2.7x, chất lượng không khác biệt so với fp16"
                    )
                    fast_mode_cb = gr.Checkbox(
                        label="⚡ Fast Mode (--fast)",
                        value=True,
                        info="Bật fp16_accumulation cho convolutions, tăng tốc ~20-25%"
                    )
                with gr.Row():
                    tiled_cb = gr.Checkbox(
                        label="🔲 Tiled VAE Decode",
                        value=False,
                        info="Giảm VRAM khi decode. BẬT nếu bị OOM ở HD (1344x768)"
                    )
                    post_process_cb = gr.Checkbox(
                        label="🎨 Post-Processing (Sharpen + Denoise)",
                        value=True,
                        info="Tăng sắc nét + giảm noise nhẹ bằng ffmpeg (unsharp + hqdn3d)"
                    )
                text_enc_mm = gr.Radio(
                    label="📝 Text Encoder (Qwen3-VL 32B)",
                    choices=["int8", "fp4"],
                    value="int8",
                    info="int8 (27GB, ⭐ khuyên dùng, cần ≥40GB) · fp4 (16GB, cho T4/L4)"
                )

            with gr.Accordion("⚙️ Cài đặt nâng cao", open=False):
                gr.Markdown("**📐 Độ phân giải & Thời lượng**")
                ratio_mm = gr.Radio(label="Tỉ lệ", choices=ratio_choices, value=ratio_choices[0])
                with gr.Row():
                    dur_mm = gr.Slider(label="⏱️ Giây/cảnh", minimum=2, maximum=15, step=1, value=5)
                    fps_mm = gr.Number(label="🎞️ FPS", value=24, precision=0, interactive=False)
                with gr.Row():
                    seed_mm = gr.Number(label="🎲 Seed (-1=random)", value=-1, precision=0)
                    seg_mm = gr.Slider(label="🔢 Segments (1 prompt)", minimum=1, maximum=10, step=1, value=1)
                fixed_mm = gr.Checkbox(label="🔗 Cùng Seed mọi cảnh", value=False)

                gr.Markdown("**🧬 Sampler & LoRA**")
                with gr.Row():
                    sched_mm = gr.Radio(label="Scheduler", choices=["beta", "normal", "simple"], value="beta")
                    turbo_mm = gr.Checkbox(
                        label="⚡ Turbo LoRA (tăng tốc)", value=True,
                        info="BẬT: nhanh x5 (4 hoặc 8 steps). TẮT: Full 20+ steps.")
                turbo_variant_mm = gr.Radio(
                    label="🚀 Turbo Variant (lightx2v)",
                    choices=[
                        "4-step v1.0 (gốc, nhanh nhất)",
                        "8-step v1.0 ⭐ (chất lượng tốt nhất)",
                        "4-step v1.2 (audio cải thiện)",
                    ],
                    value="8-step v1.0 ⭐ (chất lượng tốt nhất)",
                    info="8-step: motion mượt, ít artifact. v1.2: audio rõ hơn. 4-step gốc: nhanh nhất."
                )
                with gr.Row():
                    steps_full_mm = gr.Slider(
                        label="🔢 Steps (Full mode, khi TẮT turbo)",
                        minimum=10, maximum=50, step=1, value=20,
                        info="20 = chuẩn. 30-40 = chi tiết hơn nhưng chậm hơn."
                    )
                    ref_mm = gr.Radio(
                        label="ref_image_size", choices=["match", "max"], value="match",
                        info="match = nhanh · max = giữ chi tiết ảnh tốt hơn")

                gr.Markdown("**⚙️ Server**")
                vram_mm = gr.Checkbox(label="🧊 Low VRAM (--cache-none)", value=True)

        with gr.Column(scale=5):
            with gr.Group():
                gallery_mm = gr.Gallery(label="🎥 Các cảnh lẻ", columns=2, height="auto")
                video_mm = gr.Video(label="🎬 Video hoàn chỉnh")
                with gr.Row():
                    btn_mm = gr.Button("🎬 Bắt Đầu Tạo Video", variant="primary", scale=3)
                    clr_mm = gr.Button("🗑️ Clear", scale=1)
                status_mm = gr.Textbox(
                    label="ℹ️ Status", interactive=False, lines=5, elem_classes="status-box")

    mm_prompt.change(fn=count_scenes, inputs=[mm_prompt], outputs=[scene_display])
    btn_mm.click(
        fn=generate_minimax_gradio,
        inputs=[
            op_mode, mm_pic1, mm_pic2, mm_pic3, mm_pic4,
            mm_prompt,
            ratio_mm, dur_mm, fps_mm, seed_mm, seg_mm, fixed_mm,
            sched_mm, turbo_mm, ref_mm, vram_mm,
            vae_mode, tiled_cb, post_process_cb, fast_mode_cb, steps_full_mm, turbo_variant_mm, text_enc_mm,
        ],
        outputs=[gallery_mm, video_mm, status_mm],
    )
    def on_clear():
        free_comfyui_memory()
        return None, None, "🟢 Đã dọn dẹp!", "🔹 **Số phân cảnh:** 0"
    clr_mm.click(fn=on_clear, outputs=[gallery_mm, video_mm, status_mm, scene_display])
    log_btn.click(fn=read_server_log, outputs=[status_mm])

print("🔄 Khởi động ComfyUI server (UPGRADED — Fast Mode)...")
try:
    ensure_server(low_vram=True, fast_mode=True)
    print("🟢 ComfyUI server sẵn sàng!")
except Exception as e:
    print(f"⚠️ {e}")

demo.queue()
demo.launch(
    share=True, inline=False, debug=True,
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo", neutral_hue="slate"),
    css=custom_css, js=notification_js,
)
