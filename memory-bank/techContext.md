# Tech Context — AI Video Studio: LTX-2.5 & MiniMax H3

> Công nghệ sử dụng, cấu hình môi trường, thư viện phụ thuộc và ràng buộc kỹ thuật.

## 1. Công nghệ & Nền tảng cốt lõi
- **Ngôn ngữ:** Python 3.10+
- **Framework & Giao diện:**
  - `gradio` (tương thích Gradio 6.0+)
  - `opencv-python` (OpenCV xử lý frame, trích xuất ảnh đầu/cuối)
  - `torch` & `torchvision` (PyTorch inference)
- **Engine Backend:**
  - [ComfyUI](https://github.com/comfyanonymous/ComfyUI) chạy ở port `8188` (giao tiếp qua HTTP REST API và WebSocket)
- **Mô hình AI Video:**
  - **Lightricks LTX-2.5 (22B):**
    - UNet: `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`
    - Text Encoder: `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`
    - VAE: `ltx-2.5-video-vae-bf16.safetensors` & `ltx-2.5-audio-vae-bf16.safetensors`
    - Upscaler: `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors`
  - **MiniMax H3:**
    - Diffusion Transformer: MiniMax H3
    - Text Encoder: Qwen3-VL 32B (chuẩn hóa `int8` ~27GB và `fp4 AWQ` ~16GB)
    - Video VAE: `int8_convrot`
    - LoRA tăng tốc: Turbo LoRA 8-step v1.0 & 4-step v1.2 (từ `lightx2v`)
  - **RIFE Post-Processor:**
    - Mô hình: Practical-RIFE v4.26 (`flownet.pkl`)
- **Công cụ Media:**
  - `ffmpeg` (ghép video, trích xuất audio, nối storyboard, mã hóa H.264/AAC)

## 2. Môi trường triển khai (Deployment Target)
- **Chính:** Google Colab GPU (NVIDIA T4, V100, A100, L4).
- **Đường dẫn thư mục chuẩn trên Colab:**
  - `/content/ComfyUI/`
  - `/content/ComfyUI/input/`
  - `/content/ComfyUI/output/`
  - `/content/ComfyUI/models/` (checkpoints, loras, vae, clip)
  - `/content/RIFE/` & `/content/rife_output/`
- **Môi trường cục bộ:** Có thể chạy trên máy tính Windows/Linux nếu có GPU NVIDIA $\ge$ 16GB VRAM (khuyến nghị $\ge$ 24GB).

## 3. Ràng buộc kỹ thuật & Xử lý ngoại lệ
- **VRAM Allocation:** Sử dụng `PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"` để tránh phân mảnh bộ nhớ CUDA.
- **Port Conflict:** Các script tự động kiểm tra port `8188` qua socket và `urllib`, tự động giải phóng qua `fuser -k 8188/tcp` nếu server cũ bị treo.
- **Tương thích Gradio 6.0+:** Không dùng các thuộc tính deprecated (như `scale` trực tiếp trên một số container không hỗ trợ), dùng layout blocks linh hoạt.
- **Bảo toàn âm thanh khi làm mượt:** `rife_postprocess.py` trích xuất audio stream từ video gốc và remux vào video sau nội suy bằng lệnh FFmpeg codec copy (`-c:a copy`), đảm bảo không bị lệch pha tiếng.
