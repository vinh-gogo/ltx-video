#@title 📦 Cell 1: Install ComfyUI + Tải Model (MSR & I2V)
import os

COMFYUI_ROOT = "/content/ComfyUI"

MINIMAX_MODELS = [
    # ---- 1. Shared Models (CLIP & VAE) ----
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", f"{COMFYUI_ROOT}/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors", f"{COMFYUI_ROOT}/models/vae/minimax_h3_video_vae_fp16.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors", f"{COMFYUI_ROOT}/models/vae/minimax_h3_audio_vae_fp32.safetensors"),

    # ---- 2. MSR Models (Multi-Subject Reference) ----
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"),

    # ---- 3. I2V Models (First/Last Frame Interpolation) ----
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"),
]

def download_models(models):
    has_aria2 = os.system("which aria2c > /dev/null 2>&1") == 0
    for url, dest in models:
        if os.path.exists(dest) and os.path.getsize(dest) > 1024 * 1024 * 50:
            print(f"✅ Đã có: {os.path.basename(dest)}")
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        print(f"⬇️ Đang tải: {os.path.basename(dest)} ...")
        cmd = f'aria2c -c -x 16 -s 16 -k 1M -d "{os.path.dirname(dest)}" -o "{os.path.basename(dest)}" "{url}"' if has_aria2 else f'wget -q --show-progress -c "{url}" -O "{dest}"'
        if os.system(cmd) == 0:
            print(f"✅ Xong: {os.path.basename(dest)}")

def setup_comfyui():
    if not os.path.exists(f"{COMFYUI_ROOT}/main.py"):
        os.system(f"git clone https://github.com/comfyanonymous/ComfyUI {COMFYUI_ROOT}")
    if os.path.exists(f"{COMFYUI_ROOT}/requirements.txt"):
        os.system(f"pip install -q -r {COMFYUI_ROOT}/requirements.txt")

print("="*60)
print("  MiniMax H3 — Setup & Download (MSR + I2V)")
print("="*60)
os.system("apt-get -y install -qq aria2 > /dev/null 2>&1 || true")
setup_comfyui()
os.system("pip install -q uv")
os.system("uv pip install -q --system gradio opencv-python accelerate diffusers einops sentencepiece av spandrel aiohttp")
download_models(MINIMAX_MODELS)
print("\n🎉 HOÀN TẤT CELL 1!")

