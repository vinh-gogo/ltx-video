#@title 📦 Cell 1: Install ComfyUI + Tải Model (MSR & I2V) — UPGRADED
import os

COMFYUI_ROOT = "/content/ComfyUI"

MINIMAX_MODELS = [
    # ---- 1. Shared Models (CLIP & VAE) ----
    # Text Encoder — bf16
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_bf16.safetensors", f"{COMFYUI_ROOT}/models/text_encoders/qwen3vl_32b_minimax_h3_bf16.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", f"{COMFYUI_ROOT}/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),

    # Video VAE — fp16 (fallback, vẫn giữ để tương thích)
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors", f"{COMFYUI_ROOT}/models/vae/minimax_h3_video_vae_fp16.safetensors"),

    # Video VAE — int8_convrot (⭐ KHUYÊN DÙNG: nhanh 1.4-2.7x, chất lượng tương đương fp16)
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/vae/minimax_h3_video_vae_int8_convrot.safetensors"),

    # Audio VAE
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors", f"{COMFYUI_ROOT}/models/vae/minimax_h3_audio_vae_fp32.safetensors"),

    # ---- 2. MSR Models (Multi-Subject Reference) ----
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"),
    # ⭐ MSR 8-step turbo — chất lượng tốt hơn 4-step, vẫn nhanh
    ("https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"),

    # ---- 3. I2V Models (First/Last Frame Interpolation) ----
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", f"{COMFYUI_ROOT}/models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"),
    ("https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"),
    # ⭐ I2V 8-step turbo — motion mượt hơn, ít artifact hơn 4-step
    ("https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"),
    # ⭐ I2V 4-step v1.2 — phiên bản mới nhất, audio cải thiện đáng kể
    ("https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors", f"{COMFYUI_ROOT}/models/loras/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors"),

    # ---- 4. Upscaler Model (Real-ESRGAN x4 — Video Post-Processing) ----
    ("https://huggingface.co/ai-forever/Real-ESRGAN/resolve/main/RealESRGAN_x4.pth", f"{COMFYUI_ROOT}/models/upscale_models/RealESRGAN_x4.pth"),
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

def install_custom_nodes():
    """Cài đặt custom nodes nâng cao cho chất lượng video tốt hơn."""
    cn_dir = os.path.join(COMFYUI_ROOT, "custom_nodes")
    os.makedirs(cn_dir, exist_ok=True)

    nodes_to_install = [
        # SageAttention — tăng tốc attention kernel, giảm VRAM
        ("https://github.com/kijai/ComfyUI-KJNodes.git", "ComfyUI-KJNodes"),
        # Video Helper Suite — quản lý frame sequences tốt hơn
        ("https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git", "ComfyUI-VideoHelperSuite"),
    ]

    for repo_url, folder_name in nodes_to_install:
        target = os.path.join(cn_dir, folder_name)
        if os.path.exists(target):
            print(f"✅ Custom node đã có: {folder_name}")
        else:
            print(f"⬇️ Cài đặt custom node: {folder_name} ...")
            ret = os.system(f'git clone {repo_url} "{target}"')
            if ret == 0:
                req_file = os.path.join(target, "requirements.txt")
                if os.path.exists(req_file):
                    os.system(f"pip install -q -r {req_file}")
                print(f"✅ Xong: {folder_name}")
            else:
                print(f"⚠️ Không cài được: {folder_name}")

print("="*60)
print("  MiniMax H3 — Setup & Download (MSR + I2V) — UPGRADED")
print("="*60)
os.system("apt-get -y install -qq aria2 > /dev/null 2>&1 || true")
setup_comfyui()
os.system("pip install -q uv")
os.system("uv pip install -q --system gradio opencv-python accelerate diffusers einops sentencepiece av spandrel aiohttp")

# Cài SageAttention để tăng tốc (optional, sẽ skip nếu không cài được)
print("\n🔧 Cài đặt SageAttention (tăng tốc attention)...")
os.system("pip install -q sageattention 2>/dev/null || true")

download_models(MINIMAX_MODELS)
install_custom_nodes()
print("\n🎉 HOÀN TẤT CELL 1! (Upgraded — Video VAE int8 + Upscaler + Custom Nodes)")
